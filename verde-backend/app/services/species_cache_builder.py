"""
Verde Species Cache Builder

이 모듈은 IUCN API에서 국가별 카테고리별 종 개수를 미리 계산하여
JSON 파일에 캐시합니다.

핵심 특징:
- IUCN API에서 지원하는 모든 국가를 동적으로 가져옴 (하드코딩 없음)
- 서버 시작 시 또는 수동으로 실행 가능

사용법:
    python -m app.services.species_cache_builder
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

import cloudscraper
from functools import partial

# 설정
CACHE_FILE_PATH = Path(__file__).parent.parent / "data" / "species_counts.json"
IUCN_BASE_URL = "https://api.iucnredlist.org/api/v4"

# 카테고리 분류 기준
CATEGORY_MAPPING = {
    # 동물: 포유류, 조류, 파충류, 양서류
    "동물": ['MAMMALIA', 'AVES', 'REPTILIA', 'AMPHIBIA'],
    # 해양생물: 어류, 연체동물, 갑각류, 산호 등
    "해양생물": ['ACTINOPTERYGII', 'CHONDRICHTHYES', 'CEPHALOPODA', 'MALACOSTRACA',
                 'ANTHOZOA', 'BIVALVIA', 'GASTROPODA', 'HOLOTHUROIDEA', 'ECHINOIDEA'],
    # 곤충
    "곤충": ['INSECTA', 'ARACHNIDA'],
    # 식물: 왕국이 PLANTAE인 경우
    "식물": ['LILIOPSIDA', 'MAGNOLIOPSIDA', 'PINOPSIDA', 'POLYPODIOPSIDA',
             'CYCADOPSIDA', 'GINKGOOPSIDA', 'GNETOPSIDA', 'BRYOPSIDA']
}


class SpeciesCacheBuilder:
    def __init__(self, token: str):
        self.token = token
        self.base_url = IUCN_BASE_URL
        self.scraper = cloudscraper.create_scraper()
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }
        # taxon 정보 캐시 (sis_taxon_id -> class_name/kingdom_name)
        self.taxon_cache: Dict[int, Dict[str, str]] = {}
        # 세마포어로 동시 요청 제한
        self.semaphore = asyncio.Semaphore(20)

    async def _make_request(self, url: str, params: dict = None) -> Any:
        """HTTP 요청 (동기 cloudscraper를 비동기로 래핑)"""
        async with self.semaphore:
            try:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    partial(self.scraper.get, url, headers=self.headers, params=params, timeout=15)
                )
                return response
            except Exception:
                return None

    async def fetch_all_countries(self) -> List[str]:
        """IUCN API에서 지원하는 모든 국가 코드를 동적으로 가져옴"""
        print("🌍 IUCN API에서 국가 목록 가져오는 중...", flush=True)

        url = f"{self.base_url}/countries"
        response = await self._make_request(url)

        if not response or response.status_code != 200:
            print("❌ 국가 목록을 가져올 수 없습니다.", flush=True)
            return []

        data = response.json()
        countries = data.get('countries', data)

        # ISO 코드 추출
        country_codes = []
        for country in countries:
            if isinstance(country, dict):
                code = country.get('code', '')
                if code and len(code) == 2:  # ISO Alpha-2 코드만
                    country_codes.append(code)

        print(f"✅ {len(country_codes)}개 국가 발견", flush=True)
        return country_codes

    async def _fetch_country_assessments(self, country_code: str, max_pages: int = 10) -> list:
        """국가별 종 목록 조회 (최대 1000종 - 종 목록 API와 동일)"""
        all_assessments = []

        for page in range(1, max_pages + 1):
            url = f"{self.base_url}/countries/{country_code}"
            params = {"page": page, "latest": "true"}

            response = await self._make_request(url, params)
            if not response or response.status_code != 200:
                break

            data = response.json()
            assessments = data.get('assessments', [])
            if not assessments:
                break

            all_assessments.extend(assessments)

            if len(assessments) < 100:  # 마지막 페이지
                break

        return all_assessments

    async def _fetch_taxon_info(self, sis_taxon_id: int) -> Optional[Dict[str, str]]:
        """sis_taxon_id로 taxon 정보 조회 (class_name, kingdom_name, order_name, family_name)"""
        # 캐시 확인
        if sis_taxon_id in self.taxon_cache:
            return self.taxon_cache[sis_taxon_id]

        try:
            url = f"{self.base_url}/taxa/sis/{sis_taxon_id}"
            response = await self._make_request(url)

            if response and response.status_code == 200:
                data = response.json()
                taxon = data.get('taxon', data)
                result = {
                    'class_name': (taxon.get('class_name') or '').upper(),
                    'kingdom_name': (taxon.get('kingdom_name') or '').upper(),
                    'order_name': (taxon.get('order_name') or '').upper(),
                    'family_name': (taxon.get('family_name') or '').upper()
                }
                self.taxon_cache[sis_taxon_id] = result
                return result

            return None
        except Exception:
            return None

    # 해양포유류 목(Order) - 고래, 돌고래, 물개 등
    MARINE_MAMMAL_ORDERS = ['CETACEA', 'SIRENIA']  # 고래목, 해우목
    # CARNIVORA 중 해양 과(Family)
    MARINE_CARNIVORA_FAMILIES = ['OTARIIDAE', 'PHOCIDAE', 'ODOBENIDAE']  # 물개, 바다표범, 바다코끼리

    def _determine_category(self, class_name: str, kingdom_name: str, order_name: str = '', family_name: str = '') -> Optional[str]:
        """
        class_name, kingdom_name, order_name으로 카테고리 결정

        종 목록 API(iucn_service.py)와 동일한 로직 적용:
        - taxon 정보 없으면 None 반환 (기본값 없음)
        - 명확한 분류가 가능한 경우만 카테고리 반환
        - 해양포유류(고래, 해우, 물개)는 해양생물로 분류
        """
        # 분류 정보가 없으면 None
        if not class_name and not kingdom_name:
            return None

        # 식물: kingdom이 PLANTAE
        if kingdom_name == 'PLANTAE':
            return "식물"

        # 해양포유류 체크 (고래목, 해우목, 기각류)
        if class_name == 'MAMMALIA':
            # 고래목(CETACEA)과 해우목(SIRENIA)은 해양생물
            if order_name in self.MARINE_MAMMAL_ORDERS:
                return "해양생물"
            # 식육목(CARNIVORA) 중 해양 과는 해양생물 (물개, 바다표범 등)
            if order_name == 'CARNIVORA' and family_name in self.MARINE_CARNIVORA_FAMILIES:
                return "해양생물"

        # 카테고리별 class_name 매칭
        for category, classes in CATEGORY_MAPPING.items():
            if class_name in classes:
                return category

        # ANIMALIA지만 알 수 없는 class는 제외 (기본값 없음)
        # 이렇게 해야 종 목록 API와 동일한 결과
        return None

    async def _count_species_by_category(self, country_code: str) -> Dict[str, int]:
        """
        국가의 카테고리별 종 개수 계산

        종 목록 API(iucn_service.py)와 동일한 로직 적용:
        - 10페이지(1000종) 조회
        - 알파벳 범위별 350개 샘플링
        - taxon 정보 없으면 제외 (비율 추정 없이 실제 카운트)
        """
        counts = {"동물": 0, "식물": 0, "곤충": 0, "해양생물": 0}

        # 종 목록 조회 (10페이지, 최대 1000종)
        assessments = await self._fetch_country_assessments(country_code)
        if not assessments:
            return counts

        total = len(assessments)

        # === 종 목록 API와 동일한 알파벳 범위별 샘플링 ===
        if total <= 200:
            sample_assessments = assessments
        else:
            sample_assessments = []

            # 알파벳 범위별 균등 샘플링 (포유류는 L~Z에 집중)
            alphabet_ranges = [
                (0, 0.12),    # A-B: 0-12%
                (0.12, 0.25), # C-E: 12-25%
                (0.25, 0.38), # F-I: 25-38%
                (0.38, 0.50), # J-M: 38-50% (많은 포유류)
                (0.50, 0.62), # N-P: 50-62% (많은 포유류)
                (0.62, 0.75), # Q-S: 62-75%
                (0.75, 0.88), # T-V: 75-88%
                (0.88, 1.0),  # W-Z: 88-100%
            ]

            samples_per_range = 40  # 각 범위에서 40개씩 = 320개

            for start_pct, end_pct in alphabet_ranges:
                start_idx = int(total * start_pct)
                end_idx = int(total * end_pct)
                range_size = end_idx - start_idx

                if range_size > 0:
                    step = max(1, range_size // samples_per_range)
                    for i in range(0, min(range_size, samples_per_range * step), step):
                        if start_idx + i < len(assessments):
                            sample_assessments.append(assessments[start_idx + i])

            # 중복 제거
            seen = set()
            unique_samples = []
            for a in sample_assessments:
                key = a.get('sis_taxon_id')
                if key not in seen:
                    seen.add(key)
                    unique_samples.append(a)
            sample_assessments = unique_samples[:350]  # 최대 350개

        # 병렬로 taxon 정보 조회 및 카테고리 분류
        async def classify_species(assessment: dict) -> Optional[str]:
            sis_taxon_id = assessment.get('sis_taxon_id')
            if not sis_taxon_id:
                return None  # taxon ID 없으면 제외

            taxon_info = await self._fetch_taxon_info(sis_taxon_id)
            if not taxon_info:
                return None  # taxon 정보 없으면 제외

            return self._determine_category(
                taxon_info.get('class_name', ''),
                taxon_info.get('kingdom_name', ''),
                taxon_info.get('order_name', ''),
                taxon_info.get('family_name', '')
            )

        tasks = [classify_species(a) for a in sample_assessments]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 카테고리별 카운트 (None은 제외)
        for result in results:
            if isinstance(result, str) and result in counts:
                counts[result] += 1

        # 비율 추정 없이 실제 카운트 반환
        # (종 목록 API도 샘플링된 결과만 반환하므로 일관성 유지)
        return counts

    async def build_cache(self, resume: bool = True) -> Dict[str, Any]:
        """전체 캐시 빌드 (동적 국가 목록 사용, 이어하기 지원)"""
        print("=" * 60, flush=True)
        print("🏗️  Verde Species Cache Builder 시작", flush=True)
        print("=" * 60, flush=True)

        # IUCN API에서 동적으로 국가 목록 가져오기
        all_countries = await self.fetch_all_countries()

        if not all_countries:
            print("❌ 국가 목록을 가져올 수 없어 중단합니다.", flush=True)
            return {"generated_at": datetime.now().isoformat(), "countries": {}}

        print(f"📍 대상 국가: {len(all_countries)}개", flush=True)
        print(f"📁 캐시 파일: {CACHE_FILE_PATH}", flush=True)

        # 기존 캐시 로드 (이어하기 모드)
        existing_countries = {}
        if resume and CACHE_FILE_PATH.exists():
            try:
                with open(CACHE_FILE_PATH, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                existing_countries = existing_data.get("countries", {})
                print(f"📂 기존 캐시 발견: {len(existing_countries)}개 국가", flush=True)
            except Exception:
                pass

        print(flush=True)

        cache_data = {
            "generated_at": datetime.now().isoformat(),
            "total_countries": len(all_countries),
            "countries": existing_countries.copy()
        }

        # 각 국가별로 처리
        processed = 0
        skipped_existing = 0
        for i, country_code in enumerate(all_countries, 1):
            # 이미 처리된 국가는 스킵
            if country_code in existing_countries:
                skipped_existing += 1
                continue

            print(f"[{i}/{len(all_countries)}] {country_code}...", end=" ", flush=True)

            try:
                counts = await self._count_species_by_category(country_code)
                total_species = sum(counts.values())

                # 종이 하나라도 있는 경우만 저장
                if total_species > 0:
                    cache_data["countries"][country_code] = counts
                    print(f"OK ({total_species}종)", flush=True)
                else:
                    print(f"SKIP (0종)", flush=True)

                processed += 1

                # 10개 국가마다 중간 저장
                if processed % 10 == 0:
                    self.save_cache(cache_data, silent=True)
                    print(f"   💾 중간 저장 ({len(cache_data['countries'])}개 국가)", flush=True)

            except Exception as e:
                print(f"FAIL ({e})", flush=True)

            # API 부하 방지를 위한 딜레이
            await asyncio.sleep(0.2)

        print(flush=True)
        print("=" * 60, flush=True)
        print("✅ 캐시 빌드 완료!", flush=True)
        print(f"📊 처리된 국가: {len(cache_data['countries'])}개 (총 {len(all_countries)}개 중)", flush=True)
        if skipped_existing > 0:
            print(f"⏭️  스킵한 국가 (기존 캐시): {skipped_existing}개", flush=True)
        print("=" * 60, flush=True)

        return cache_data

    def save_cache(self, cache_data: Dict[str, Any], silent: bool = False):
        """캐시를 JSON 파일로 저장"""
        # 디렉토리 생성
        CACHE_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

        with open(CACHE_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)

        if not silent:
            print(f"💾 캐시 저장됨: {CACHE_FILE_PATH}", flush=True)


# 전역 캐시 변수 (서버에서 사용)
SPECIES_COUNT_CACHE: Dict[str, Dict[str, int]] = {}


def load_species_cache() -> Dict[str, Dict[str, int]]:
    """
    JSON 파일에서 캐시 로드

    Returns:
        { "동물": {"KR": 12, "US": 50, ...}, "식물": {...}, ... }
    """
    global SPECIES_COUNT_CACHE

    if not CACHE_FILE_PATH.exists():
        print(f"⚠️ 캐시 파일이 없습니다: {CACHE_FILE_PATH}")
        return {}

    try:
        with open(CACHE_FILE_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 데이터 변환: countries 구조를 카테고리별 구조로 변환
        # 원본: {"countries": {"KR": {"동물": 12, ...}, ...}}
        # 변환: {"동물": {"KR": 12, ...}, "식물": {...}, ...}
        categories = ["동물", "식물", "곤충", "해양생물"]
        result = {cat: {} for cat in categories}

        for country_code, counts in data.get("countries", {}).items():
            for category in categories:
                # 0인 값도 포함 (프론트엔드에서 회색으로 표시하기 위해)
                count_value = counts.get(category, 0)
                result[category][country_code] = count_value

        SPECIES_COUNT_CACHE = result

        print(f"✅ 캐시 로드 완료: {CACHE_FILE_PATH}")
        print(f"   생성 시간: {data.get('generated_at', 'Unknown')}")
        print(f"   총 국가 수: {data.get('total_countries', len(data.get('countries', {})))}")
        for cat in categories:
            count = len(result[cat])
            print(f"   {cat}: {count}개 국가")

        return result

    except Exception as e:
        print(f"❌ 캐시 로드 실패: {e}")
        return {}


def get_cached_counts(category: str) -> Dict[str, int]:
    """특정 카테고리의 국가별 종 개수 반환"""
    return SPECIES_COUNT_CACHE.get(category, {})


async def main():
    """메인 실행 함수 (CLI용)"""
    # 환경변수에서 API 키 로드
    from app.core.config import settings
    token = settings.IUCN_API_KEY

    if not token:
        print("❌ IUCN_API_KEY가 설정되지 않았습니다.")
        print("   .env 파일에 IUCN_API_KEY를 설정하세요.")
        return

    builder = SpeciesCacheBuilder(token)
    cache_data = await builder.build_cache()
    builder.save_cache(cache_data)

    # 로드 테스트
    print("\n📖 캐시 로드 테스트:")
    load_species_cache()


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
전 세계 생물 데이터 수집 스크립트

사용법:
    # 전체 수집
    python -m app.scripts.collect_global_data --all

    # 특정 국가만
    python -m app.scripts.collect_global_data --countries KR,US,JP

    # 특정 카테고리만
    python -m app.scripts.collect_global_data --categories 식물,동물

    # 진행 상황 확인
    python -m app.scripts.collect_global_data --status

    # 중단된 작업 재개
    python -m app.scripts.collect_global_data --resume
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
import time

# 프로젝트 루트를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.species import Species, CategoryEnum
from app.services.gbif_service import GBIFService

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('data_collection.log')
    ]
)
logger = logging.getLogger(__name__)


# ========== 상수 정의 ==========

# 카테고리별 목표 비율
CATEGORY_RATIOS = {
    "식물": 0.40,
    "동물": 0.30,
    "곤충": 0.20,
    "해양생물": 0.10
}

# GBIF 검색 키워드 (카테고리별)
CATEGORY_SEARCH_TERMS = {
    "식물": ["Plantae", "flowering plant", "tree", "fern", "moss"],
    "동물": ["Mammalia", "Aves", "Reptilia", "Amphibia", "vertebrate"],
    "곤충": ["Insecta", "butterfly", "beetle", "ant", "bee"],
    "해양생물": ["marine fish", "coral", "mollusk", "crustacean", "seaweed"]
}

# GBIF taxon_key 매핑 (카테고리 -> GBIF 분류 키)
CATEGORY_TO_TAXON_KEY = {
    "식물": 6,       # Plantae kingdom key
    "동물": 1,       # Animalia kingdom key
    "곤충": 212,     # Insecta class key
    "해양생물": None  # 해양생물은 taxon_key 없이 검색어로만 필터링
}

# 전 세계 195개국 목록 (ISO 3166-1 alpha-2)
COUNTRIES = {
    # 아시아
    "KR": {"name": "대한민국", "region": "아시아"},
    "JP": {"name": "일본", "region": "아시아"},
    "CN": {"name": "중국", "region": "아시아"},
    "TW": {"name": "대만", "region": "아시아"},
    "HK": {"name": "홍콩", "region": "아시아"},
    "MO": {"name": "마카오", "region": "아시아"},
    "MN": {"name": "몽골", "region": "아시아"},
    "VN": {"name": "베트남", "region": "아시아"},
    "TH": {"name": "태국", "region": "아시아"},
    "MY": {"name": "말레이시아", "region": "아시아"},
    "SG": {"name": "싱가포르", "region": "아시아"},
    "ID": {"name": "인도네시아", "region": "아시아"},
    "PH": {"name": "필리핀", "region": "아시아"},
    "MM": {"name": "미얀마", "region": "아시아"},
    "KH": {"name": "캄보디아", "region": "아시아"},
    "LA": {"name": "라오스", "region": "아시아"},
    "BN": {"name": "브루나이", "region": "아시아"},
    "TL": {"name": "동티모르", "region": "아시아"},
    "IN": {"name": "인도", "region": "아시아"},
    "PK": {"name": "파키스탄", "region": "아시아"},
    "BD": {"name": "방글라데시", "region": "아시아"},
    "LK": {"name": "스리랑카", "region": "아시아"},
    "NP": {"name": "네팔", "region": "아시아"},
    "BT": {"name": "부탄", "region": "아시아"},
    "MV": {"name": "몰디브", "region": "아시아"},
    "AF": {"name": "아프가니스탄", "region": "아시아"},

    # 중동
    "IR": {"name": "이란", "region": "중동"},
    "IQ": {"name": "이라크", "region": "중동"},
    "SA": {"name": "사우디아라비아", "region": "중동"},
    "AE": {"name": "아랍에미리트", "region": "중동"},
    "QA": {"name": "카타르", "region": "중동"},
    "KW": {"name": "쿠웨이트", "region": "중동"},
    "BH": {"name": "바레인", "region": "중동"},
    "OM": {"name": "오만", "region": "중동"},
    "YE": {"name": "예멘", "region": "중동"},
    "JO": {"name": "요르단", "region": "중동"},
    "SY": {"name": "시리아", "region": "중동"},
    "LB": {"name": "레바논", "region": "중동"},
    "IL": {"name": "이스라엘", "region": "중동"},
    "PS": {"name": "팔레스타인", "region": "중동"},
    "TR": {"name": "터키", "region": "중동"},
    "CY": {"name": "키프로스", "region": "중동"},

    # 유럽
    "GB": {"name": "영국", "region": "유럽"},
    "FR": {"name": "프랑스", "region": "유럽"},
    "DE": {"name": "독일", "region": "유럽"},
    "IT": {"name": "이탈리아", "region": "유럽"},
    "ES": {"name": "스페인", "region": "유럽"},
    "PT": {"name": "포르투갈", "region": "유럽"},
    "NL": {"name": "네덜란드", "region": "유럽"},
    "BE": {"name": "벨기에", "region": "유럽"},
    "LU": {"name": "룩셈부르크", "region": "유럽"},
    "CH": {"name": "스위스", "region": "유럽"},
    "AT": {"name": "오스트리아", "region": "유럽"},
    "IE": {"name": "아일랜드", "region": "유럽"},
    "DK": {"name": "덴마크", "region": "유럽"},
    "NO": {"name": "노르웨이", "region": "유럽"},
    "SE": {"name": "스웨덴", "region": "유럽"},
    "FI": {"name": "핀란드", "region": "유럽"},
    "IS": {"name": "아이슬란드", "region": "유럽"},
    "PL": {"name": "폴란드", "region": "유럽"},
    "CZ": {"name": "체코", "region": "유럽"},
    "SK": {"name": "슬로바키아", "region": "유럽"},
    "HU": {"name": "헝가리", "region": "유럽"},
    "RO": {"name": "루마니아", "region": "유럽"},
    "BG": {"name": "불가리아", "region": "유럽"},
    "GR": {"name": "그리스", "region": "유럽"},
    "HR": {"name": "크로아티아", "region": "유럽"},
    "SI": {"name": "슬로베니아", "region": "유럽"},
    "RS": {"name": "세르비아", "region": "유럽"},
    "BA": {"name": "보스니아 헤르체고비나", "region": "유럽"},
    "ME": {"name": "몬테네그로", "region": "유럽"},
    "MK": {"name": "북마케도니아", "region": "유럽"},
    "AL": {"name": "알바니아", "region": "유럽"},
    "XK": {"name": "코소보", "region": "유럽"},
    "EE": {"name": "에스토니아", "region": "유럽"},
    "LV": {"name": "라트비아", "region": "유럽"},
    "LT": {"name": "리투아니아", "region": "유럽"},
    "BY": {"name": "벨라루스", "region": "유럽"},
    "UA": {"name": "우크라이나", "region": "유럽"},
    "MD": {"name": "몰도바", "region": "유럽"},
    "RU": {"name": "러시아", "region": "유럽"},
    "MT": {"name": "몰타", "region": "유럽"},
    "MC": {"name": "모나코", "region": "유럽"},
    "AD": {"name": "안도라", "region": "유럽"},
    "SM": {"name": "산마리노", "region": "유럽"},
    "VA": {"name": "바티칸", "region": "유럽"},
    "LI": {"name": "리히텐슈타인", "region": "유럽"},

    # 북미
    "US": {"name": "미국", "region": "북미"},
    "CA": {"name": "캐나다", "region": "북미"},
    "MX": {"name": "멕시코", "region": "북미"},
    "GT": {"name": "과테말라", "region": "북미"},
    "BZ": {"name": "벨리즈", "region": "북미"},
    "HN": {"name": "온두라스", "region": "북미"},
    "SV": {"name": "엘살바도르", "region": "북미"},
    "NI": {"name": "니카라과", "region": "북미"},
    "CR": {"name": "코스타리카", "region": "북미"},
    "PA": {"name": "파나마", "region": "북미"},

    # 카리브해
    "CU": {"name": "쿠바", "region": "카리브해"},
    "JM": {"name": "자메이카", "region": "카리브해"},
    "HT": {"name": "아이티", "region": "카리브해"},
    "DO": {"name": "도미니카 공화국", "region": "카리브해"},
    "PR": {"name": "푸에르토리코", "region": "카리브해"},
    "BS": {"name": "바하마", "region": "카리브해"},
    "TT": {"name": "트리니다드 토바고", "region": "카리브해"},
    "BB": {"name": "바베이도스", "region": "카리브해"},
    "LC": {"name": "세인트루시아", "region": "카리브해"},
    "GD": {"name": "그레나다", "region": "카리브해"},
    "VC": {"name": "세인트빈센트 그레나딘", "region": "카리브해"},
    "AG": {"name": "앤티가 바부다", "region": "카리브해"},
    "DM": {"name": "도미니카", "region": "카리브해"},
    "KN": {"name": "세인트키츠 네비스", "region": "카리브해"},

    # 남미
    "BR": {"name": "브라질", "region": "남미"},
    "AR": {"name": "아르헨티나", "region": "남미"},
    "CL": {"name": "칠레", "region": "남미"},
    "CO": {"name": "콜롬비아", "region": "남미"},
    "PE": {"name": "페루", "region": "남미"},
    "VE": {"name": "베네수엘라", "region": "남미"},
    "EC": {"name": "에콰도르", "region": "남미"},
    "BO": {"name": "볼리비아", "region": "남미"},
    "PY": {"name": "파라과이", "region": "남미"},
    "UY": {"name": "우루과이", "region": "남미"},
    "GY": {"name": "가이아나", "region": "남미"},
    "SR": {"name": "수리남", "region": "남미"},
    "GF": {"name": "프랑스령 기아나", "region": "남미"},

    # 아프리카
    "EG": {"name": "이집트", "region": "아프리카"},
    "ZA": {"name": "남아프리카 공화국", "region": "아프리카"},
    "NG": {"name": "나이지리아", "region": "아프리카"},
    "KE": {"name": "케냐", "region": "아프리카"},
    "ET": {"name": "에티오피아", "region": "아프리카"},
    "TZ": {"name": "탄자니아", "region": "아프리카"},
    "UG": {"name": "우간다", "region": "아프리카"},
    "GH": {"name": "가나", "region": "아프리카"},
    "MA": {"name": "모로코", "region": "아프리카"},
    "DZ": {"name": "알제리", "region": "아프리카"},
    "TN": {"name": "튀니지", "region": "아프리카"},
    "LY": {"name": "리비아", "region": "아프리카"},
    "SD": {"name": "수단", "region": "아프리카"},
    "SS": {"name": "남수단", "region": "아프리카"},
    "AO": {"name": "앙골라", "region": "아프리카"},
    "MZ": {"name": "모잠비크", "region": "아프리카"},
    "ZW": {"name": "짐바브웨", "region": "아프리카"},
    "ZM": {"name": "잠비아", "region": "아프리카"},
    "MW": {"name": "말라위", "region": "아프리카"},
    "BW": {"name": "보츠와나", "region": "아프리카"},
    "NA": {"name": "나미비아", "region": "아프리카"},
    "SN": {"name": "세네갈", "region": "아프리카"},
    "CI": {"name": "코트디부아르", "region": "아프리카"},
    "CM": {"name": "카메룬", "region": "아프리카"},
    "CD": {"name": "콩고민주공화국", "region": "아프리카"},
    "CG": {"name": "콩고공화국", "region": "아프리카"},
    "GA": {"name": "가봉", "region": "아프리카"},
    "GQ": {"name": "적도 기니", "region": "아프리카"},
    "CF": {"name": "중앙아프리카공화국", "region": "아프리카"},
    "TD": {"name": "차드", "region": "아프리카"},
    "NE": {"name": "니제르", "region": "아프리카"},
    "ML": {"name": "말리", "region": "아프리카"},
    "BF": {"name": "부르키나파소", "region": "아프리카"},
    "MR": {"name": "모리타니", "region": "아프리카"},
    "GM": {"name": "감비아", "region": "아프리카"},
    "GW": {"name": "기니비사우", "region": "아프리카"},
    "GN": {"name": "기니", "region": "아프리카"},
    "SL": {"name": "시에라리온", "region": "아프리카"},
    "LR": {"name": "라이베리아", "region": "아프리카"},
    "TG": {"name": "토고", "region": "아프리카"},
    "BJ": {"name": "베냉", "region": "아프리카"},
    "RW": {"name": "르완다", "region": "아프리카"},
    "BI": {"name": "부룬디", "region": "아프리카"},
    "SO": {"name": "소말리아", "region": "아프리카"},
    "DJ": {"name": "지부티", "region": "아프리카"},
    "ER": {"name": "에리트레아", "region": "아프리카"},
    "MG": {"name": "마다가스카르", "region": "아프리카"},
    "MU": {"name": "모리셔스", "region": "아프리카"},
    "SC": {"name": "세이셸", "region": "아프리카"},
    "KM": {"name": "코모로", "region": "아프리카"},
    "CV": {"name": "카보베르데", "region": "아프리카"},
    "ST": {"name": "상투메 프린시페", "region": "아프리카"},
    "SZ": {"name": "에스와티니", "region": "아프리카"},
    "LS": {"name": "레소토", "region": "아프리카"},

    # 오세아니아
    "AU": {"name": "호주", "region": "오세아니아"},
    "NZ": {"name": "뉴질랜드", "region": "오세아니아"},
    "PG": {"name": "파푸아뉴기니", "region": "오세아니아"},
    "FJ": {"name": "피지", "region": "오세아니아"},
    "SB": {"name": "솔로몬 제도", "region": "오세아니아"},
    "VU": {"name": "바누아투", "region": "오세아니아"},
    "WS": {"name": "사모아", "region": "오세아니아"},
    "TO": {"name": "통가", "region": "오세아니아"},
    "KI": {"name": "키리바시", "region": "오세아니아"},
    "FM": {"name": "미크로네시아", "region": "오세아니아"},
    "MH": {"name": "마셜 제도", "region": "오세아니아"},
    "PW": {"name": "팔라우", "region": "오세아니아"},
    "NR": {"name": "나우루", "region": "오세아니아"},
    "TV": {"name": "투발루", "region": "오세아니아"},

    # 중앙아시아
    "KZ": {"name": "카자흐스탄", "region": "중앙아시아"},
    "UZ": {"name": "우즈베키스탄", "region": "중앙아시아"},
    "TM": {"name": "투르크메니스탄", "region": "중앙아시아"},
    "KG": {"name": "키르기스스탄", "region": "중앙아시아"},
    "TJ": {"name": "타지키스탄", "region": "중앙아시아"},

    # 코카서스
    "GE": {"name": "조지아", "region": "코카서스"},
    "AM": {"name": "아르메니아", "region": "코카서스"},
    "AZ": {"name": "아제르바이잔", "region": "코카서스"},
}

# 진행 상황 저장 파일
PROGRESS_FILE = "collection_progress.json"
BATCH_SIZE = 1000
MAX_RETRIES = 3
RETRY_DELAY = 5  # 초
API_DELAY = 0.5  # 초 (API 호출 간격)


class DataCollector:
    """전 세계 생물 데이터 수집기"""

    def __init__(self, db: Session):
        self.db = db
        self.progress = self._load_progress()
        self.stats = {
            "total_collected": 0,
            "total_duplicates": 0,
            "total_errors": 0,
            "countries_completed": 0
        }

    def _load_progress(self) -> Dict:
        """진행 상황 로드"""
        if os.path.exists(PROGRESS_FILE):
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "completed_countries": [],
            "in_progress": None,
            "last_update": None,
            "stats": {}
        }

    def _save_progress(self):
        """진행 상황 저장"""
        self.progress["last_update"] = datetime.now().isoformat()
        self.progress["stats"] = self.stats
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.progress, f, ensure_ascii=False, indent=2)

    def get_existing_species(self) -> Set[str]:
        """기존 종 목록 가져오기 (중복 체크용)"""
        existing = self.db.query(Species.scientific_name).filter(
            Species.scientific_name.isnot(None)
        ).all()
        return {s[0] for s in existing if s[0]}

    async def collect_for_country(
        self,
        country_code: str,
        target_count: int = 100,
        categories: Optional[List[str]] = None
    ) -> Dict:
        """특정 국가의 데이터 수집"""
        country_info = COUNTRIES.get(country_code)
        if not country_info:
            logger.error(f"Unknown country code: {country_code}")
            return {"error": f"Unknown country: {country_code}"}

        country_name = country_info["name"]
        region = country_info["region"]

        logger.info(f"Starting collection for {country_name} ({country_code})")
        self.progress["in_progress"] = country_code

        # 카테고리별 목표 수 계산
        if categories:
            category_targets = {cat: target_count // len(categories) for cat in categories}
        else:
            category_targets = {
                cat: int(target_count * ratio)
                for cat, ratio in CATEGORY_RATIOS.items()
            }

        collected = {cat: 0 for cat in category_targets}
        errors = []
        existing_species = self.get_existing_species()

        async with GBIFService() as gbif:
            for category, target in category_targets.items():
                search_terms = CATEGORY_SEARCH_TERMS.get(category, [category])

                for term in search_terms:
                    if collected[category] >= target:
                        break

                    remaining = target - collected[category]
                    retry_count = 0

                    while retry_count < MAX_RETRIES:
                        try:
                            logger.info(f"  [{country_code}] {category}: searching '{term}' (need {remaining} more)")

                            # GBIF API 호출
                            taxon_key = CATEGORY_TO_TAXON_KEY.get(category)
                            species_list = await gbif.fetch_species_by_region(
                                country_code=country_code,
                                limit=min(remaining * 2, 500),  # 여유있게 가져옴
                                taxon_key=taxon_key
                            )

                            if not species_list:
                                logger.warning(f"  No results for {term} in {country_code}")
                                break

                            # 중복 제거 및 저장
                            new_count = 0
                            for species_data in species_list:
                                scientific_name = species_data.get("scientific_name")

                                # 중복 체크
                                if scientific_name and scientific_name in existing_species:
                                    self.stats["total_duplicates"] += 1
                                    continue

                                # 좌표 추출
                                lat = species_data.get("decimalLatitude")
                                lon = species_data.get("decimalLongitude")

                                # DB에 저장
                                new_species = Species(
                                    name=species_data.get("vernacularName") or species_data.get("species", "Unknown"),
                                    scientific_name=scientific_name,
                                    category=category,
                                    region=region,
                                    country=country_name,
                                    description=species_data.get("description", ""),
                                    image_url=species_data.get("image_url"),
                                    conservation_status=species_data.get("conservation_status", "관심대상"),
                                    latitude=lat,
                                    longitude=lon
                                )

                                self.db.add(new_species)
                                existing_species.add(scientific_name)
                                new_count += 1
                                collected[category] += 1

                                if collected[category] >= target:
                                    break

                            # 배치 커밋
                            self.db.commit()
                            self.stats["total_collected"] += new_count
                            logger.info(f"  [{country_code}] {category}: collected {new_count} species")

                            # API 호출 간격
                            await asyncio.sleep(API_DELAY)
                            break

                        except Exception as e:
                            retry_count += 1
                            logger.error(f"  Error (attempt {retry_count}/{MAX_RETRIES}): {str(e)}")
                            errors.append(str(e))

                            # 트랜잭션 롤백
                            self.db.rollback()

                            if retry_count < MAX_RETRIES:
                                await asyncio.sleep(RETRY_DELAY * retry_count)
                            else:
                                self.stats["total_errors"] += 1

        # 국가 완료 처리
        if country_code not in self.progress["completed_countries"]:
            self.progress["completed_countries"].append(country_code)
        self.progress["in_progress"] = None
        self.stats["countries_completed"] += 1
        self._save_progress()

        result = {
            "country": country_name,
            "country_code": country_code,
            "region": region,
            "collected": collected,
            "total": sum(collected.values()),
            "errors": errors
        }

        logger.info(f"Completed {country_name}: {result['total']} species collected")
        return result

    async def collect_all(
        self,
        target_per_country: int = 100,
        categories: Optional[List[str]] = None,
        resume: bool = True
    ) -> Dict:
        """모든 국가 데이터 수집"""
        results = []
        countries_to_process = list(COUNTRIES.keys())

        # 재개 모드: 완료된 국가 건너뛰기
        if resume:
            completed = set(self.progress.get("completed_countries", []))
            countries_to_process = [c for c in countries_to_process if c not in completed]
            logger.info(f"Resuming collection: {len(completed)} countries already completed")

        total_countries = len(countries_to_process)
        logger.info(f"Starting collection for {total_countries} countries")

        for i, country_code in enumerate(countries_to_process, 1):
            logger.info(f"\n{'='*50}")
            logger.info(f"Progress: {i}/{total_countries} ({i/total_countries*100:.1f}%)")
            logger.info(f"{'='*50}")

            result = await self.collect_for_country(
                country_code,
                target_count=target_per_country,
                categories=categories
            )
            results.append(result)

            # 중간 저장
            self._save_progress()

        return {
            "total_countries": total_countries,
            "results": results,
            "stats": self.stats
        }

    def show_status(self):
        """진행 상황 출력"""
        completed = len(self.progress.get("completed_countries", []))
        total = len(COUNTRIES)
        in_progress = self.progress.get("in_progress")

        print("\n" + "="*50)
        print("데이터 수집 진행 상황")
        print("="*50)
        print(f"완료된 국가: {completed}/{total} ({completed/total*100:.1f}%)")
        print(f"현재 진행 중: {in_progress or 'None'}")
        print(f"마지막 업데이트: {self.progress.get('last_update', 'N/A')}")

        if self.progress.get("stats"):
            stats = self.progress["stats"]
            print(f"\n수집 통계:")
            print(f"  - 총 수집: {stats.get('total_collected', 0)}종")
            print(f"  - 중복 제거: {stats.get('total_duplicates', 0)}건")
            print(f"  - 에러: {stats.get('total_errors', 0)}건")

        if self.progress.get("completed_countries"):
            print(f"\n완료된 국가: {', '.join(self.progress['completed_countries'][:10])}")
            if len(self.progress['completed_countries']) > 10:
                print(f"  ... 외 {len(self.progress['completed_countries'])-10}개국")

        print("="*50 + "\n")


async def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="전 세계 생물 데이터 수집 스크립트")

    parser.add_argument("--all", action="store_true", help="모든 국가 데이터 수집")
    parser.add_argument("--countries", type=str, help="특정 국가만 수집 (쉼표 구분)")
    parser.add_argument("--categories", type=str, help="특정 카테고리만 수집 (쉼표 구분)")
    parser.add_argument("--target", type=int, default=100, help="국가당 목표 종 수")
    parser.add_argument("--status", action="store_true", help="진행 상황 확인")
    parser.add_argument("--resume", action="store_true", help="중단된 작업 재개")
    parser.add_argument("--reset", action="store_true", help="진행 상황 초기화")

    args = parser.parse_args()

    # DB 세션 생성
    db = SessionLocal()

    try:
        collector = DataCollector(db)

        # 진행 상황 확인
        if args.status:
            collector.show_status()
            return

        # 진행 상황 초기화
        if args.reset:
            if os.path.exists(PROGRESS_FILE):
                os.remove(PROGRESS_FILE)
                print("진행 상황이 초기화되었습니다.")
            return

        # 카테고리 파싱
        categories = None
        if args.categories:
            categories = [c.strip() for c in args.categories.split(",")]
            logger.info(f"Selected categories: {categories}")

        # 전체 수집
        if args.all or args.resume:
            start_time = time.time()
            result = await collector.collect_all(
                target_per_country=args.target,
                categories=categories,
                resume=args.resume or args.all
            )
            elapsed = time.time() - start_time

            print("\n" + "="*50)
            print("수집 완료!")
            print("="*50)
            print(f"소요 시간: {elapsed/3600:.1f}시간")
            print(f"총 수집: {collector.stats['total_collected']}종")
            print(f"국가 수: {collector.stats['countries_completed']}개국")
            print("="*50)

        # 특정 국가만 수집
        elif args.countries:
            country_codes = [c.strip().upper() for c in args.countries.split(",")]

            for code in country_codes:
                if code not in COUNTRIES:
                    print(f"Unknown country code: {code}")
                    continue

                result = await collector.collect_for_country(
                    code,
                    target_count=args.target,
                    categories=categories
                )
                print(f"\n{result['country']}: {result['total']}종 수집 완료")

        else:
            parser.print_help()

    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())

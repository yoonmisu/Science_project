"""
Google Cloud Translation API 기반 번역 서비스
무료 티어: 월 500,000자 (약 2,500회 종 정보 번역 가능)
API 키 없이도 동작 (원본 텍스트 반환)

영구 캐시 시스템:
- 번역 결과를 JSON 파일에 저장하여 서버 재시작/배포 후에도 유지
- 여러 사용자가 동일 종 정보 요청 시 캐시에서 즉시 반환
- 언어별로 분리 저장하여 Git에 포함 가능
"""
import os
import httpx
from typing import Optional, Dict, Any
import asyncio
import hashlib
import json
import threading
from datetime import datetime
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

class TranslationService:
    # 지원하는 언어 코드 매핑 (Google Translate용)
    SUPPORTED_LANGUAGES = {
        'ko': 'ko',  # 한국어
        'en': 'en',  # 영어
        'ja': 'ja',  # 일본어
        'zh': 'zh-CN',  # 중국어 (간체)
        'zh-TW': 'zh-TW',  # 중국어 (번체)
        'es': 'es',  # 스페인어
        'fr': 'fr',  # 프랑스어
        'de': 'de',  # 독일어
        'pt': 'pt',  # 포르투갈어
        'ru': 'ru',  # 러시아어
        'it': 'it',  # 이탈리아어
        'vi': 'vi',  # 베트남어
        'th': 'th',  # 태국어
        'id': 'id',  # 인도네시아어
        'ar': 'ar',  # 아랍어
        'hi': 'hi',  # 힌디어
    }

    def __init__(self):
        self.api_key = os.getenv("GOOGLE_TRANSLATE_API_KEY", "")
        self.client = httpx.AsyncClient(timeout=10.0)

        # 캐시 디렉토리 설정
        self._cache_dir = os.path.join(
            os.path.dirname(__file__), "..", "data", "translations"
        )
        os.makedirs(self._cache_dir, exist_ok=True)

        # 메모리 캐시 (언어별)
        self._cache: Dict[str, Dict[str, Any]] = {}

        # 저장 대기 큐 (배치 저장용)
        self._pending_saves: Dict[str, bool] = {}
        self._save_lock = threading.Lock()

        # 모든 언어 캐시 로드
        self._load_all_caches()

    def _get_cache_file(self, lang: str) -> str:
        """언어별 캐시 파일 경로"""
        return os.path.join(self._cache_dir, f"translations_{lang}.json")

    def _load_all_caches(self):
        """모든 언어 캐시 파일 로드"""
        total_entries = 0
        for lang in self.SUPPORTED_LANGUAGES.keys():
            if lang == 'en':
                continue  # 영어는 번역 불필요
            cache_file = self._get_cache_file(lang)
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        self._cache[lang] = data.get("translations", {})
                        total_entries += len(self._cache[lang])
                except Exception as e:
                    print(f"⚠️ {lang} 번역 캐시 로드 실패: {e}")
                    self._cache[lang] = {}
            else:
                self._cache[lang] = {}

        if total_entries > 0:
            print(f"✅ 번역 캐시 로드 완료: 총 {total_entries}개 항목")

    def _save_cache(self, lang: str):
        """특정 언어 캐시를 파일에 저장"""
        if lang == 'en' or lang not in self._cache:
            return

        with self._save_lock:
            try:
                cache_file = self._get_cache_file(lang)
                data = {
                    "language": lang,
                    "updated_at": datetime.now().isoformat(),
                    "count": len(self._cache[lang]),
                    "translations": self._cache[lang]
                }
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"💾 {lang} 번역 캐시 저장: {len(self._cache[lang])}개 항목")
            except Exception as e:
                print(f"⚠️ {lang} 번역 캐시 저장 실패: {e}")

    def _get_cache_key(self, text: str) -> str:
        """캐시 키 생성 (텍스트의 MD5 해시)"""
        return hashlib.md5(text.encode()).hexdigest()

    def get_cached_translation(self, text: str, target_lang: str) -> Optional[str]:
        """캐시에서 번역 조회"""
        if target_lang not in self._cache:
            return None
        cache_key = self._get_cache_key(text)
        cached = self._cache[target_lang].get(cache_key)
        if cached:
            return cached.get("translated_text")
        return None

    def set_cached_translation(self, text: str, translated: str, target_lang: str):
        """캐시에 번역 저장"""
        if target_lang not in self._cache:
            self._cache[target_lang] = {}

        cache_key = self._get_cache_key(text)
        self._cache[target_lang][cache_key] = {
            "original_text": text[:100] + "..." if len(text) > 100 else text,  # 원본 미리보기
            "translated_text": translated,
            "cached_at": datetime.now().isoformat()
        }

        # 파일에 저장
        self._save_cache(target_lang)

    async def translate(
        self,
        text: str,
        target_lang: str = "ko",
        source_lang: str = "en"
    ) -> str:
        """
        텍스트를 대상 언어로 번역합니다 (Google Cloud Translation API 사용).

        Args:
            text: 번역할 텍스트
            target_lang: 대상 언어 코드 (ko, ja, zh 등)
            source_lang: 원본 언어 코드 (기본값: en)

        Returns:
            번역된 텍스트 또는 원본 텍스트 (API 키가 없거나 오류 시)
        """
        # 영어면 번역 불필요
        if target_lang == "en":
            return text

        # 빈 텍스트 처리
        if not text or not text.strip():
            return text

        # 캐시 확인 (영구 캐시에서 조회)
        cached = self.get_cached_translation(text, target_lang)
        if cached:
            print(f"✅ 번역 캐시 히트: {target_lang} ({len(text)} chars)")
            return cached

        # API 키 확인
        if not self.api_key:
            print(f"⚠️ GOOGLE_TRANSLATE_API_KEY 미설정, 원본 반환")
            return text

        try:
            # Google Cloud Translation API v2 호출
            target_code = self.SUPPORTED_LANGUAGES.get(target_lang, target_lang)

            response = await self.client.post(
                "https://translation.googleapis.com/language/translate/v2",
                params={"key": self.api_key},
                json={
                    "q": text,
                    "source": source_lang,
                    "target": target_code,
                    "format": "text"
                }
            )

            if response.status_code == 200:
                result = response.json()
                translations = result.get("data", {}).get("translations", [])
                if translations:
                    translated = translations[0].get("translatedText", text)

                    # 영구 캐시에 저장
                    self.set_cached_translation(text, translated, target_lang)

                    print(f"✅ Google 번역 완료: {target_lang} ({len(text)} -> {len(translated)} chars)")
                    return translated
                else:
                    print(f"⚠️ Google Translate 응답에 번역 결과 없음")
                    return text
            else:
                error_msg = response.text[:200] if response.text else "Unknown error"
                print(f"⚠️ Google Translate API 오류: {response.status_code} - {error_msg}")
                return text

        except Exception as e:
            print(f"❌ 번역 오류: {e}")
            return text

    async def translate_species_info(
        self,
        species_data: Dict[str, Any],
        target_lang: str = "ko"
    ) -> Dict[str, Any]:
        """
        종 정보 전체를 번역합니다.
        description과 common_name을 번역하고, translated 필드를 추가합니다.

        Args:
            species_data: 종 정보 딕셔너리
            target_lang: 대상 언어 코드

        Returns:
            번역된 종 정보 딕셔너리
        """
        if target_lang == "en":
            return species_data

        # 번역할 필드들
        tasks = []

        # description 번역
        description = species_data.get("description", "")
        if description:
            tasks.append(self.translate(description, target_lang))
        else:
            async def return_empty():
                return ""
            tasks.append(return_empty())

        # common_name 번역 (학명이 아닌 일반명만)
        common_name = species_data.get("common_name", "")
        # 학명 패턴 감지 (두 단어, 첫 글자 대문자, 이탤릭 형식)
        is_scientific_name = False
        if common_name and " " in common_name:
            parts = common_name.split()
            if len(parts) >= 2:
                is_scientific_name = (
                    parts[0][0].isupper() and
                    parts[1][0].islower()
                )

        if common_name and not is_scientific_name:
            tasks.append(self.translate(common_name, target_lang))
        else:
            async def return_common_name():
                return common_name
            tasks.append(return_common_name())

        # 병렬 번역 실행
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            translated_description = results[0] if not isinstance(results[0], Exception) else description
            translated_name = results[1] if not isinstance(results[1], Exception) else common_name

            # 결과 적용
            species_data["description"] = translated_description
            if translated_name:
                species_data["common_name"] = translated_name
                species_data["name"] = translated_name  # name 필드도 업데이트
            species_data["translated"] = True
            species_data["lang"] = target_lang

        except Exception as e:
            print(f"❌ 종 정보 번역 오류: {e}")
            species_data["translated"] = False
            species_data["lang"] = "en"

        return species_data

    def get_cache_stats(self) -> Dict[str, int]:
        """캐시 통계 반환"""
        stats = {}
        for lang, cache in self._cache.items():
            stats[lang] = len(cache)
        return stats

    async def close(self):
        await self.client.aclose()


# 싱글톤 인스턴스
translation_service = TranslationService()

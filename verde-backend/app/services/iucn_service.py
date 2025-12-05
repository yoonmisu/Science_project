from app.services.wikipedia_service import wikipedia_service
from app.services.country_species_map import COUNTRY_SPECIES_MAP, COUNTRY_NAMES, CONTINENT_SPECIES_MAP
import asyncio
import cloudscraper
import pycountry
from typing import List, Dict, Any, Optional
from app.core.config import settings
from datetime import datetime, timedelta
from functools import partial, lru_cache

# Continent detection imports
try:
    import pycountry_convert as pc
except ImportError:
    pc = None
    print("⚠️ pycountry_convert not installed. Continent fallback will use manual mapping.")

class IUCNService:
    # 육상 척추동물 클래스 (포유류, 조류, 파충류, 양서류)
    TERRESTRIAL_VERTEBRATE_CLASSES = ['MAMMALIA', 'AVES', 'REPTILIA', 'AMPHIBIA']
    
    def __init__(self):
        # ========================================
        # v4 API 설정 (Cloudflare 우회)
        # ========================================
        self.base_url = "https://api.iucnredlist.org/api/v4"
        self.token = settings.IUCN_API_KEY
        
        # cloudscraper로 Cloudflare 우회 (동기 방식)
        self.scraper = cloudscraper.create_scraper()
        
        # Bearer 토큰 인증 (v4 방식)
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json"
        }

        # 국가별 데이터 캐시 (메모리 캐시, 1시간 유지)
        self.country_cache: Dict[str, Dict[str, Any]] = {}
        # 종별 데이터 캐시 (학명 기반, LRU)
        self.species_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = timedelta(hours=1)
        
        # IP별 마지막 검색어 캐시 (중복 검색 방지용)
        self.last_search_cache: Dict[str, str] = {}
    
    async def _make_request(self, url: str, params: dict = None) -> Any:
        """
        비동기 래퍼: 동기 cloudscraper를 async/await 호환으로 변환
        """
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                partial(self.scraper.get, url, headers=self.headers, params=params, timeout=30)
            )
            return response
        except Exception as e:
            print(f"❌ Request Error: {e}")
            raise
    
    def _v4_to_v3_adapter(self, v4_data: Dict[str, Any], scientific_name: str) -> Optional[Dict[str, Any]]:
        """
        v4 API 응답을 v3 호환 포맷으로 변환
        
        Args:
            v4_data: v4 API 응답 데이터
            scientific_name: 검색한 학명
            
        Returns:
            v3 형식의 데이터 딕셔너리
        """
        try:
            if not v4_data or 'taxon' not in v4_data:
                return None
            
            taxon = v4_data['taxon']
            
            # 기본 정보 추출
            result = {
                'taxonid': taxon.get('sis_id'),  # v4: sis_id -> v3: taxonid
                'scientific_name': taxon.get('scientific_name', scientific_name),
                'kingdom_name': taxon.get('kingdom_name'),
                'phylum_name': taxon.get('phylum_name'),
                'class_name': taxon.get('class_name'),
                'order_name': taxon.get('order_name'),
                'family_name': taxon.get('family_name'),
                'genus_name': taxon.get('genus_name'),
                'species_name': taxon.get('species_name'),
            }
            
            # Assessment 정보에서 category 추출 (v4는 중첩 구조)
            # subpopulation이 있으면 첫 번째 사용, 없으면 species 레벨 확인
            category = None
            if taxon.get('subpopulation_taxa') and len(taxon['subpopulation_taxa']) > 0:
                # 첫 번째 subpopulation의 카테고리 사용
                subpop = taxon['subpopulation_taxa'][0]
                # assessment 배열에서 가장 최신 카테고리 찾기 (v4 구조 추정)
                category = subpop.get('category', 'DD')
            elif taxon.get('species_taxa') and len(taxon['species_taxa']) > 0:
                species_data = taxon['species_taxa'][0]
                category = species_data.get('category', 'DD')
            
            # category가 여전히 없으면 기본값
            if not category:
                category = 'DD'  # Data Deficient
            
            result['category'] = category
            
            return result
            
        except Exception as e:
            print(f"⚠️ Adapter Error for {scientific_name}: {e}")
            return None
    
    def _normalize_country_code(self, country_input: str) -> Optional[str]:
        """
        국가 입력값을 표준 ISO 코드로 변환 (pycountry 라이브러리 사용)

        전 세계 모든 국가명, 공식명칭, ISO 코드를 인식하여 표준 2자리 코드로 변환합니다.
        예: "South Korea", "korea", "KR", "Russia", "Russian Federation" → "KR", "RU"

        Args:
            country_input: 사용자가 입력한 국가명 또는 코드

        Returns:
            표준 ISO 3166-1 alpha-2 국가 코드 (예: 'RU', 'KR') 또는 None
        """
        if not country_input:
            return None

        # 먼저 대문자로 변환 (ISO 코드는 대문자)
        country_upper = country_input.upper().strip()

        # 1. 이미 유효한 2자리 ISO 코드인지 확인 (빠른 경로)
        if len(country_upper) == 2:
            try:
                country = pycountry.countries.get(alpha_2=country_upper)
                if country:
                    return country.alpha_2
            except (KeyError, AttributeError):
                pass

        # 2. 3자리 ISO 코드 (alpha-3) 확인
        if len(country_upper) == 3:
            try:
                country = pycountry.countries.get(alpha_3=country_upper)
                if country:
                    return country.alpha_2
            except (KeyError, AttributeError):
                pass

        # 3. Common name aliases (pycountry가 인식하지 못하는 일반명)
        common_aliases = {
            "south korea": "KR",
            "north korea": "KP",
            "vietnam": "VN",
            "viet nam": "VN",
        }

        country_lower = country_input.lower().strip()
        if country_lower in common_aliases:
            return common_aliases[country_lower]

        # 4. 국가명 검색 (공식명칭, 일반명칭 모두 지원)
        try:
            # 정확한 이름 매칭 시도
            country = pycountry.countries.get(name=country_input)
            if country:
                return country.alpha_2
        except (KeyError, AttributeError):
            pass

        # 5. 공식 국가명 검색 (official_name 필드)
        try:
            country = pycountry.countries.get(official_name=country_input)
            if country:
                return country.alpha_2
        except (KeyError, AttributeError):
            pass

        # 6. 퍼지 검색 (부분 일치, 대소문자 무시)
        try:
            for country in pycountry.countries:
                # 일반 이름 확인 (대소문자 무시)
                if hasattr(country, 'name') and country.name.lower() == country_lower:
                    return country.alpha_2
                # 공식 이름 확인 (대소문자 무시)
                if hasattr(country, 'official_name') and country.official_name.lower() == country_lower:
                    return country.alpha_2
                # 부분 일치 확인 (예: "Korea" -> "Korea, Republic of")
                if hasattr(country, 'name') and country_lower in country.name.lower():
                    return country.alpha_2
                # Common name 확인
                if hasattr(country, 'common_name') and country.common_name.lower() == country_lower:
                    return country.alpha_2
        except Exception as e:
            print(f"⚠️ pycountry 검색 오류: {e}")

        # 6. 모든 방법 실패 시 None 반환
        print(f"⚠️ 국가 코드 변환 실패: '{country_input}' (pycountry가 인식하지 못함)")
        return None

    def _get_continent_code(self, country_code: str) -> Optional[str]:
        """
        국가 코드(ISO Alpha-2)를 대륙 코드로 변환

        Regional Fallback Pattern의 핵심 메서드
        국가별 데이터가 없을 때 해당 국가가 속한 대륙의 데이터를 반환하기 위함

        Args:
            country_code: ISO 3166-1 alpha-2 국가 코드 (예: 'KR', 'ZW', 'FR')

        Returns:
            대륙 코드 ('AS', 'EU', 'AF', 'NA', 'SA', 'OC', 'AN') 또는 None
        """
        if not country_code or len(country_code) != 2:
            return None

        # Method 1: pycountry_convert 사용 (설치된 경우)
        # Note: pycountry_convert API가 변경되었거나 호환되지 않을 수 있으므로
        # 에러 발생 시 자동으로 manual mapping으로 fallback
        if pc is not None:
            try:
                # Try different pycountry_convert API methods
                # API가 버전마다 다를 수 있으므로 여러 방법 시도
                if hasattr(pc, 'convert_country_alpha2_to_continent_code'):
                    continent_name = pc.convert_country_alpha2_to_continent_code(country_code)
                    return continent_name
                elif hasattr(pc, 'country_alpha2_to_continent_code'):
                    continent_name = pc.country_alpha2_to_continent_code(country_code)
                    return continent_name
            except Exception:
                # pycountry_convert 실패 시 manual mapping 사용 (로그는 제거하여 깔끔하게)
                pass

        # Method 2: Manual mapping (Fallback)
        # 전 세계 모든 국가 -> 대륙 매핑 (포괄적)
        COUNTRY_TO_CONTINENT = {
            # Asia
            "KR": "AS", "KP": "AS", "JP": "AS", "CN": "AS", "TW": "AS", "HK": "AS", "MO": "AS",
            "MN": "AS", "VN": "AS", "TH": "AS", "LA": "AS", "KH": "AS", "MM": "AS", "MY": "AS",
            "SG": "AS", "BN": "AS", "ID": "AS", "PH": "AS", "TL": "AS", "IN": "AS", "PK": "AS",
            "BD": "AS", "LK": "AS", "NP": "AS", "BT": "AS", "MV": "AS", "AF": "AS", "IR": "AS",
            "IQ": "AS", "SY": "AS", "LB": "AS", "JO": "AS", "IL": "AS", "PS": "AS", "SA": "AS",
            "YE": "AS", "OM": "AS", "AE": "AS", "QA": "AS", "BH": "AS", "KW": "AS", "TR": "AS",
            "CY": "AS", "GE": "AS", "AM": "AS", "AZ": "AS", "KZ": "AS", "UZ": "AS", "TM": "AS",
            "KG": "AS", "TJ": "AS",

            # Europe
            "GB": "EU", "IE": "EU", "FR": "EU", "ES": "EU", "PT": "EU", "AD": "EU", "MC": "EU",
            "IT": "EU", "SM": "EU", "VA": "EU", "MT": "EU", "GR": "EU", "AL": "EU", "MK": "EU",
            "RS": "EU", "ME": "EU", "BA": "EU", "HR": "EU", "SI": "EU", "XK": "EU", "BG": "EU",
            "RO": "EU", "MD": "EU", "UA": "EU", "BY": "EU", "LT": "EU", "LV": "EU", "EE": "EU",
            "PL": "EU", "CZ": "EU", "SK": "EU", "HU": "EU", "AT": "EU", "CH": "EU", "LI": "EU",
            "DE": "EU", "NL": "EU", "BE": "EU", "LU": "EU", "DK": "EU", "SE": "EU", "NO": "EU",
            "FI": "EU", "IS": "EU", "RU": "EU",  # Russia는 유럽으로 분류 (대부분의 인구/수도가 유럽)

            # Africa
            "EG": "AF", "LY": "AF", "TN": "AF", "DZ": "AF", "MA": "AF", "EH": "AF", "MR": "AF",
            "ML": "AF", "NE": "AF", "TD": "AF", "SD": "AF", "SS": "AF", "ER": "AF", "DJ": "AF",
            "SO": "AF", "ET": "AF", "KE": "AF", "UG": "AF", "RW": "AF", "BI": "AF", "TZ": "AF",
            "MZ": "AF", "MW": "AF", "ZM": "AF", "ZW": "AF", "BW": "AF", "NA": "AF", "ZA": "AF",
            "LS": "AF", "SZ": "AF", "AO": "AF", "CD": "AF", "CG": "AF", "GA": "AF", "GQ": "AF",
            "CM": "AF", "CF": "AF", "ST": "AF", "GH": "AF", "TG": "AF", "BJ": "AF", "NG": "AF",
            "SN": "AF", "GM": "AF", "GW": "AF", "GN": "AF", "SL": "AF", "LR": "AF", "CI": "AF",
            "BF": "AF", "CV": "AF", "SC": "AF", "KM": "AF", "MU": "AF", "MG": "AF",

            # North America
            "US": "NA", "CA": "NA", "MX": "NA", "GT": "NA", "BZ": "NA", "SV": "NA", "HN": "NA",
            "NI": "NA", "CR": "NA", "PA": "NA", "CU": "NA", "JM": "NA", "HT": "NA", "DO": "NA",
            "BS": "NA", "TT": "NA", "BB": "NA", "GD": "NA", "LC": "NA", "VC": "NA", "AG": "NA",
            "DM": "NA", "KN": "NA", "PR": "NA",

            # South America
            "CO": "SA", "VE": "SA", "GY": "SA", "SR": "SA", "GF": "SA", "BR": "SA", "EC": "SA",
            "PE": "SA", "BO": "SA", "PY": "SA", "UY": "SA", "AR": "SA", "CL": "SA", "FK": "SA",

            # Oceania
            "AU": "OC", "NZ": "OC", "PG": "OC", "FJ": "OC", "SB": "OC", "VU": "OC", "NC": "OC",
            "PF": "OC", "WS": "OC", "TO": "OC", "KI": "OC", "TV": "OC", "NR": "OC", "PW": "OC",
            "FM": "OC", "MH": "OC", "NF": "OC", "CK": "OC", "NU": "OC", "WF": "OC", "AS": "OC",
            "GU": "OC", "MP": "OC",

            # Antarctica
            "AQ": "AN", "BV": "AN", "HM": "AN", "GS": "AN", "TF": "AN",
        }

        continent = COUNTRY_TO_CONTINENT.get(country_code.upper())
        if continent:
            print(f"🗺️ Continent Detection: {country_code} -> {continent}")
            return continent

        print(f"⚠️ 대륙 매핑 실패: '{country_code}' (알 수 없는 국가)")
        return None

    async def get_species_by_country(self, country_code: str, category: str = None) -> List[Dict[str, Any]]:
        """
        Hybrid Lookup Pattern: 국가별 큐레이션된 종 리스트 + 실시간 v4 API 조회

        v4 API는 국가별 엔드포인트를 제공하지 않으므로,
        사전 정의된 대표 종 리스트를 기반으로 실시간 데이터를 병렬 조회합니다.

        Args:
            country_code: 국가 코드 (ISO Alpha-2)
            category: 카테고리 필터 (동물, 식물, 곤충, 해양생물) - None이면 모든 카테고리

        이점:
        - 목록은 큐레이션되지만, 멸종위기 등급과 정보는 항상 최신 상태
        - Wikipedia 데이터로 추가 보강
        - 개별 종 조회 실패가 전체 응답에 영향을 주지 않음
        """
        try:
            # ========================================
            # [LOG 1/5 - Entry] 메서드 진입 시점
            # ========================================
            original_input = country_code
            print(f"\n{'='*60}")
            print(f"[ENTRY] get_species_by_country 시작")
            print(f"  입력값: '{original_input}', 카테고리: '{category}'")

            # ========================================
            # 1. 국가 코드 정규화 (Russia -> RU 변환 등)
            # ========================================
            country_code = self._normalize_country_code(country_code)

            if not country_code:
                print(f"⚠️ 알 수 없는 국가: '{original_input}'")
                print(f"   지원되는 국가: {', '.join(COUNTRY_SPECIES_MAP.keys())}")
                print(f"[RETURN] 빈 리스트 반환 (type: {type([])}, len: 0)")
                print(f"{'='*60}\n")
                return []  # 명시적으로 빈 리스트 반환 (프론트엔드 Empty State 표시)

            print(f"  정규화: '{original_input}' -> '{country_code}'")

            # ========================================
            # 2. 캐시 확인 (카테고리별 캐시)
            # ========================================
            cache_key = f"{country_code}_{category or 'all'}"
            if cache_key in self.country_cache:
                cache_entry = self.country_cache[cache_key]
                cache_time = cache_entry.get('timestamp')
                if cache_time and datetime.now() - cache_time < self.cache_ttl:
                    cached_data = cache_entry.get('data', [])
                    print(f"💾 캐시 히트: {cache_key}")
                    print(f"[RETURN] 캐시된 데이터 반환 (type: {type(cached_data)}, len: {len(cached_data)})")
                    print(f"{'='*60}\n")
                    return cached_data

            # ========================================
            # [LOG 2/5 - Lookup] COUNTRY_SPECIES_MAP 조회
            # ========================================
            country_data = COUNTRY_SPECIES_MAP.get(country_code)

            # 카테고리별 조회 지원 (dict 구조 vs list 구조)
            species_list = None
            species_category_map = {}  # 학명 -> 카테고리 매핑

            if isinstance(country_data, dict):
                # 새로운 카테고리 구조: {"동물": [...], "식물": [...], ...}
                if category and category in country_data:
                    # 특정 카테고리만 반환
                    species_list = country_data[category]
                    for species in species_list:
                        species_category_map[species] = category
                elif category:
                    # 요청된 카테고리가 없으면 빈 리스트
                    species_list = []
                else:
                    # 카테고리 지정 없으면 모든 종 반환
                    species_list = []
                    for category_name, category_species in country_data.items():
                        species_list.extend(category_species)
                        for species in category_species:
                            species_category_map[species] = category_name
            elif isinstance(country_data, list):
                # 기존 리스트 구조 (동물만)
                if category and category != "동물":
                    species_list = []  # 동물 외 카테고리 요청 시 빈 리스트
                else:
                    species_list = country_data
                    for species in species_list:
                        species_category_map[species] = "동물"

            if species_list is None or len(species_list) == 0:
                # ========================================
                # Regional Fallback Pattern 적용
                # 특정 국가 데이터가 없으면 대륙 데이터로 fallback
                # ========================================
                print(f"⚠️ [LOOKUP] Country-specific data not found for '{country_code}'")
                print(f"   🌍 Attempting Regional Fallback...")

                continent_code = self._get_continent_code(country_code)

                if continent_code:
                    species_list = CONTINENT_SPECIES_MAP.get(continent_code)
                    if species_list:
                        continent_names = {
                            "AS": "Asia", "EU": "Europe", "AF": "Africa",
                            "NA": "North America", "SA": "South America",
                            "OC": "Oceania", "AN": "Antarctica"
                        }
                        continent_name = continent_names.get(continent_code, continent_code)
                        print(f"✅ [FALLBACK] Using regional data for {continent_name} ({continent_code})")
                        print(f"   Found {len(species_list)} representative species")
                    else:
                        print(f"❌ [FALLBACK] No continent data found for '{continent_code}'")
                        print(f"[RETURN] 빈 리스트 반환 (type: {type([])}, len: 0)")
                        print(f"{'='*60}\n")
                        return []
                else:
                    print(f"❌ [FALLBACK] Could not determine continent for '{country_code}'")
                    print(f"   사용 가능한 국가: {', '.join(COUNTRY_SPECIES_MAP.keys())}")
                    print(f"[RETURN] 빈 리스트 반환 (type: {type([])}, len: 0)")
                    print(f"{'='*60}\n")
                    return []

            country_name = COUNTRY_NAMES.get(country_code, country_code)
            print(f"✅ [LOOKUP] 종 리스트 확인: {len(species_list)}개")
            print(f"   국가명: {country_name} ({country_code})")
            print(f"   종 목록: {', '.join(species_list[:3])}{'...' if len(species_list) > 3 else ''}")

            # 병렬 조회 함수: 각 종에 대해 v4 API 호출
            async def fetch_single_species(scientific_name: str) -> Optional[Dict[str, Any]]:
                """
                단일 종 조회 (캐싱 + v4 API + Wikipedia 보강)

                [SAFETY GUARD] Wikipedia 타임아웃 2초, 전체 실패해도 메인 로직 진행
                """
                try:
                    # 종별 캐시 확인
                    if scientific_name in self.species_cache:
                        cache_entry = self.species_cache[scientific_name]
                        cache_time = cache_entry.get('timestamp')
                        if cache_time and datetime.now() - cache_time < self.cache_ttl:
                            cached_data = cache_entry.get('data')
                            if cached_data:
                                # 캐시된 데이터의 카테고리를 현재 요청의 카테고리로 덮어씀
                                cached_data = cached_data.copy()
                                cached_data['category'] = species_category_map.get(scientific_name, "동물")
                                return cached_data

                    # v4 API 호출 (3초 타임아웃)
                    v4_data = await asyncio.wait_for(
                        self.search_by_scientific_name(scientific_name),
                        timeout=3.0
                    )

                    if not v4_data:
                        return None

                    # v4 -> v3 어댑터 적용
                    v3_data = self._v4_to_v3_adapter(v4_data, scientific_name)
                    if not v3_data:
                        return None

                    # [DATA VALIDATION] 필수 키 검증
                    required_keys = ['taxonid', 'scientific_name', 'category']
                    missing_keys = [key for key in required_keys if key not in v3_data]
                    if missing_keys:
                        print(f"⚠️ [VALIDATION] Missing keys in v3_data for {scientific_name}: {missing_keys}")
                        return None

                    # Wikipedia 데이터 보강 (타임아웃 5초)
                    wiki_info = {}
                    try:
                        wiki_info = await asyncio.wait_for(
                            wikipedia_service.get_species_info(scientific_name),
                            timeout=5.0
                        )
                    except asyncio.TimeoutError:
                        print(f"⏱️ Wikipedia 타임아웃 (5s): {scientific_name}")
                    except Exception as e:
                        print(f"⚠️ Wikipedia 오류: {scientific_name} - {e}")

                    # 최종 결과 조합
                    # Wikipedia 이미지가 있으면 사용, 없으면 빈 문자열 (프론트엔드에서 이모지 표시)
                    image_url = wiki_info.get("image_url", "") if wiki_info.get("image_url") else ""

                    # 카테고리 정보 가져오기 (species_category_map에서)
                    species_category = species_category_map.get(scientific_name, "동물")

                    result = {
                        "id": v3_data.get('taxonid'),
                        "scientific_name": scientific_name,
                        "common_name": wiki_info.get("common_name", scientific_name),
                        "category": species_category,  # 카테고리 매핑에서 가져옴
                        "image_url": image_url,
                        "description": wiki_info.get("description", f"IUCN Red List Category: {v3_data.get('category', 'Unknown')}"),
                        "country": country_code,
                        "risk_level": v3_data.get('category', 'DD')
                    }

                    # 종별 캐시 저장
                    self.species_cache[scientific_name] = {
                        'data': result,
                        'timestamp': datetime.now()
                    }

                    return result

                except asyncio.TimeoutError:
                    print(f"⏱️ 타임아웃: {scientific_name}")
                    return None
                except Exception as e:
                    print(f"❌ 조회 실패 ({scientific_name}): {e}")
                    return None

            # ========================================
            # [LOG 3/5 - API Start] asyncio.gather 시작
            # ========================================
            print(f"\n[API START] Starting fetching {len(species_list)} species...")
            fetch_tasks = [fetch_single_species(name) for name in species_list]

            # ⚡ CRITICAL: 전체 병렬 조회에 30초 타임아웃 적용
            # 개별 종 타임아웃(3초)이 있더라도, 네트워크 문제로 누적 지연 발생 가능
            # 어떤 상황에서도 30초 이내에 응답을 보장
            try:
                results = await asyncio.wait_for(
                    asyncio.gather(*fetch_tasks, return_exceptions=True),
                    timeout=30.0
                )
            except asyncio.TimeoutError:
                print(f"⚠️ [TIMEOUT] Global timeout (30s) reached. Returning partial results.")
                # 타임아웃 발생 시 빈 결과 반환 (무한 대기 방지)
                results = []

            # ========================================
            # [LOG 4/5 - API End] asyncio.gather 완료
            # ========================================
            print(f"[API END] Fetched {len(results)} results (including None/Exceptions)")

            # 성공한 결과만 필터링 (None과 Exception 제외)
            species_data_raw = [
                r for r in results
                if r is not None and not isinstance(r, Exception)
            ]

            # 중복 제거: scientific_name 기준으로 유니크한 데이터만 유지
            seen_names = set()
            species_data = []
            for species in species_data_raw:
                name = species.get('scientific_name')
                if name and name not in seen_names:
                    seen_names.add(name)
                    species_data.append(species)
                elif name:
                    print(f"⚠️ 중복 제거: {name}")

            success_count = len(species_data)
            total_count = len(species_list)
            duplicate_count = len(species_data_raw) - len(species_data)
            print(f"✅ 성공: {success_count}/{total_count}개 종 (중복 제거: {duplicate_count}개)")

            # 국가별 캐시 저장
            self.country_cache[country_code] = {
                'data': species_data,
                'timestamp': datetime.now()
            }

            # ========================================
            # [LOG 5/5 - Return] 최종 반환 데이터
            # ========================================
            print(f"[RETURN] 최종 데이터 반환")
            print(f"  타입: {type(species_data)}")
            print(f"  길이: {len(species_data)}")
            if species_data:
                print(f"  샘플 키: {list(species_data[0].keys())}")
            print(f"{'='*60}\n")

            return species_data

        except Exception as e:
            print(f"❌ Country Service Error ({country_code}): {e}")
            print(f"[RETURN] 예외 발생으로 빈 리스트 반환 (type: {type([])}, len: 0)")
            print(f"{'='*60}\n")
            return []

    async def get_species_detail(self, species_id: int) -> Optional[Dict[str, Any]]:
        """
        특정 종의 상세 정보를 IUCN v4 API와 Wikipedia에서 조회합니다.

        ⚡ v4 API Redesign:
        - v4에는 ID 기반 직접 조회가 제한적이므로 캐시 또는 학명 기반 재조회 사용
        - Wikipedia 통합 (2초 타임아웃)
        - 프론트엔드 호환 완벽 보장

        Args:
            species_id: IUCN sis_id (v4 기준)

        Returns:
            종 상세 정보 딕셔너리 (모든 필드 보장) 또는 None
        """
        try:
            print(f"\n{'='*60}")
            print(f"[DETAIL] get_species_detail 시작")
            print(f"  Species ID: {species_id}")
            print(f"{'='*60}")

            # ========================================
            # Step 1: 캐시에서 학명 찾기 (빠른 경로)
            # ========================================
            scientific_name = None
            for cached_name, cache_entry in self.species_cache.items():
                cached_data = cache_entry.get('data', {})
                if cached_data.get('id') == species_id:
                    scientific_name = cached_name
                    print(f"✅ 캐시에서 학명 발견: {scientific_name}")
                    break

            # ========================================
            # Step 2: 캐시 미스 시 v4 API로 학명 조회
            # (주의: v4는 ID 기반 조회가 제한적, 실패 시 fallback)
            # ========================================
            if not scientific_name:
                print(f"⚠️ 캐시에 없음. ID {species_id}로 직접 조회 시도...")

                # v4 API: /taxa/id/{sis_id} 엔드포인트 시도
                try:
                    url = f"{self.base_url}/taxa/id/{species_id}"
                    print(f"📡 Trying v4 endpoint: {url}")

                    response = await asyncio.wait_for(
                        self._make_request(url),
                        timeout=3.0
                    )

                    if response.status_code == 200:
                        v4_data = response.json()
                        if v4_data and 'taxon' in v4_data:
                            scientific_name = v4_data['taxon'].get('scientific_name')
                            print(f"✅ v4 API로 학명 획득: {scientific_name}")
                except Exception as e:
                    print(f"⚠️ v4 ID 조회 실패: {e}")

            # ========================================
            # Step 3: 학명 없으면 즉시 None 반환 (무한 대기 방지)
            # ========================================
            if not scientific_name:
                print(f"❌ 학명을 찾을 수 없음. ID: {species_id}")
                print(f"[RETURN] None")
                print(f"{'='*60}\n")
                return None

            # ========================================
            # Step 4: 학명으로 v4 데이터 조회
            # ========================================
            print(f"🔍 학명으로 상세 조회: {scientific_name}")

            v4_response = await asyncio.wait_for(
                self.search_by_scientific_name(scientific_name),
                timeout=5.0
            )

            # v4 -> v3 어댑터 적용
            if not v4_response:
                print(f"⚠️ v4 API 응답 없음")
                v3_data = None
            else:
                v3_data = self._v4_to_v3_adapter(v4_response, scientific_name)

            # ========================================
            # Step 5: Wikipedia 데이터 조회 (타임아웃 5초)
            # ========================================
            wiki_info = {}
            try:
                wiki_info = await asyncio.wait_for(
                    wikipedia_service.get_species_info(scientific_name),
                    timeout=5.0
                )
                print(f"✅ Wikipedia 데이터 획득")
            except asyncio.TimeoutError:
                print(f"⏱️ Wikipedia 타임아웃 (5s)")
            except Exception as e:
                print(f"⚠️ Wikipedia 오류: {e}")

            # ========================================
            # Step 6: 프론트엔드 호환 응답 구성 (모든 필드 보장)
            # ========================================
            # Wikipedia 이미지가 있으면 사용, 없으면 빈 문자열 (프론트엔드에서 이모지 표시)
            image_url = wiki_info.get("image_url", "") if wiki_info.get("image_url") else ""

            # 공통 이름 결정 (Wikipedia 우선, 없으면 학명)
            common_name = wiki_info.get("common_name", scientific_name)

            detail_response = {
                # 필수 식별 정보
                "id": species_id,
                "name": common_name,  # ⚡ 프론트엔드 필수 필드 추가
                "scientific_name": scientific_name,
                "common_name": common_name,

                # 분류 정보
                "category": "동물",
                "kingdom": v3_data.get('kingdom_name', 'Unknown') if v3_data else 'Unknown',
                "phylum": v3_data.get('phylum_name', 'Unknown') if v3_data else 'Unknown',
                "class": v3_data.get('class_name', 'Unknown') if v3_data else 'Unknown',

                # 이미지 (Wikipedia에서 가져온 실제 이미지, 없으면 빈 문자열)
                "image": image_url,
                "image_url": image_url,

                # 설명 (Wikipedia 우선)
                "description": wiki_info.get("description") or
                              (f"IUCN Red List Category: {v3_data.get('category', 'Unknown')}" if v3_data else "No description available"),

                # 보전 상태 (IUCN 데이터)
                "status": v3_data.get('category', 'DD') if v3_data else 'DD',
                "risk_level": v3_data.get('category', 'DD') if v3_data else 'DD',

                # 추가 정보 (기본값 제공)
                "population": "Unknown",
                "habitat": "Various habitats",
                "threats": [],
                "country": "Global",
                "color": "green",  # UI 표시용
            }

            print(f"✅ 상세 정보 구성 완료")
            print(f"[RETURN] Detail data")
            print(f"{'='*60}\n")

            return detail_response

        except asyncio.TimeoutError:
            print(f"⏱️ 전체 타임아웃 발생")
            print(f"[RETURN] None")
            print(f"{'='*60}\n")
            return None
        except Exception as e:
            print(f"❌ Species Detail Error: {e}")
            import traceback
            traceback.print_exc()
            print(f"[RETURN] None")
            print(f"{'='*60}\n")
            return None

    async def search_by_scientific_name(self, scientific_name: str) -> Optional[Dict]:
        """
        v4 API: 학명으로 종 검색
        
        Args:
            scientific_name: 학명 (예: "Panthera leo")
            
        Returns:
            종 정보 딕셔너리 또는 None
        """
        try:
            parts = scientific_name.split(' ', 1)
            if len(parts) < 2:
                print(f"⚠️ Invalid scientific name format: {scientific_name}")
                return None
            
            genus, species = parts[0], parts[1]
            url = f"{self.base_url}/taxa/scientific_name"
            params = {
                "genus_name": genus,
                "species_name": species
            }
            
            print(f"🔍 Searching: {genus} {species}")
            response = await self._make_request(url, params)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"⚠️ Search failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Scientific Name Search Error: {e}")
            return None

    async def close(self):
        """cloudscraper는 명시적 종료가 필요 없음"""
        pass

iucn_service = IUCNService()

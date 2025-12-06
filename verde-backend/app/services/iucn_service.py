from app.services.wikipedia_service import wikipedia_service
from app.services.translation_service import translation_service
import asyncio
import cloudscraper
import pycountry
from typing import List, Dict, Any, Optional
from app.core.config import settings
from datetime import datetime, timedelta
from functools import partial, lru_cache

try:
    import pycountry_convert as pc
except ImportError:
    pc = None

class IUCNService:
    TERRESTRIAL_VERTEBRATE_CLASSES = ['MAMMALIA', 'AVES', 'REPTILIA', 'AMPHIBIA']

    CATEGORY_TO_CLASSES = {
        "동물": ['MAMMALIA', 'AVES', 'REPTILIA', 'AMPHIBIA'],
        "식물": ['LILIOPSIDA', 'MAGNOLIOPSIDA', 'PINOPSIDA', 'POLYPODIOPSIDA', 'CYCADOPSIDA', 'GINKGOOPSIDA', 'GNETOPSIDA'],
        "곤충": ['INSECTA'],
        "해양생물": ['ACTINOPTERYGII', 'CHONDRICHTHYES', 'MALACOSTRACA', 'CEPHALOPODA', 'ANTHOZOA', 'MAMMALIA'],
    }

    MARINE_KEYWORDS = ['marine', 'ocean', 'sea', 'coral', 'whale', 'dolphin', 'shark', 'turtle', 'dugong', 'manatee']

    MAP_IMAGE_KEYWORDS = [
        'map', 'Map', 'MAP',
        'range', 'Range', 'RANGE',
        'distribution', 'Distribution',
        'habitat', 'Habitat',
        'area', 'Area',
        'location', 'Location',
        'spread', 'Spread',
        'geographic', 'Geographic',
        'territory', 'Territory',
        '_dis.', '_dis_',
        'LocationMap', 'location_map',
        'AreaMap', 'area_map',
        'RangeMap', 'range_map',
        'Locator', 'locator',
        'BlankMap', 'Blank_map',
        'svg',
    ]

    @staticmethod
    def is_valid_species_image(image_url: str) -> bool:
        if not image_url:
            return False

        url_lower = image_url.lower()

        for keyword in IUCNService.MAP_IMAGE_KEYWORDS:
            if keyword.lower() in url_lower:
                return False

        if url_lower.endswith('.svg'):
            return False

        map_patterns = [
            'in_europe', 'in_asia', 'in_africa', 'in_america',
            'in_australia', 'world_', 'globe_', 'earth_',
            'country_', 'region_', 'continent_',
        ]
        for pattern in map_patterns:
            if pattern in url_lower:
                return False

        return True

    ICONIC_ANIMALS = {
        'CN': ['Ailuropoda melanoleuca', 'Panthera tigris', 'Rhinopithecus roxellana', 'Ailurus fulgens'],
        'RU': ['Ursus maritimus', 'Panthera tigris', 'Ursus arctos', 'Canis lupus'],
        'JP': ['Macaca fuscata', 'Naemorhedus crispus', 'Ursus thibetanus'],
        'KR': ['Ursus thibetanus', 'Panthera pardus', 'Naemorhedus caudatus', 'Neophocaena asiaeorientalis'],
        'US': ['Ursus americanus', 'Bison bison', 'Puma concolor', 'Ursus arctos'],
        'CA': ['Ursus maritimus', 'Alces alces', 'Castor canadensis', 'Ursus arctos'],
        'AU': ['Phascolarctos cinereus', 'Macropus rufus', 'Ornithorhynchus anatinus', 'Vombatus ursinus'],
        'BR': ['Panthera onca', 'Tapirus terrestris', 'Myrmecophaga tridactyla', 'Bradypus variegatus'],
        'IN': ['Panthera tigris', 'Elephas maximus', 'Rhinoceros unicornis', 'Panthera leo'],
        'KE': ['Loxodonta africana', 'Panthera leo', 'Giraffa camelopardalis', 'Diceros bicornis'],
        'ZA': ['Loxodonta africana', 'Panthera leo', 'Ceratotherium simum', 'Diceros bicornis'],
        'DE': ['Lynx lynx', 'Canis lupus', 'Sus scrofa', 'Cervus elaphus'],
        'GB': ['Cervus elaphus', 'Meles meles', 'Vulpes vulpes', 'Lutra lutra'],
        'FR': ['Ursus arctos', 'Lynx lynx', 'Canis lupus', 'Cervus elaphus'],
        'MX': ['Panthera onca', 'Puma concolor', 'Tapirus bairdii', 'Ursus americanus'],
        'ID': ['Pongo pygmaeus', 'Panthera tigris', 'Rhinoceros sondaicus', 'Elephas maximus'],
        'NZ': ['Apteryx mantelli', 'Apteryx australis'],
    }

    def __init__(self):
        self.base_url = "https://api.iucnredlist.org/api/v4"
        self.token = settings.IUCN_API_KEY
        self.scraper = cloudscraper.create_scraper()
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json"
        }
        self.country_cache: Dict[str, Dict[str, Any]] = {}
        self.species_cache: Dict[str, Dict[str, Any]] = {}
        self.id_to_species_cache: Dict[int, Dict[str, Any]] = {}
        self.cache_ttl = timedelta(hours=1)
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
        # 6. 모든 방법 실패 시 None 반환
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
            return continent
        return None

    # 해양포유류 목(Order) - 고래, 돌고래, 물개 등
    # 참고: IUCN API는 고래를 ARTIODACTYLA(우제류)로 분류하므로 family_name으로 판별해야 함
    MARINE_MAMMAL_ORDERS = ['CETACEA', 'SIRENIA', 'CARNIVORA']  # 고래목, 해우목 (레거시 호환)

    # 해양포유류 과(Family) - 고래, 돌고래, 해우, 물개 등
    MARINE_MAMMAL_FAMILIES = [
        # 고래류 (Cetaceans) - 수염고래, 이빨고래
        'BALAENIDAE',       # 참고래과 (Right whales)
        'BALAENOPTERIDAE',  # 수염고래과 (Rorquals: 밍크고래, 대왕고래, 혹등고래 등)
        'ESCHRICHTIIDAE',   # 귀신고래과 (Gray whales)
        'NEOBALAENIDAE',    # 피그미참고래과 (Pygmy right whales)
        'DELPHINIDAE',      # 돌고래과 (Dolphins, 범고래 포함)
        'MONODONTIDAE',     # 일각고래과 (Narwhals, Belugas)
        'PHOCOENIDAE',      # 쇠돌고래과 (Porpoises)
        'PHYSETERIDAE',     # 향고래과 (Sperm whales)
        'KOGIIDAE',         # 꼬마향고래과 (Dwarf/Pygmy sperm whales)
        'ZIPHIIDAE',        # 부리고래과 (Beaked whales)
        'PLATANISTIDAE',    # 강돌고래과 (River dolphins)
        'INIIDAE',          # 아마존강돌고래과
        'PONTOPORIIDAE',    # 라플라타돌고래과
        'LIPOTIDAE',        # 양쯔강돌고래과
        # 해우류 (Sirenians)
        'TRICHECHIDAE',     # 매너티과 (Manatees)
        'DUGONGIDAE',       # 듀공과 (Dugongs)
        # 기각류 (Pinnipeds) - 물개, 바다표범, 바다코끼리
        'OTARIIDAE',        # 물개과 (Eared seals, sea lions)
        'PHOCIDAE',         # 바다표범과 (True seals)
        'ODOBENIDAE',       # 바다코끼리과 (Walruses)
    ]

    # CARNIVORA 중 해양 과(Family) - 레거시 호환용
    MARINE_CARNIVORA_FAMILIES = ['OTARIIDAE', 'PHOCIDAE', 'ODOBENIDAE']  # 물개, 바다표범, 바다코끼리

    def _determine_category(self, assessment: Dict[str, Any]) -> str:
        """
        IUCN assessment 데이터에서 카테고리(동물/식물/곤충/해양생물)를 판별합니다.

        ⚠️ 주의: IUCN API v4 /countries/{code} 엔드포인트는 class_name, kingdom_name을
        포함하지 않습니다. 따라서 해당 필드가 없으면 기본값 "동물"을 반환합니다.

        Args:
            assessment: IUCN API v4 assessment 데이터

        Returns:
            카테고리 문자열 (동물, 식물, 곤충, 해양생물)
        """
        # v4 country endpoint에서는 class_name/kingdom_name이 없을 수 있음
        class_name = assessment.get('class_name', '').upper()
        kingdom_name = assessment.get('kingdom_name', '').upper()
        order_name = assessment.get('order_name', '').upper()
        family_name = assessment.get('family_name', '').upper()
        systems = assessment.get('systems', [])

        # systems가 없는 경우 빈 리스트로 처리
        if not isinstance(systems, list):
            systems = []

        # 해양생물 체크 (시스템에 'Marine' 포함)
        if any('marine' in str(s).lower() for s in systems if s):
            return "해양생물"

        # 왕국 기반 분류
        if kingdom_name == 'PLANTAE':
            return "식물"

        # 해양포유류 체크 (고래목, 해우목, 기각류)
        if class_name == 'MAMMALIA':
            # 고래목(CETACEA)과 해우목(SIRENIA)은 해양생물
            if order_name in ['CETACEA', 'SIRENIA']:
                return "해양생물"
            # 식육목(CARNIVORA) 중 해양 과는 해양생물 (물개, 바다표범 등)
            if order_name == 'CARNIVORA' and family_name in self.MARINE_CARNIVORA_FAMILIES:
                return "해양생물"

        # 클래스 기반 분류
        if class_name == 'INSECTA':
            return "곤충"
        elif class_name in ['ACTINOPTERYGII', 'CHONDRICHTHYES', 'CEPHALOPODA', 'MALACOSTRACA']:
            return "해양생물"
        elif class_name in self.TERRESTRIAL_VERTEBRATE_CLASSES:
            return "동물"

        # ⚠️ v4 /countries/{code}에서 class_name이 없는 경우:
        # 기본값으로 "동물" 반환 (프론트엔드에서 카테고리 필터 선택에 의존)
        return "동물"

    async def _fetch_country_assessments(self, country_code: str, page: int = 1) -> Dict[str, Any]:
        """
        IUCN API v4 /countries/{code} 엔드포인트로 국가별 종 목록을 가져옵니다.

        Args:
            country_code: ISO Alpha-2 국가 코드
            page: 페이지 번호 (기본값: 1)

        Returns:
            API 응답 딕셔너리 (assessments 배열 포함)
        """
        url = f"{self.base_url}/countries/{country_code}"
        params = {
            "page": page,
            "latest": "true"  # 최신 평가만
        }

        try:
            response = await self._make_request(url, params)
            if response.status_code == 200:
                return response.json()
            else:
                return {"assessments": []}
        except Exception as e:
            return {"assessments": []}

    async def get_species_count_fast(self, country_code: str) -> int:
        """
        국가별 멸종위기 점수를 빠르게 계산합니다 (Wikipedia 호출 없음).

        ⚡ 지도 시각화용 최적화:
        - 1페이지만 조회하여 빠른 응답 (100종 샘플)
        - 위험 등급별 가중치 점수 계산으로 국가별 다양성 확보
          - CR (Critically Endangered): 5점
          - EN (Endangered): 3점
          - VU (Vulnerable): 2점
          - NT (Near Threatened): 1점
          - LC/DD 등: 0점
        - 캐시 활용으로 반복 호출 시 즉시 응답

        Args:
            country_code: ISO Alpha-2 국가 코드

        Returns:
            해당 국가의 멸종위기 가중 점수 (0~500)
        """
        # 위험 등급별 가중치
        RISK_WEIGHTS = {
            'CR': 5,  # Critically Endangered
            'EN': 3,  # Endangered
            'VU': 2,  # Vulnerable
            'NT': 1,  # Near Threatened
            'LC': 0,  # Least Concern
            'DD': 0,  # Data Deficient
            'NE': 0,  # Not Evaluated
        }

        try:
            # 국가 코드 정규화
            normalized_code = self._normalize_country_code(country_code)
            if not normalized_code:
                return 0

            # 캐시 확인 (score 전용)
            cache_key = f"score_{normalized_code}"
            if cache_key in self.country_cache:
                cache_entry = self.country_cache[cache_key]
                cache_time = cache_entry.get('timestamp')
                if cache_time and datetime.now() - cache_time < self.cache_ttl:
                    return cache_entry.get('data', 0)

            # IUCN API 1페이지만 조회 (빠른 응답)
            url = f"{self.base_url}/countries/{normalized_code}"
            params = {"page": 1, "latest": "true"}

            response = await self._make_request(url, params)

            if response.status_code != 200:
                return 0

            data = response.json()
            assessments = data.get('assessments', [])

            # 위험 등급별 가중 점수 계산
            score = 0
            for assessment in assessments:
                # v4 API: red_list_category_code 필드 사용
                category_code = assessment.get('red_list_category_code', 'DD')
                weight = RISK_WEIGHTS.get(category_code, 0)
                score += weight

            # 캐시 저장
            self.country_cache[cache_key] = {
                'data': score,
                'timestamp': datetime.now()
            }

            return score

        except Exception as e:
            return 0

    async def get_species_count_by_category(self, country_code: str, category: str) -> int:
        """
        국가별, 카테고리별 종 개수를 조회합니다.

        ⚡ 지도 시각화용 최적화:
        - taxon API를 사용하여 class_name 조회
        - 카테고리별 필터링 후 종 개수 반환
        - 캐시 활용으로 빠른 응답

        Args:
            country_code: ISO Alpha-2 국가 코드
            category: 카테고리 (동물, 식물, 곤충, 해양생물)

        Returns:
            해당 국가/카테고리의 종 개수
        """
        try:
            # 국가 코드 정규화
            normalized_code = self._normalize_country_code(country_code)
            if not normalized_code:
                return 0

            # 캐시 확인
            cache_key = f"count_{normalized_code}_{category}"
            if cache_key in self.country_cache:
                cache_entry = self.country_cache[cache_key]
                cache_time = cache_entry.get('timestamp')
                if cache_time and datetime.now() - cache_time < self.cache_ttl:
                    return cache_entry.get('data', 0)

            # IUCN API 3페이지 조회 (300종 샘플)
            all_assessments = []
            for page in range(1, 4):
                url = f"{self.base_url}/countries/{normalized_code}"
                params = {"page": page, "latest": "true"}
                response = await self._make_request(url, params)

                if response.status_code != 200:
                    break

                data = response.json()
                assessments = data.get('assessments', [])
                if not assessments:
                    break
                all_assessments.extend(assessments)
                if len(assessments) < 100:
                    break

            if not all_assessments:
                return 0

            # 카테고리별 필터링 (taxon 정보 조회)
            count = 0

            # 병렬 처리를 위한 함수
            async def check_category(assessment: Dict[str, Any]) -> bool:
                """종의 카테고리 확인"""
                scientific_name = assessment.get('taxon_scientific_name', '')
                if not scientific_name:
                    return False

                # 캐시된 taxon 정보 확인
                species_cache_key = f"taxon_{scientific_name}"
                taxon_info = None

                if species_cache_key in self.species_cache:
                    cache_entry = self.species_cache[species_cache_key]
                    if cache_entry.get('timestamp') and datetime.now() - cache_entry['timestamp'] < self.cache_ttl:
                        taxon_info = cache_entry.get('data')

                # 캐시 미스 시 taxon API 호출
                if not taxon_info:
                    taxon_info = await self._fetch_taxon_info(scientific_name)
                    if taxon_info:
                        self.species_cache[species_cache_key] = {
                            'data': taxon_info,
                            'timestamp': datetime.now()
                        }

                if not taxon_info:
                    # taxon 정보 없으면 기본값 "동물"로 처리
                    return category == "동물"

                # 카테고리 판별
                class_name = taxon_info.get('class_name', '').upper()
                kingdom_name = taxon_info.get('kingdom_name', '').upper()

                detected_category = "동물"  # 기본값

                if kingdom_name == 'PLANTAE':
                    detected_category = "식물"
                elif class_name == 'INSECTA':
                    detected_category = "곤충"
                elif class_name in ['ACTINOPTERYGII', 'CHONDRICHTHYES', 'CEPHALOPODA',
                                   'MALACOSTRACA', 'ANTHOZOA', 'BIVALVIA', 'GASTROPODA']:
                    detected_category = "해양생물"
                elif class_name in ['MAMMALIA', 'AVES', 'REPTILIA', 'AMPHIBIA']:
                    detected_category = "동물"
                elif kingdom_name == 'ANIMALIA':
                    detected_category = "동물"

                return detected_category == category

            # 최대 50개만 샘플링하여 카테고리 확인 (성능 고려)
            sample_size = min(50, len(all_assessments))
            sample_assessments = all_assessments[:sample_size]

            tasks = [check_category(a) for a in sample_assessments]
            try:
                results = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=30.0
                )
                count = sum(1 for r in results if r is True)
            except asyncio.TimeoutError:
                count = 0

            # 전체 종 대비 비율로 추정 (샘플링 보정)
            if sample_size < len(all_assessments) and count > 0:
                ratio = count / sample_size
                estimated_count = int(len(all_assessments) * ratio)
                count = estimated_count

            # 캐시 저장
            self.country_cache[cache_key] = {
                'data': count,
                'timestamp': datetime.now()
            }

            return count

        except Exception as e:
            return 0

    async def _fetch_taxon_info(self, scientific_name: str) -> Optional[Dict[str, Any]]:
        """
        학명으로 taxon 상세 정보를 조회합니다.
        class_name, kingdom_name 등 분류 정보를 얻기 위해 사용합니다.

        Args:
            scientific_name: 학명 (예: "Panthera tigris")

        Returns:
            taxon 정보 딕셔너리 또는 None
        """
        try:
            parts = scientific_name.split(' ', 1)
            if len(parts) < 2:
                return None

            genus, species = parts[0], parts[1].split()[0] if ' ' in parts[1] else parts[1]
            url = f"{self.base_url}/taxa/scientific_name"
            params = {"genus_name": genus, "species_name": species}

            response = await self._make_request(url, params)

            if response.status_code == 200:
                data = response.json()
                return data.get('taxon')
            return None
        except Exception as e:
            return None

    async def _fetch_iconic_animals(self, country_code: str) -> List[Dict[str, Any]]:
        """
        국가별 대표 동물(판다, 호랑이, 북극곰 등)을 IUCN taxon API로 조회합니다.
        IUCN /countries/{code} 엔드포인트에서 누락되는 유명 포유류를 보완합니다.

        Args:
            country_code: ISO Alpha-2 국가 코드

        Returns:
            대표 동물 데이터 리스트
        """
        iconic_names = self.ICONIC_ANIMALS.get(country_code.upper(), [])
        if not iconic_names:
            return []
        iconic_species = []

        async def fetch_one_iconic(scientific_name: str) -> Optional[Dict[str, Any]]:
            """단일 대표 동물 데이터 조회"""
            try:
                # 캐시 확인
                cache_key = f"iconic_{scientific_name}"
                if cache_key in self.species_cache:
                    cache_entry = self.species_cache[cache_key]
                    if cache_entry.get('timestamp') and datetime.now() - cache_entry['timestamp'] < self.cache_ttl:
                        return cache_entry.get('data')

                # taxon 정보 조회
                taxon_info = await self._fetch_taxon_info(scientific_name)
                if not taxon_info:
                    return None

                sis_id = taxon_info.get('sis_id')
                class_name = (taxon_info.get('class_name') or '').upper()

                # 동물(척추동물)인지 확인
                if class_name not in ['MAMMALIA', 'AVES', 'REPTILIA', 'AMPHIBIA']:
                    return None

                # Wikipedia 데이터 조회 (2초 타임아웃)
                wiki_info = {}
                try:
                    wiki_info = await asyncio.wait_for(
                        wikipedia_service.get_species_info(scientific_name),
                        timeout=2.0
                    )
                except (asyncio.TimeoutError, Exception):
                    pass

                # 공통 이름 결정
                common_name = wiki_info.get("common_name")
                if not common_name:
                    common_names = taxon_info.get('common_names', [])
                    if common_names:
                        common_name = common_names[0].get('name')
                if not common_name:
                    common_name = scientific_name

                # 이미지 URL (이미지 없거나 지도 이미지면 필터링)
                image_url = wiki_info.get("image_url", "")
                if not self.is_valid_species_image(image_url):
                    return None  # 이미지 없거나 지도 이미지인 대표 동물 필터링

                # IUCN 위험 등급 조회 (assessment 엔드포인트)
                risk_level = "DD"
                if sis_id:
                    try:
                        assess_url = f"{self.base_url}/taxa/sis/{sis_id}/assessments"
                        assess_resp = await self._make_request(assess_url, {"latest": "true"})
                        if assess_resp.status_code == 200:
                            assess_data = assess_resp.json()
                            assessments = assess_data.get('assessments', [])
                            if assessments:
                                risk_level = assessments[0].get('red_list_category_code', 'DD')
                    except Exception:
                        pass

                species_data = {
                    "id": sis_id,
                    "scientific_name": scientific_name,
                    "common_name": common_name,
                    "name": common_name,
                    "category": "동물",
                    "image": image_url,
                    "image_url": image_url,
                    "description": wiki_info.get("description", f"{common_name} - IUCN {risk_level}"),
                    "country": country_code.upper(),
                    "risk_level": risk_level,
                    "is_iconic": True  # 대표 동물 표시
                }

                # 캐시에 저장
                self.species_cache[cache_key] = {
                    'data': species_data,
                    'timestamp': datetime.now()
                }

                # ID 캐시에도 저장
                if sis_id:
                    self.id_to_species_cache[sis_id] = {
                        'data': species_data,
                        'timestamp': datetime.now()
                    }
                return species_data

            except Exception as e:
                return None

        # 병렬로 대표 동물 조회 (세마포어로 제한)
        semaphore = asyncio.Semaphore(5)

        async def limited_fetch(name):
            async with semaphore:
                return await fetch_one_iconic(name)

        tasks = [limited_fetch(name) for name in iconic_names]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if result and not isinstance(result, Exception):
                iconic_species.append(result)
        return iconic_species

    async def get_species_by_country(self, country_code: str, category: str = None, species_name: str = None) -> List[Dict[str, Any]]:
        """
        IUCN API v4를 사용하여 국가별 멸종위기종을 동적으로 조회합니다.

        🌍 동적 데이터 조회:
        - 모든 국가 지원 (하드코딩 없음)
        - IUCN API v4 /countries/{code} 엔드포인트 사용
        - taxon API로 class_name 조회하여 카테고리별 필터링 (동물, 식물, 곤충, 해양생물)
        - Wikipedia 데이터로 이미지/설명 보강

        Args:
            country_code: 국가 코드 (ISO Alpha-2)
            category: 카테고리 필터 (동물, 식물, 곤충, 해양생물) - None이면 모든 카테고리
            species_name: 종 이름 필터 (검색 모드일 때 해당 종만 반환)

        Returns:
            종 데이터 리스트
        """
        try:
            original_input = country_code
            # 1. 국가 코드 정규화
            country_code = self._normalize_country_code(country_code)
            if not country_code:
                return []

            # 2. 캐시 확인 (카테고리별 캐시)
            cache_key = f"species_{country_code}_{category or 'all'}"
            if cache_key in self.country_cache:
                cache_entry = self.country_cache[cache_key]
                cache_time = cache_entry.get('timestamp')
                if cache_time and datetime.now() - cache_time < self.cache_ttl:
                    cached_data = cache_entry.get('data', [])
                    return cached_data

            # 3. IUCN API v4 /countries/{code} 호출 (10페이지, 1000종 - 다양한 클래스 포함)
            all_assessments = []
            for page in range(1, 11):  # 10페이지까지 (1000종) - 더 다양한 클래스 포함
                response_data = await self._fetch_country_assessments(country_code, page)
                assessments = response_data.get('assessments', [])
                if not assessments:
                    break
                all_assessments.extend(assessments)
                if len(assessments) < 100:
                    break

            if not all_assessments:
                return []
            # 4. taxon 정보 조회 + 카테고리 필터링 + Wikipedia 보강 (병렬 처리)
            async def enrich_and_filter(assessment: Dict[str, Any]) -> Optional[Dict[str, Any]]:
                """종 데이터 보강 및 카테고리 필터링"""
                try:
                    scientific_name = assessment.get('taxon_scientific_name', '')
                    sis_id = assessment.get('sis_taxon_id')
                    risk_level = assessment.get('red_list_category_code', 'DD')

                    if not scientific_name:
                        return None

                    # 종 캐시 확인
                    species_cache_key = f"taxon_{scientific_name}"
                    cached_taxon = None
                    if species_cache_key in self.species_cache:
                        cache_entry = self.species_cache[species_cache_key]
                        if cache_entry.get('timestamp') and datetime.now() - cache_entry['timestamp'] < self.cache_ttl:
                            cached_taxon = cache_entry.get('data')

                    # taxon 정보 조회 (캐시 미스 시)
                    taxon_info = cached_taxon
                    if not taxon_info:
                        taxon_info = await self._fetch_taxon_info(scientific_name)
                        if taxon_info:
                            self.species_cache[species_cache_key] = {
                                'data': taxon_info,
                                'timestamp': datetime.now()
                            }

                    # 카테고리 판별 (taxon_info 필수)
                    # taxon_info가 없으면 정확한 분류가 불가능하므로 제외
                    if not taxon_info:
                        return None  # taxon 정보 없음 - 제외

                    class_name = taxon_info.get('class_name', '').upper()
                    kingdom_name = taxon_info.get('kingdom_name', '').upper()
                    order_name = taxon_info.get('order_name', '').upper()
                    family_name = taxon_info.get('family_name', '').upper()

                    # class_name 또는 kingdom_name이 없으면 분류 불가
                    if not class_name and not kingdom_name:
                        return None  # 분류 정보 없음 - 제외

                    detected_category = None  # 기본값 없음 (명확한 분류 필요)

                    # 카테고리 결정 (명확한 순서로)
                    if kingdom_name == 'PLANTAE':
                        detected_category = "식물"
                    elif class_name == 'INSECTA' or class_name == 'ARACHNIDA':
                        detected_category = "곤충"
                    elif class_name in ['ACTINOPTERYGII', 'CHONDRICHTHYES', 'CEPHALOPODA',
                                       'MALACOSTRACA', 'ANTHOZOA', 'BIVALVIA', 'GASTROPODA',
                                       'HOLOTHUROIDEA', 'ECHINOIDEA', 'ASTEROIDEA', 'OPHIUROIDEA',
                                       'HYDROZOA', 'SCYPHOZOA', 'POLYCHAETA']:
                        # 해양 무척추동물 및 어류 (해삼, 성게, 불가사리, 조개, 산호, 해파리 등)
                        detected_category = "해양생물"
                    elif class_name == 'MAMMALIA':
                        # 해양포유류 체크 - family_name 기준 (IUCN API는 고래를 ARTIODACTYLA로 분류함)
                        if family_name in self.MARINE_MAMMAL_FAMILIES:
                            # 고래과, 돌고래과, 물개과, 바다표범과, 해우과 등은 해양생물
                            detected_category = "해양생물"
                        elif order_name in ['CETACEA', 'SIRENIA']:
                            # 레거시 호환: order_name으로도 체크 (혹시 family가 없을 경우)
                            detected_category = "해양생물"
                        else:
                            # 기타 포유류는 육상 동물
                            detected_category = "동물"
                    elif class_name in ['AVES', 'REPTILIA', 'AMPHIBIA']:
                        # 육상 척추동물만 "동물" 카테고리
                        detected_category = "동물"
                    elif kingdom_name == 'ANIMALIA':
                        # 기타 ANIMALIA는 class_name으로 더 정확히 분류
                        # 알 수 없는 class는 제외 (잘못된 분류 방지)
                        return None

                    # 카테고리를 결정하지 못한 경우 제외
                    if detected_category is None:
                        return None  # 분류 불가 - 제외

                    # 카테고리 필터링
                    if category and detected_category != category:
                        return None  # 카테고리 불일치 - 제외

                    # Wikipedia 데이터 조회
                    wiki_info = {}
                    try:
                        wiki_info = await asyncio.wait_for(
                            wikipedia_service.get_species_info(scientific_name),
                            timeout=3.0
                        )
                    except (asyncio.TimeoutError, Exception):
                        pass

                    # 공통 이름 결정
                    common_name = wiki_info.get("common_name")
                    if not common_name and taxon_info:
                        common_names = taxon_info.get('common_names', [])
                        if common_names:
                            common_name = common_names[0].get('name')
                    if not common_name:
                        common_name = scientific_name

                    # 이미지 URL 확인 (Wikipedia 이미지만 사용)
                    # 이미지가 없거나 지도 이미지인 종은 필터링하여 제외
                    image_url = wiki_info.get("image_url", "")

                    # 이미지가 없거나 지도 이미지면 결과에서 제외
                    if not self.is_valid_species_image(image_url):
                        return None  # 유효한 이미지 없는 종은 필터링

                    species_data = {
                        "id": sis_id,
                        "scientific_name": scientific_name,
                        "common_name": common_name,
                        "name": common_name,  # 프론트엔드 호환
                        "category": detected_category,
                        "image": image_url,
                        "image_url": image_url,
                        "description": wiki_info.get("description", f"{common_name} - IUCN {risk_level}"),
                        "country": country_code,
                        "risk_level": risk_level
                    }

                    # ID 캐시에 저장 (상세 조회용)
                    if sis_id:
                        self.id_to_species_cache[sis_id] = {
                            'data': species_data,
                            'timestamp': datetime.now()
                        }

                    return species_data

                except Exception as e:
                    return None

            # === 개선된 샘플링 전략 ===
            # IUCN API 데이터의 약 10%만 육상 척추동물(동물 카테고리)이므로
            # 충분한 결과를 얻으려면 많은 샘플이 필요함
            # 알파벳 범위별로 다양하게 선택하여 MAMMALIA(L~Z), AVES(A~Z) 등 다양한 클래스 포함
            total_species = len(all_assessments)

            if total_species <= 200:
                sample_assessments = all_assessments
            else:
                sample_assessments = []

                # 전략: 알파벳 범위별 균등 샘플링 (더 많은 샘플)
                # 포유류는 주로 L, M, P, R, S 등에 집중되어 있음
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

                # 동물 카테고리가 약 10%이므로 300개 샘플링하면 약 30개 동물 확보
                samples_per_range = 40  # 각 범위에서 40개씩 = 320개

                for start_pct, end_pct in alphabet_ranges:
                    start_idx = int(total_species * start_pct)
                    end_idx = int(total_species * end_pct)
                    range_size = end_idx - start_idx

                    if range_size > 0:
                        # 해당 범위에서 균등 샘플링
                        step = max(1, range_size // samples_per_range)
                        for i in range(0, min(range_size, samples_per_range * step), step):
                            if start_idx + i < len(all_assessments):
                                sample_assessments.append(all_assessments[start_idx + i])

                # 중복 제거
                seen = set()
                unique_samples = []
                for a in sample_assessments:
                    key = a.get('sis_taxon_id')
                    if key not in seen:
                        seen.add(key)
                        unique_samples.append(a)
                sample_assessments = unique_samples[:350]  # 최대 350개 샘플링
            # 세마포어로 동시 요청 제한 (API 부하 방지)
            semaphore = asyncio.Semaphore(20)  # 더 많은 병렬 요청 허용

            async def limited_enrich(assessment):
                async with semaphore:
                    return await enrich_and_filter(assessment)

            tasks = [limited_enrich(a) for a in sample_assessments]
            try:
                results = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=120.0  # 350개 처리를 위해 타임아웃 증가
                )
            except asyncio.TimeoutError:
                results = []

            # 디버깅: 결과 통계
            none_count = sum(1 for r in results if r is None)
            exception_count = sum(1 for r in results if isinstance(r, Exception))
            success_count = sum(1 for r in results if r is not None and not isinstance(r, Exception))
            # 성공한 결과만 필터링 (카테고리 일치 + 데이터 있음)
            species_data = [r for r in results if r is not None and not isinstance(r, Exception)]

            # 중복 제거 (학명 + 이미지 URL 기준)
            seen_names = set()
            seen_images = set()
            unique_species = []
            for species in species_data:
                name = species.get('scientific_name')
                image_url = species.get('image', '')

                # 학명 중복 제거
                if name and name in seen_names:
                    continue

                # 이미지 중복 제거 (같은 이미지가 다른 종에 사용된 경우)
                if image_url and image_url in seen_images:
                    continue

                if name:
                    seen_names.add(name)
                if image_url:
                    seen_images.add(image_url)
                unique_species.append(species)
            # ========================================
            # 대표 동물 병합 (동물 카테고리 전용)
            # IUCN /countries/{code} 엔드포인트에서 누락되는
            # 유명 포유류(판다, 호랑이, 북극곰 등)를 추가
            # ========================================
            if category == "동물" or category is None:
                iconic_animals = await self._fetch_iconic_animals(country_code)

                # 대표 동물을 맨 앞에 추가 (학명 + 이미지 중복 제외)
                iconic_added = 0
                for iconic in iconic_animals:
                    iconic_name = iconic.get('scientific_name')
                    iconic_image = iconic.get('image', '')

                    # 학명 또는 이미지가 이미 존재하면 스킵
                    if iconic_name and iconic_name in seen_names:
                        continue
                    if iconic_image and iconic_image in seen_images:
                        continue

                    if iconic_name:
                        seen_names.add(iconic_name)
                    if iconic_image:
                        seen_images.add(iconic_image)
                    # 대표 동물은 맨 앞에 배치
                    unique_species.insert(iconic_added, iconic)
                    iconic_added += 1

                if iconic_added > 0:
            # 캐시 저장 (species_name 필터 없을 때만)
            if not species_name:
                self.country_cache[cache_key] = {
                    'data': unique_species,
                    'timestamp': datetime.now()
                }

            # ========================================
            # species_name 필터링 (검색 모드일 때)
            # ========================================
            if species_name:
                species_name_lower = species_name.lower()
                # scientific_name 또는 common_name에 검색어가 포함된 종만 필터링
                filtered_species = [
                    sp for sp in unique_species
                    if (sp.get('scientific_name', '').lower().find(species_name_lower) >= 0 or
                        sp.get('common_name', '').lower().find(species_name_lower) >= 0 or
                        sp.get('name', '').lower().find(species_name_lower) >= 0)
                ]
                # ========================================
                # 폴백: 필터링 결과가 0개일 때 직접 taxon API 조회
                # ========================================
                if len(filtered_species) == 0 and ' ' in species_name:
                    try:
                        # taxon 정보 조회
                        taxon_info = await self._fetch_taxon_info(species_name)
                        if taxon_info:
                            sis_id = taxon_info.get('sis_id')
                            scientific_name_from_api = taxon_info.get('scientific_name', species_name)
                            class_name = (taxon_info.get('class_name') or '').upper()

                            # Wikipedia 데이터 조회 (2초 타임아웃)
                            wiki_info = {}
                            try:
                                wiki_info = await asyncio.wait_for(
                                    wikipedia_service.get_species_info(scientific_name_from_api),
                                    timeout=2.0
                                )
                            except (asyncio.TimeoutError, Exception) as e:
                            # 공통 이름 결정
                            common_name = wiki_info.get("common_name")
                            if not common_name:
                                common_names = taxon_info.get('common_names', [])
                                if common_names:
                                    common_name = common_names[0].get('name')
                            if not common_name:
                                common_name = scientific_name_from_api

                            # 이미지 URL
                            image_url = wiki_info.get("image_url", "")

                            # IUCN 위험 등급 조회
                            risk_level = "DD"
                            if sis_id:
                                try:
                                    assess_url = f"{self.base_url}/taxa/sis/{sis_id}/assessments"
                                    assess_resp = await self._make_request(assess_url, {"latest": "true"})
                                    if assess_resp.status_code == 200:
                                        assess_data = assess_resp.json()
                                        assessments = assess_data.get('assessments', [])
                                        if assessments:
                                            risk_level = assessments[0].get('red_list_category_code', 'DD')
                                except Exception:
                                    pass

                            # 카테고리 결정
                            fallback_category = category or "동물"
                            if class_name in ['MAMMALIA', 'AVES', 'REPTILIA', 'AMPHIBIA']:
                                fallback_category = "동물"
                            elif class_name == 'INSECTA':
                                fallback_category = "곤충"
                            elif class_name in ['ACTINOPTERYGII', 'CHONDRICHTHYES']:
                                fallback_category = "해양생물"
                            elif class_name in ['MAGNOLIOPSIDA', 'LILIOPSIDA', 'PINOPSIDA']:
                                fallback_category = "식물"

                            fallback_species = {
                                "id": sis_id,
                                "scientific_name": scientific_name_from_api,
                                "common_name": common_name,
                                "name": common_name,
                                "category": fallback_category,
                                "image": image_url,
                                "image_url": image_url,
                                "description": wiki_info.get("description", f"{common_name} - IUCN {risk_level}"),
                                "country": country_code.upper(),
                                "risk_level": risk_level,
                                "is_searched": True  # 검색으로 조회된 종 표시
                            }

                            filtered_species = [fallback_species]
                        else:
                    except Exception as e:
                unique_species = filtered_species

            # ========================================
            # [LOG 5/5 - Return] 최종 반환 데이터
            # ========================================
            if unique_species:
            return unique_species

        except Exception as e:
            import traceback
            traceback.print_exc()
            return []

    async def get_species_detail(self, species_id: int, lang: str = "en", scientific_name_hint: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        특정 종의 상세 정보를 IUCN v4 API와 Wikipedia에서 조회합니다.

        ⚡ v4 API Redesign:
        - v4에는 ID 기반 직접 조회가 제한적이므로 캐시 또는 학명 기반 재조회 사용
        - Wikipedia 통합 (2초 타임아웃)
        - 프론트엔드 호환 완벽 보장
        - 다국어 지원: 요청된 언어의 Wikipedia에서 정보 조회
        - scientific_name_hint: 학명을 미리 알고 있을 경우 직접 전달 (캐시 미스 시 사용)

        Args:
            species_id: IUCN sis_id (v4 기준)
            lang: 언어 코드 (ko=한국어, en=영어, ja=일본어, zh=중국어 등)
            scientific_name_hint: 학명 힌트 (선택, 캐시 미스 시 이 값을 사용)

        Returns:
            종 상세 정보 딕셔너리 (모든 필드 보장) 또는 None
        """
        try:
            # ========================================
            # Step 0: ID 캐시에서 먼저 확인 (가장 빠른 경로)
            # ========================================
            if species_id in self.id_to_species_cache:
                cache_entry = self.id_to_species_cache[species_id]
                cache_time = cache_entry.get('timestamp')
                if cache_time and datetime.now() - cache_time < self.cache_ttl:
                    cached_species_data = cache_entry.get('data', {})
                    scientific_name = cached_species_data.get('scientific_name')
                    # Wikipedia 데이터 조회 (항상 영어로 가져옴 - 가장 완전한 정보)
                    wiki_info = {}
                    try:
                        wiki_info = await asyncio.wait_for(
                            wikipedia_service.get_species_info(scientific_name, lang="en"),
                            timeout=2.0
                        )
                    except (asyncio.TimeoutError, Exception) as e:
                    # 캐시된 데이터를 기반으로 상세 정보 구성
                    image_url = wiki_info.get("image_url") or cached_species_data.get("image_url", "")
                    common_name = wiki_info.get("common_name") or cached_species_data.get("common_name", scientific_name)
                    description = wiki_info.get("description") or cached_species_data.get("description", "No description available")

                    detail_response = {
                        "id": species_id,
                        "name": common_name,
                        "scientific_name": scientific_name,
                        "common_name": common_name,
                        "category": cached_species_data.get("category", "동물"),
                        "kingdom": "Animalia",
                        "phylum": "Chordata",
                        "class": "Unknown",
                        "image": image_url,
                        "image_url": image_url,
                        "description": description,
                        "status": cached_species_data.get("risk_level", "DD"),
                        "risk_level": cached_species_data.get("risk_level", "DD"),
                        "population": "Unknown",
                        "habitat": "Various habitats",
                        "threats": [],
                        "country": cached_species_data.get("country", "Global"),
                        "color": "green",
                        "lang": "en",
                    }

                    # AI 번역 적용 (영어가 아닌 경우)
                    if lang != "en":
                        try:
                            detail_response = await translation_service.translate_species_info(
                                detail_response, target_lang=lang
                            )
                        except Exception as e:
                    return detail_response

            # ========================================
            # Step 1: taxon 캐시에서 학명 찾기 (느린 경로)
            # species_cache는 {taxon_scientific_name: {data: {...}, timestamp: ...}} 형태
            # ========================================
            scientific_name = None
            cached_species_data = None

            for cached_name, cache_entry in self.species_cache.items():
                cached_data = cache_entry.get('data', {})
                # taxon 데이터에서 sis_id 확인
                if cached_data.get('sis_id') == species_id:
                    scientific_name = cached_data.get('scientific_name')
                    cached_species_data = cached_data
                    break

            # ========================================
            # Step 2: 캐시 히트 시 캐시 데이터를 기반으로 상세 정보 반환
            # (v4 API 재호출 없이 빠르게 응답)
            # ========================================
            if cached_species_data:
                # Wikipedia 데이터 조회 (항상 영어로 가져옴 - 가장 완전한 정보)
                wiki_info = {}
                try:
                    wiki_info = await asyncio.wait_for(
                        wikipedia_service.get_species_info(scientific_name, lang="en"),
                        timeout=2.0
                    )
                except asyncio.TimeoutError:
                except Exception as e:
                # 캐시된 데이터를 기반으로 상세 정보 구성
                image_url = wiki_info.get("image_url") or cached_species_data.get("image_url", "")
                common_name = wiki_info.get("common_name") or cached_species_data.get("common_name", scientific_name)
                description = wiki_info.get("description") or cached_species_data.get("description", "No description available")

                detail_response = {
                    "id": species_id,
                    "name": common_name,
                    "scientific_name": scientific_name,
                    "common_name": common_name,
                    "category": cached_species_data.get("category", "동물"),
                    "kingdom": "Animalia",
                    "phylum": "Chordata",
                    "class": "Unknown",
                    "image": image_url,
                    "image_url": image_url,
                    "description": description,
                    "status": cached_species_data.get("risk_level", "DD"),
                    "risk_level": cached_species_data.get("risk_level", "DD"),
                    "population": "Unknown",
                    "habitat": "Various habitats",
                    "threats": [],
                    "country": cached_species_data.get("country", "Global"),
                    "color": "green",
                    "lang": "en",
                }

                # AI 번역 적용 (영어가 아닌 경우)
                if lang != "en":
                    try:
                        detail_response = await translation_service.translate_species_info(
                            detail_response, target_lang=lang
                        )
                    except Exception as e:
                return detail_response

            # ========================================
            # Step 3: 캐시 미스 시 v4 API로 학명 조회
            # (주의: v4는 ID 기반 조회가 제한적, 실패 시 fallback)
            # ========================================
            # v4 API: /taxa/id/{sis_id} 엔드포인트 시도
            try:
                url = f"{self.base_url}/taxa/id/{species_id}"
                response = await asyncio.wait_for(
                    self._make_request(url),
                    timeout=3.0
                )

                if response.status_code == 200:
                    v4_data = response.json()
                    if v4_data and 'taxon' in v4_data:
                        scientific_name = v4_data['taxon'].get('scientific_name')
            except asyncio.TimeoutError:
            except Exception as e:
            # ========================================
            # Step 3.5: scientific_name_hint가 있으면 fallback으로 사용
            # ========================================
            if not scientific_name and scientific_name_hint:
                scientific_name = scientific_name_hint
            # ========================================
            # Step 4: 학명 없으면 에러 응답 반환 (None 대신)
            # ========================================
            if not scientific_name:
                # None 대신 에러 정보를 담은 딕셔너리 반환
                return {
                    "id": species_id,
                    "name": f"Species #{species_id}",
                    "scientific_name": "Unknown",
                    "common_name": f"Species #{species_id}",
                    "category": "동물",
                    "image": "",
                    "image_url": "",
                    "description": "상세 정보를 불러올 수 없습니다. 잠시 후 다시 시도해주세요.",
                    "status": "DD",
                    "risk_level": "DD",
                    "population": "Unknown",
                    "habitat": "Unknown",
                    "threats": [],
                    "country": "Unknown",
                    "color": "green",
                    "error": True,
                    "error_message": "학명을 찾을 수 없습니다"
                }

            # ========================================
            # Step 5: 학명으로 v4 데이터 조회
            # ========================================
            v3_data = None
            try:
                v4_response = await asyncio.wait_for(
                    self.search_by_scientific_name(scientific_name),
                    timeout=5.0
                )

                # v4 -> v3 어댑터 적용
                if v4_response:
                    v3_data = self._v4_to_v3_adapter(v4_response, scientific_name)
                else:
            except asyncio.TimeoutError:
            except Exception as e:
            # ========================================
            # Step 6: Wikipedia 데이터 조회 (항상 영어로 가져옴)
            # ========================================
            wiki_info = {}
            try:
                wiki_info = await asyncio.wait_for(
                    wikipedia_service.get_species_info(scientific_name, lang="en"),
                    timeout=2.0
                )
            except asyncio.TimeoutError:
            except Exception as e:
            # ========================================
            # Step 7: 프론트엔드 호환 응답 구성 (모든 필드 보장)
            # ========================================
            # Wikipedia 이미지가 있으면 사용, 없으면 빈 문자열 (프론트엔드에서 이모지 표시)
            image_url = wiki_info.get("image_url", "") if wiki_info.get("image_url") else ""

            # 공통 이름 결정 (Wikipedia 우선, 없으면 학명)
            common_name = wiki_info.get("common_name", scientific_name)

            detail_response = {
                # 필수 식별 정보
                "id": species_id,
                "name": common_name,
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
                "color": "green",
                "lang": "en",
            }

            # AI 번역 적용 (영어가 아닌 경우)
            if lang != "en":
                try:
                    detail_response = await translation_service.translate_species_info(
                        detail_response, target_lang=lang
                    )
                except Exception as e:
            return detail_response

        except asyncio.TimeoutError:
            # 타임아웃 시에도 에러 정보를 담은 응답 반환
            return {
                "id": species_id,
                "name": f"Species #{species_id}",
                "scientific_name": "Unknown",
                "common_name": f"Species #{species_id}",
                "category": "동물",
                "image": "",
                "image_url": "",
                "description": "요청 시간이 초과되었습니다. 잠시 후 다시 시도해주세요.",
                "status": "DD",
                "risk_level": "DD",
                "population": "Unknown",
                "habitat": "Unknown",
                "threats": [],
                "country": "Unknown",
                "color": "green",
                "error": True,
                "error_message": "Timeout"
            }
        except Exception as e:
            import traceback
            traceback.print_exc()
            # 예외 발생 시에도 에러 정보를 담은 응답 반환
            return {
                "id": species_id,
                "name": f"Species #{species_id}",
                "scientific_name": "Unknown",
                "common_name": f"Species #{species_id}",
                "category": "동물",
                "image": "",
                "image_url": "",
                "description": f"오류가 발생했습니다: {str(e)}",
                "status": "DD",
                "risk_level": "DD",
                "population": "Unknown",
                "habitat": "Unknown",
                "threats": [],
                "country": "Unknown",
                "color": "green",
                "error": True,
                "error_message": str(e)
            }

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
                return None
            
            genus, species = parts[0], parts[1]
            url = f"{self.base_url}/taxa/scientific_name"
            params = {
                "genus_name": genus,
                "species_name": species
            }
            response = await self._make_request(url, params)
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except Exception as e:
            return None

    async def close(self):
        """cloudscraper는 명시적 종료가 필요 없음"""
        pass

iucn_service = IUCNService()

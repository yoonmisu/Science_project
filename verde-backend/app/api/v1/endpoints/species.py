from fastapi import APIRouter, Query, Depends, Request
from typing import Optional, Dict, Any, List
from app.services.iucn_service import iucn_service
from app.services.species_cache_builder import get_cached_counts, SPECIES_COUNT_CACHE
from app.services.search_index import (
    search_species as search_species_index,
    get_species_countries,
    load_search_index,
    KEYWORD_INDEX
)
from app.database import get_db
from app.models.search_history import SearchHistory
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
import difflib

router = APIRouter()

# 서버 시작 시 검색 인덱스 로드
try:
    load_search_index()
except Exception as e:
    print(f"⚠️ 검색 인덱스 로드 실패: {e}")

# 한글-영문 종 이름 매핑 (확장된 버전)
SPECIES_TRANSLATIONS = {
    # 동물 (포유류)
    '판다': ['panda', 'giant panda', 'ailuropoda melanoleuca'],
    '팬더': ['panda', 'giant panda', 'ailuropoda melanoleuca'],
    '호랑이': ['tiger', 'panthera tigris', 'amur tiger', 'siberian tiger'],
    '타이거': ['tiger', 'panthera tigris'],
    '곰': ['bear', 'ursus', 'grizzly', 'polar bear'],
    '베어': ['bear', 'ursus'],
    '흑곰': ['black bear', 'ursus thibetanus', 'asiatic black bear'],
    '북극곰': ['polar bear', 'ursus maritimus'],
    '사자': ['lion', 'panthera leo'],
    '라이언': ['lion', 'panthera leo'],
    '코끼리': ['elephant', 'elephas', 'loxodonta'],
    '엘리펀트': ['elephant'],
    '기린': ['giraffe', 'giraffa camelopardalis'],
    '고릴라': ['gorilla', 'gorilla gorilla'],
    '침팬지': ['chimpanzee', 'pan troglodytes'],
    '늑대': ['wolf', 'canis lupus', 'grey wolf'],
    '여우': ['fox', 'vulpes vulpes'],
    '표범': ['leopard', 'panthera pardus'],
    '치타': ['cheetah', 'acinonyx jubatus'],
    '하이에나': ['hyena', 'crocuta crocuta'],
    '캥거루': ['kangaroo', 'macropus'],
    '코알라': ['koala', 'phascolarctos cinereus'],
    '수달': ['otter', 'lutra lutra'],
    '너구리': ['raccoon dog', 'nyctereutes'],
    '오랑우탄': ['orangutan', 'pongo'],
    '산양': ['wild goat', 'naemorhedus', 'goral'],
    '사슴': ['deer', 'cervus', 'cervidae'],
    '영양': ['antelope', 'gazelle'],
    '재규어': ['jaguar', 'panthera onca'],
    '퓨마': ['puma', 'cougar', 'puma concolor'],
    '스라소니': ['lynx', 'lynx lynx'],
    '바이슨': ['bison', 'bison bison'],
    '들소': ['buffalo', 'bubalus', 'bison'],
    '하마': ['hippopotamus', 'hippopotamus amphibius'],
    '코뿔소': ['rhinoceros', 'rhino', 'diceros', 'ceratotherium'],
    
    # 조류
    '두루미': ['crane', 'grus japonensis', 'red-crowned crane'],
    '크레인': ['crane', 'grus'],
    '독수리': ['eagle', 'haliaeetus', 'bald eagle', 'aquila'],
    '이글': ['eagle', 'haliaeetus'],
    '황새': ['stork', 'ciconia', 'white stork'],
    '따오기': ['crested ibis', 'nipponia nippon'],
    '콘도르': ['condor', 'gymnogyps', 'vultur'],
    '올빼미': ['owl', 'bubo', 'strix'],
    '부엉이': ['owl', 'bubo bubo', 'eagle owl'],
    '매': ['falcon', 'falco', 'falco peregrinus'],
    '솔개': ['kite', 'milvus'],
    '펭귄': ['penguin', 'aptenodytes', 'spheniscidae'],
    '앵무새': ['parrot', 'ara', 'psittacidae'],
    '플라밍고': ['flamingo', 'phoenicopterus'],
    
    # 해양생물
    '돌고래': ['dolphin', 'delphinus', 'tursiops'],
    '고래': ['whale', 'balaenoptera', 'cetacea'],
    '흰수염고래': ['blue whale', 'balaenoptera musculus'],
    '향유고래': ['sperm whale', 'physeter'],
    '혹등고래': ['humpback whale', 'megaptera novaeangliae'],
    '상어': ['shark', 'carcharodon', 'carcharodon carcharias'],
    '백상아리': ['great white shark', 'carcharodon carcharias'],
    '물개': ['seal', 'phoca', 'phocidae'],
    '바다표범': ['seal', 'leopard seal', 'phoca vitulina'],
    '바다사자': ['sea lion', 'otariidae'],
    '해마': ['seahorse', 'hippocampus'],
    '거북이': ['turtle', 'sea turtle', 'chelonia mydas'],
    '바다거북': ['sea turtle', 'chelonia', 'caretta caretta'],
    '듀공': ['dugong', 'dugong dugon'],
    '매너티': ['manatee', 'trichechus'],
    '해파리': ['jellyfish', 'cnidaria'],
    
    # 파충류/양서류
    '악어': ['crocodile', 'crocodylus', 'alligator'],
    '도마뱀': ['lizard', 'lacertilia'],
    '이구아나': ['iguana'],
    '뱀': ['snake', 'serpentes'],
    '개구리': ['frog', 'anura', 'rana'],
    '도롱뇽': ['salamander', 'salamandridae'],
    '아홀로틀': ['axolotl', 'ambystoma mexicanum'],
    
    # 곤충
    '나비': ['butterfly', 'lepidoptera', 'papilionidae'],
    '호랑나비': ['swallowtail', 'papilio'],
    '모르포나비': ['morpho butterfly', 'morpho'],
    '딱정벌레': ['beetle', 'coleoptera'],
    '사슴벌레': ['stag beetle', 'lucanus', 'lucanidae'],
    '장수풍뎅이': ['hercules beetle', 'dynastes', 'rhinoceros beetle'],
    '반딧불이': ['firefly', 'lampyridae'],
    '벌': ['bee', 'apis', 'apidae'],
    '잠자리': ['dragonfly', 'odonata'],
    
    # 식물
    '소나무': ['pine', 'pinus'],
    '전나무': ['fir', 'abies'],
    '삼나무': ['cedar', 'cedrus'],
    '단풍나무': ['maple', 'acer'],
    '벚나무': ['cherry tree', 'prunus'],
    '목련': ['magnolia', 'magnolia sieboldii'],
    '난초': ['orchid', 'orchidaceae'],
    '진달래': ['azalea', 'rhododendron'],
}

@router.get("", response_model=Dict[str, Any])
async def get_species(
    country: Optional[str] = None,
    category: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(3, ge=1, le=100)
):
    """
    외부 API(IUCN + Wikipedia)를 통해 생물 다양성 데이터를 조회합니다.
    데이터베이스를 사용하지 않습니다.
    """
    if not country:
        return {"data": [], "total": 0, "page": page, "totalPages": 0}

    # IUCN API + Wikipedia API 호출 (카테고리 필터링 적용)
    species_list = await iucn_service.get_species_by_country(country, category)

    # API 호출 결과가 None인 경우 처리
    if species_list is None:
        return {
            "data": [],
            "total": 0,
            "page": page,
            "totalPages": 0,
            "message": f"해당 국가({country})의 데이터를 불러올 수 없습니다."
        }

    # 카테고리 필터링은 iucn_service에서 이미 처리됨

    total = len(species_list)

    # 페이지네이션
    start = (page - 1) * limit
    end = start + limit
    paginated_list = species_list[start:end]

    total_pages = (total + limit - 1) // limit if total > 0 else 0

    return {
        "data": paginated_list,
        "total": total,
        "page": page,
        "totalPages": total_pages,
        "message": "데이터가 없습니다." if total == 0 else None
    }

def fuzzy_match(query: str, target: str, threshold: float = 0.6) -> bool:
    """
    퍼지 매칭: 유사도 기반 문자열 비교
    threshold: 0.0 ~ 1.0 (높을수록 엄격)
    """
    ratio = difflib.SequenceMatcher(None, query.lower(), target.lower()).ratio()
    return ratio >= threshold

def translate_query(query: str) -> List[str]:
    """
    한글 검색어를 영문으로 번역
    """
    query_lower = query.lower()

    # 한글 매핑 직접 검색
    if query_lower in SPECIES_TRANSLATIONS:
        return SPECIES_TRANSLATIONS[query_lower]

    # 퍼지 매칭으로 한글 키워드 찾기
    for korean_key, english_terms in SPECIES_TRANSLATIONS.items():
        if fuzzy_match(query_lower, korean_key, threshold=0.7):
            print(f"🔍 한글 매칭: '{query}' → '{korean_key}' → {english_terms}")
            return english_terms

    # 영문 그대로 반환
    return [query]

@router.get("/search", response_model=Dict[str, Any])
async def search_species(
    request: Request,  # IP 추출용
    query: str = Query(..., min_length=1),
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    종 이름으로 검색하여 해당 종이 서식하는 국가 목록을 반환합니다.

    ⚡ 최적화된 검색:
    - 로컬 검색 인덱스 사용 (즉시 응답)
    - 한글 지원 (예: 판다, 호랑이, 곰)
    - 영어 지원 (예: tiger, panda, elephant)
    - 학명 지원 (예: Panthera tigris)
    - 오타 허용 (퍼지 매칭)
    - 부분 일치 지원

    Args:
        query: 검색어 (한글/영어/학명)
        category: 카테고리 필터 (선택사항)

    Returns:
        {query, countries, total, category, matched_species}
    """
    print(f"🔍 검색 요청: '{query}' (카테고리: {category})")

    # 클라이언트 IP 추출
    client_ip = request.client.host if request.client else "unknown"

    # === 1단계: 로컬 인덱스 검색 (즉시) ===
    countries, matched_name, matched_category = get_species_countries(query, category)

    # 검색 결과 로깅
    if countries:
        print(f"✅ 로컬 인덱스 매칭: '{matched_name}' → {len(countries)}개 국가")
        print(f"   국가: {countries}")
        print(f"   카테고리: {matched_category}")
    else:
        print(f"⚠️ 로컬 인덱스에서 매칭 없음: '{query}'")

        # === 2단계: 폴백 - 기존 번역 기반 검색 ===
        search_terms = translate_query(query)
        print(f"📝 번역 기반 검색: {search_terms}")

        # 로컬 인덱스의 키워드와 퍼지 매칭
        from app.services.search_index import fuzzy_match_keyword, SPECIES_DATA

        for term in search_terms:
            matched_species = fuzzy_match_keyword(term, threshold=0.5)
            if matched_species:
                for sci_name in matched_species:
                    info = SPECIES_DATA.get(sci_name, {})
                    for country in info.get("countries", []):
                        if country not in countries:
                            countries.append(country)
                    if not matched_name:
                        matched_name = info.get("korean_name") or info.get("common_name") or sci_name
                        matched_category = info.get("category")

        if countries:
            print(f"✅ 번역 기반 매칭: {len(countries)}개 국가")

    # IP 기반 중복 검색 확인
    last_query = iucn_service.last_search_cache.get(client_ip)
    is_duplicate = last_query and last_query.lower() == query.lower()

    # 마지막 검색어 업데이트
    iucn_service.last_search_cache[client_ip] = query

    # 검색 기록 저장 (중복이 아닌 경우에만)
    if not is_duplicate:
        try:
            search_record = SearchHistory(
                query=query,
                category=matched_category,
                result_count=len(countries)
            )
            db.add(search_record)
            db.commit()
            print(f"💾 검색 기록 저장: '{query}' (결과: {len(countries)}개)")
        except Exception as e:
            print(f"⚠️ 검색 기록 저장 실패: {e}")
            db.rollback()
    else:
        print(f"🔄 중복 검색 (IP: {client_ip}): '{query}' - 통계 제외")

    print(f"🎯 최종 결과: {len(countries)}개 국가 - {countries} (카테고리: {matched_category})")

    return {
        "query": query,
        "countries": countries,
        "total": len(countries),
        "category": matched_category,
        "matched_species": matched_name  # 매칭된 종 이름 추가
    }

@router.get("/trending", response_model=Dict[str, Any])
async def get_trending_searches(
    limit: int = Query(7, ge=1, le=20),
    hours: int = Query(24, ge=1, le=168),  # 기본 24시간, 최대 7일
    db: Session = Depends(get_db)
):
    """
    실시간 검색어 랭킹을 조회합니다.
    - limit: 조회할 검색어 개수 (기본 7개)
    - hours: 조회 기간 (기본 24시간)
    """
    try:
        # 특정 시간 이내의 검색 기록만 조회
        since = datetime.utcnow() - timedelta(hours=hours)

        # 검색어별 검색 횟수 집계 (대소문자 구분 없이)
        trending = db.query(
            func.lower(SearchHistory.query).label('query'),
            func.count(SearchHistory.id).label('count')
        ).filter(
            SearchHistory.searched_at >= since
        ).group_by(
            func.lower(SearchHistory.query)
        ).order_by(
            func.count(SearchHistory.id).desc()
        ).limit(limit).all()

        # 결과 포맷팅
        result = [
            {
                "rank": idx + 1,
                "query": item.query,
                "count": item.count
            }
            for idx, item in enumerate(trending)
        ]

        print(f"📊 실시간 검색어 조회: {len(result)}개 (최근 {hours}시간)")

        return {
            "data": result,
            "period_hours": hours,
            "total": len(result)
        }
    except Exception as e:
        print(f"❌ 실시간 검색어 조회 실패: {e}")
        return {
            "data": [],
            "period_hours": hours,
            "total": 0
        }

@router.get("/random-daily", response_model=Dict[str, Any])
async def get_daily_random_species():
    """
    오늘의 랜덤 종을 조회합니다.
    날짜 기반 시드를 사용하여 하루 동안 같은 종이 반환됩니다.
    """
    import hashlib
    from datetime import date
    from app.services.country_species_map import COUNTRY_SPECIES_MAP
    
    try:
        # 날짜 기반 시드 생성 (같은 날에는 같은 종 반환)
        today = date.today().isoformat()
        seed = int(hashlib.md5(today.encode()).hexdigest(), 16)
        
        # 모든 종 목록 수집
        all_species = []
        for country_code, country_data in COUNTRY_SPECIES_MAP.items():
            if isinstance(country_data, dict):
                for category, species_list in country_data.items():
                    if isinstance(species_list, list):
                        all_species.extend(species_list)
        
        if not all_species:
            return {"error": "No species available", "species": None}
        
        # 중복 제거
        unique_species = list(set(all_species))
        
        # 날짜 기반 랜덤 선택
        selected_index = seed % len(unique_species)
        selected_species_name = unique_species[selected_index]
        
        print(f"🎲 오늘의 랜덤 종: {selected_species_name}")
        
        # 종 상세 정보 조회 (캐시된 데이터 사용)
        # 간단한 응답 반환 (상세 정보는 클라이언트에서 별도 조회)
        return {
            "date": today,
            "scientific_name": selected_species_name,
            "message": "Species of the Day"
        }
        
    except Exception as e:
        print(f"❌ 오늘의 랜덤 종 조회 실패: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e), "species": None}

@router.get("/weekly-top", response_model=Dict[str, Any])
async def get_weekly_top_species(
    db: Session = Depends(get_db)
):
    """
    주간 최다 검색된 종을 조회합니다.
    최근 7일간 가장 많이 검색된 종 이름을 반환합니다.
    """
    try:
        since = datetime.utcnow() - timedelta(days=7)
        
        # 최근 7일간 가장 많이 검색된 쿼리 조회
        top_search = db.query(
            func.lower(SearchHistory.query).label('query'),
            func.count(SearchHistory.id).label('count')
        ).filter(
            SearchHistory.searched_at >= since
        ).group_by(
            func.lower(SearchHistory.query)
        ).order_by(
            func.count(SearchHistory.id).desc()
        ).first()
        
        if not top_search:
            print("📊 주간 인기 종: 검색 기록 없음")
            return {"species_name": None, "search_count": 0, "message": "No search data"}
        
        print(f"🔥 주간 인기 종: {top_search.query} ({top_search.count}회)")
        
        return {
            "species_name": top_search.query,
            "search_count": top_search.count,
            "period_days": 7,
            "message": "Species of the Week"
        }
        
    except Exception as e:
        print(f"❌ 주간 인기 종 조회 실패: {e}")
        import traceback
        traceback.print_exc()
        return {"species_name": None, "search_count": 0, "error": str(e)}

@router.get("/endangered", response_model=Dict[str, Any])
async def get_endangered_species(
    country: str = Query(..., description="국가 코드 (예: KR, US, CN)"),
    category: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """
    멸종위기종 목록을 조회합니다.
    IUCN 위험 등급이 CR (Critically Endangered), EN (Endangered), VU (Vulnerable)인 종만 반환합니다.

    Args:
        country: 국가 코드 (ISO Alpha-2)
        category: 카테고리 필터 (선택사항)
        page: 페이지 번호
        limit: 페이지당 항목 수
    """
    try:
        print(f"🔍 멸종위기종 조회: {country} (카테고리: {category})")

        # 국가별 전체 종 데이터 조회
        species_list = await iucn_service.get_species_by_country(country)

        # 멸종위기종만 필터링 (CR, EN, VU)
        endangered_list = [
            s for s in species_list
            if s.get("risk_level") in ["CR", "EN", "VU"]
        ]

        # 카테고리 필터링
        if category and category != "동물":
            endangered_list = [s for s in endangered_list if s.get("category") == category]

        total = len(endangered_list)

        # 페이지네이션
        start = (page - 1) * limit
        end = start + limit
        paginated_list = endangered_list[start:end]

        total_pages = (total + limit - 1) // limit if total > 0 else 0

        print(f"✅ 멸종위기종 {total}개 발견 (현재 페이지: {len(paginated_list)}개)")

        return {
            "data": paginated_list,
            "total": total,
            "page": page,
            "totalPages": total_pages
        }
    except Exception as e:
        print(f"❌ 멸종위기종 조회 실패: {e}")
        return {
            "data": [],
            "total": 0,
            "page": page,
            "totalPages": 0
        }

@router.get("/stats/countries", response_model=Dict[str, Any])
async def get_all_countries_species_count(
    category: Optional[str] = None
):
    """
    사전 계산된 캐시에서 각 국가별 카테고리별 종 개수를 반환합니다.

    ⚡ 최적화:
    - 서버 시작 시 JSON 파일에서 로드된 캐시 사용
    - 실시간 API 호출 없이 즉시 응답 (< 10ms)

    Args:
        category: 카테고리 필터 (동물, 식물, 곤충, 해양생물)

    Returns:
        { 'KR': 56, 'US': 100, 'BR': 89, ... } (카테고리별 종 개수)
    """
    category = category or "동물"
    print(f"📊 [{category}] 국가별 종 개수 조회 (캐시)")

    # 캐시에서 조회
    country_counts = get_cached_counts(category)

    if country_counts:
        counts = list(country_counts.values())
        print(f"✅ [{category}] 캐시 결과: {len(country_counts)}개 국가")
        print(f"   범위: {min(counts)} ~ {max(counts)}")
        sample = dict(list(country_counts.items())[:5])
        print(f"   샘플: {sample}")
    else:
        print(f"⚠️ [{category}] 캐시 데이터 없음 - 캐시 빌드 필요")
        print(f"   실행: python -m app.services.species_cache_builder")

    return country_counts

@router.get("/{species_id}", response_model=Dict[str, Any])
async def get_species_detail(species_id: int):
    """
    특정 종의 상세 정보를 조회합니다.
    IUCN API와 Wikipedia API를 통해 실시간으로 데이터를 가져옵니다.

    참고: species_id는 IUCN taxonid를 의미합니다.
    """
    try:
        print(f"🔍 종 상세 정보 조회: ID {species_id}")

        # IUCN API를 통해 상세 정보 조회
        species_detail = await iucn_service.get_species_detail(species_id)

        if not species_detail:
            return {
                "error": "Species not found",
                "id": species_id
            }

        print(f"✅ 상세 정보 수신 완료: {species_detail.get('common_name', species_detail.get('scientific_name'))}")

        return species_detail
    except Exception as e:
        print(f"❌ 종 상세 정보 조회 실패: {e}")
        return {
            "error": str(e),
            "id": species_id
        }

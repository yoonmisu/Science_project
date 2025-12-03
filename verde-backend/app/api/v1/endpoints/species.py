from fastapi import APIRouter, Query, Depends
from typing import Optional, Dict, Any, List
from app.services.iucn_service import iucn_service
from app.database import get_db
from app.models.search_history import SearchHistory
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
import difflib

router = APIRouter()

# 한글-영문 종 이름 매핑
SPECIES_TRANSLATIONS = {
    # 동물
    '판다': ['panda', 'giant panda', 'ailuropoda'],
    '팬더': ['panda', 'giant panda', 'ailuropoda'],
    '호랑이': ['tiger', 'panthera tigris', 'amur tiger', 'siberian tiger'],
    '타이거': ['tiger', 'panthera tigris'],
    '곰': ['bear', 'ursus', 'grizzly', 'polar'],
    '베어': ['bear', 'ursus'],
    '두루미': ['crane', 'grus', 'red-crowned'],
    '크레인': ['crane', 'grus'],
    '독수리': ['eagle', 'haliaeetus', 'bald eagle'],
    '이글': ['eagle', 'haliaeetus'],
    '사자': ['lion', 'panthera leo'],
    '라이언': ['lion', 'panthera leo'],
    '코끼리': ['elephant', 'elephas', 'loxodonta'],
    '엘리펀트': ['elephant'],
    '기린': ['giraffe', 'giraffa'],
    '고릴라': ['gorilla'],
    '침팬지': ['chimpanzee', 'pan'],
    '늑대': ['wolf', 'canis lupus'],
    '여우': ['fox', 'vulpes'],
    '표범': ['leopard', 'panthera pardus'],
    '치타': ['cheetah', 'acinonyx'],
    '하이에나': ['hyena', 'crocuta'],
    '악어': ['crocodile', 'alligator'],
    '펭귄': ['penguin', 'aptenodytes'],
    '돌고래': ['dolphin', 'delphinus'],
    '고래': ['whale', 'balaenoptera'],
    '상어': ['shark', 'carcharodon'],
    '물개': ['seal', 'phoca'],
    '바다표범': ['seal', 'leopard seal'],
    '캥거루': ['kangaroo', 'macropus'],
    '코알라': ['koala', 'phascolarctos'],
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

    # IUCN API + Wikipedia API 호출
    species_list = await iucn_service.get_species_by_country(country)

    # 카테고리 필터링
    if category and category != "동물":
        species_list = [s for s in species_list if s.get("category") == category]

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
        "totalPages": total_pages
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
    query: str = Query(..., min_length=1),
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    종 이름으로 검색하여 해당 종이 서식하는 국가 목록을 반환합니다.
    - 한글 지원 (예: 판다, 호랑이, 곰)
    - 오타 허용 (퍼지 매칭)
    - 부분 일치 지원
    - 매칭된 종의 카테고리 정보 반환
    """
    print(f"🔍 검색 요청: '{query}' (카테고리: {category})")

    # 한글을 영문으로 번역
    search_terms = translate_query(query)
    print(f"📝 검색어 확장: {search_terms}")

    # 여러 국가에서 종 검색
    test_countries = ['KR', 'US', 'RU', 'CN', 'JP', 'BR', 'ID', 'IN', 'AU', 'MX']
    matching_countries = []
    matched_category = None  # 매칭된 종의 카테고리

    for country_code in test_countries:
        species_list = await iucn_service.get_species_by_country(country_code)

        # 카테고리 필터링
        if category and category != "동물":
            species_list = [s for s in species_list if s.get("category") == category]

        # 종 이름으로 검색 (common_name, scientific_name)
        for species in species_list:
            common_name = species.get("common_name", "").lower()
            scientific_name = species.get("scientific_name", "").lower()

            # 각 검색어로 체크
            found = False
            for term in search_terms:
                term_lower = term.lower()

                # 1. 정확한 부분 일치
                if term_lower in common_name or term_lower in scientific_name:
                    found = True
                    break

                # 2. 퍼지 매칭 (오타 허용)
                if fuzzy_match(term_lower, common_name, threshold=0.65) or \
                   fuzzy_match(term_lower, scientific_name, threshold=0.65):
                    found = True
                    break

            if found:
                if country_code not in matching_countries:
                    matching_countries.append(country_code)
                    # 첫 번째 매칭된 종의 카테고리 저장
                    if matched_category is None:
                        matched_category = species.get("category", "동물")
                    print(f"✅ 매칭: {country_code} - {common_name} ({scientific_name}) [{matched_category}]")
                break

    print(f"🎯 최종 결과: {len(matching_countries)}개 국가 - {matching_countries} (카테고리: {matched_category})")

    # 검색 기록 저장
    try:
        search_record = SearchHistory(
            query=query,
            category=matched_category,
            result_count=len(matching_countries)
        )
        db.add(search_record)
        db.commit()
        print(f"💾 검색 기록 저장: '{query}' (결과: {len(matching_countries)}개)")
    except Exception as e:
        print(f"⚠️ 검색 기록 저장 실패: {e}")
        db.rollback()

    return {
        "query": query,
        "countries": matching_countries,
        "total": len(matching_countries),
        "category": matched_category  # 매칭된 카테고리 추가
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

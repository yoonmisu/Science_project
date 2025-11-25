"""
표준화된 API 응답 포맷

Verde 백엔드의 모든 API 엔드포인트는 일관된 응답 형식을 사용합니다.

성공 응답 형식:
{
    "success": true,
    "data": { ... },
    "metadata": {
        "timestamp": "2025-01-15T14:32:18Z",
        "api_version": "v1",
        "source": "database" | "cache" | "external_api"
    }
}

에러 응답 형식:
{
    "success": false,
    "error": {
        "code": "SPECIES_NOT_FOUND",
        "message": "해당 생물종을 찾을 수 없습니다",
        "details": {}
    },
    "metadata": {
        "timestamp": "2025-01-15T14:32:18Z"
    }
}
"""

from typing import Any, Dict, Optional
from datetime import datetime
from fastapi.responses import JSONResponse, Response


class APIResponse:
    """
    표준화된 API 응답 생성기

    사용 예시:
    >>> from app.api.response import APIResponse
    >>>
    >>> # 성공 응답
    >>> return APIResponse.success({"species": [...]}, source="database")
    >>>
    >>> # 에러 응답
    >>> return APIResponse.error(
    ...     code="SPECIES_NOT_FOUND",
    ...     message="해당 생물종을 찾을 수 없습니다",
    ...     status_code=404
    ... )
    """

    API_VERSION = "v1"

    @staticmethod
    def success(
        data: Any,
        source: str = "database",
        cache_info: Optional[Dict] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        성공 응답 생성

        Args:
            data: 반환할 데이터 (딕셔너리, 리스트, Pydantic 모델 등)
            source: 데이터 출처
                - "database": 데이터베이스에서 직접 조회
                - "cache": 캐시에서 조회 (Redis 등)
                - "external_api": 외부 API에서 조회 (GBIF, iNaturalist 등)
            cache_info: 캐시 관련 정보 (선택)
                예: {"hit": true, "ttl": 300, "key": "species:123"}
            metadata: 추가 메타데이터 (선택)

        Returns:
            표준 형식의 성공 응답 딕셔너리

        예시:
        >>> APIResponse.success(
        ...     data={"species": [{"name": "호랑이"}]},
        ...     source="database",
        ...     cache_info={"hit": False}
        ... )
        {
            "success": True,
            "data": {"species": [{"name": "호랑이"}]},
            "metadata": {
                "timestamp": "2025-01-15T14:32:18Z",
                "api_version": "v1",
                "source": "database",
                "cache": {"hit": False}
            }
        }
        """
        response = {
            "success": True,
            "data": data,
            "metadata": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "api_version": APIResponse.API_VERSION,
                "source": source
            }
        }

        # 캐시 정보 추가
        if cache_info:
            response["metadata"]["cache"] = cache_info

        # 추가 메타데이터 병합
        if metadata:
            response["metadata"].update(metadata)

        return response

    @staticmethod
    def error(
        code: str,
        message: str,
        status_code: int = 400,
        details: Optional[Dict] = None,
        suggestions: Optional[list] = None
    ) -> JSONResponse:
        """
        에러 응답 생성

        Args:
            code: 에러 코드 (대문자 스네이크 케이스)
                예: "SPECIES_NOT_FOUND", "INVALID_COUNTRY_CODE"
            message: 사용자에게 보여줄 한글 에러 메시지
            status_code: HTTP 상태 코드 (기본 400)
            details: 에러 상세 정보 (선택)
            suggestions: 해결 방법 제안 (선택)

        Returns:
            FastAPI JSONResponse 객체

        예시:
        >>> APIResponse.error(
        ...     code="SPECIES_NOT_FOUND",
        ...     message="해당 생물종을 찾을 수 없습니다",
        ...     status_code=404,
        ...     details={"species_id": 999},
        ...     suggestions=["ID를 확인해주세요", "검색어를 변경해보세요"]
        ... )
        """
        content = {
            "success": False,
            "error": {
                "code": code,
                "message": message,
                "details": details or {}
            },
            "metadata": {
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }

        # 해결 방법 제안 추가
        if suggestions:
            content["error"]["suggestions"] = suggestions

        return JSONResponse(
            status_code=status_code,
            content=content
        )

    @staticmethod
    def paginated(
        items: list,
        total: int,
        page: int,
        limit: int,
        source: str = "database",
        additional_data: Optional[Dict] = None,
        response: Optional[Response] = None
    ) -> Dict:
        """
        페이지네이션된 응답 생성

        Args:
            items: 현재 페이지의 아이템 리스트
            total: 전체 아이템 수
            page: 현재 페이지 번호 (1부터 시작)
            limit: 페이지당 아이템 수
            source: 데이터 출처
            additional_data: 추가 데이터 (선택)

        Returns:
            페이지네이션 정보가 포함된 표준 응답

        예시:
        >>> APIResponse.paginated(
        ...     items=[{"name": "호랑이"}, {"name": "사자"}],
        ...     total=150,
        ...     page=1,
        ...     limit=20
        ... )
        {
            "success": True,
            "data": {
                "items": [...],
                "pagination": {
                    "page": 1,
                    "limit": 20,
                    "total": 150,
                    "pages": 8,
                    "has_next": true,
                    "has_prev": false
                }
            },
            "metadata": {...}
        }
        """
        pages = (total + limit - 1) // limit if limit > 0 else 1
        has_next = page < pages
        has_prev = page > 1

        # Response 헤더에 페이지네이션 정보 추가 (프론트엔드 친화적)
        if response:
            response.headers["X-Total-Count"] = str(total)
            response.headers["X-Page"] = str(page)
            response.headers["X-Per-Page"] = str(limit)
            response.headers["X-Total-Pages"] = str(pages)
            response.headers["X-Has-Next"] = str(has_next).lower()
            response.headers["X-Has-Prev"] = str(has_prev).lower()

        data = {
            "items": items,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": pages,
                "has_next": has_next,
                "has_prev": has_prev
            }
        }

        # 추가 데이터 병합
        if additional_data:
            data.update(additional_data)

        return APIResponse.success(data, source=source)


# 자주 사용되는 에러 코드 상수
class ErrorCodes:
    """
    표준 에러 코드 정의

    사용법:
    >>> from app.api.response import APIResponse, ErrorCodes
    >>> return APIResponse.error(
    ...     code=ErrorCodes.SPECIES_NOT_FOUND,
    ...     message="해당 생물종을 찾을 수 없습니다",
    ...     status_code=404
    ... )
    """
    # 리소스 관련
    SPECIES_NOT_FOUND = "SPECIES_NOT_FOUND"
    REGION_NOT_FOUND = "REGION_NOT_FOUND"
    COUNTRY_NOT_FOUND = "COUNTRY_NOT_FOUND"

    # 검증 관련
    INVALID_INPUT = "INVALID_INPUT"
    INVALID_COUNTRY_CODE = "INVALID_COUNTRY_CODE"
    INVALID_CATEGORY = "INVALID_CATEGORY"
    INVALID_COORDINATES = "INVALID_COORDINATES"

    # 인증/권한 관련
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    INVALID_TOKEN = "INVALID_TOKEN"

    # 데이터 관련
    DUPLICATE_ENTRY = "DUPLICATE_ENTRY"
    DATA_VALIDATION_ERROR = "DATA_VALIDATION_ERROR"

    # 외부 API 관련
    EXTERNAL_API_ERROR = "EXTERNAL_API_ERROR"
    GBIF_API_ERROR = "GBIF_API_ERROR"
    IUCN_API_ERROR = "IUCN_API_ERROR"
    INATURALIST_API_ERROR = "INATURALIST_API_ERROR"

    # 시스템 관련
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    CACHE_ERROR = "CACHE_ERROR"


# 헬퍼 함수들
def success_response(*args, **kwargs):
    """APIResponse.success의 단축 함수"""
    return APIResponse.success(*args, **kwargs)


def error_response(*args, **kwargs):
    """APIResponse.error의 단축 함수"""
    return APIResponse.error(*args, **kwargs)


def paginated_response(*args, **kwargs):
    """APIResponse.paginated의 단축 함수"""
    return APIResponse.paginated(*args, **kwargs)

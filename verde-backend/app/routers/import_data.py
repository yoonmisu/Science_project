from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
import logging

from app.database import get_db
from app.dependencies import get_current_admin_user
from app.models.user import User
from app.services.import_service import ImportService, GBIFService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/import", tags=["Import"])


@router.post(
    "/csv",
    summary="CSV 파일 임포트",
    description="CSV 파일에서 종 데이터를 일괄 임포트합니다. 관리자 권한이 필요합니다."
)
async def import_csv(
    file: UploadFile = File(..., description="CSV 파일"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """CSV 파일에서 종 데이터 임포트"""
    try:
        # 파일 형식 확인
        if not file.filename.endswith('.csv'):
            raise HTTPException(
                status_code=400,
                detail="CSV 파일만 업로드할 수 있습니다"
            )

        # 파일 읽기
        content = await file.read()
        csv_content = content.decode('utf-8')

        # 임포트 실행
        import_service = ImportService(db)
        result = import_service.import_species_from_csv(csv_content)

        logger.info(f"CSV imported by {current_user.username}: {result['imported']} species")

        return {
            "success": True,
            "data": result,
            "message": f"{result['imported']}개의 종이 임포트되었습니다"
        }

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="파일 인코딩을 확인해주세요. UTF-8 형식이어야 합니다."
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CSV import error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="CSV 임포트 중 오류가 발생했습니다"
        )


@router.post(
    "/json",
    summary="JSON 파일 임포트",
    description="JSON 파일에서 종 데이터를 일괄 임포트합니다. 관리자 권한이 필요합니다."
)
async def import_json(
    file: UploadFile = File(..., description="JSON 파일"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """JSON 파일에서 종 데이터 임포트"""
    try:
        # 파일 형식 확인
        if not file.filename.endswith('.json'):
            raise HTTPException(
                status_code=400,
                detail="JSON 파일만 업로드할 수 있습니다"
            )

        # 파일 읽기
        content = await file.read()
        json_content = content.decode('utf-8')

        # 임포트 실행
        import_service = ImportService(db)
        result = import_service.import_species_from_json(json_content)

        logger.info(f"JSON imported by {current_user.username}: {result['imported']} species")

        return {
            "success": True,
            "data": result,
            "message": f"{result['imported']}개의 종이 임포트되었습니다"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="파일 인코딩을 확인해주세요. UTF-8 형식이어야 합니다."
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"JSON import error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="JSON 임포트 중 오류가 발생했습니다"
        )


# GBIF API 엔드포인트
@router.get(
    "/gbif/search",
    summary="GBIF 종 검색",
    description="GBIF API에서 종을 검색합니다."
)
async def search_gbif_species(
    query: str = Query(..., description="검색어"),
    limit: int = Query(20, ge=1, le=100, description="결과 수"),
    db: Session = Depends(get_db)
):
    """GBIF에서 종 검색"""
    try:
        async with GBIFService(db) as gbif:
            results = await gbif.search_species(query, limit)

        return {
            "success": True,
            "data": results,
            "total": len(results)
        }

    except Exception as e:
        logger.error(f"GBIF search error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="GBIF 검색 중 오류가 발생했습니다"
        )


@router.get(
    "/gbif/species/{gbif_key}",
    summary="GBIF 종 상세 정보",
    description="GBIF에서 특정 종의 상세 정보를 조회합니다."
)
async def get_gbif_species_detail(
    gbif_key: int,
    db: Session = Depends(get_db)
):
    """GBIF 종 상세 정보"""
    try:
        async with GBIFService(db) as gbif:
            details = await gbif.get_species_details(gbif_key)
            media = await gbif.get_species_media(gbif_key)

        return {
            "success": True,
            "data": {
                "details": details,
                "media": media
            }
        }

    except Exception as e:
        logger.error(f"GBIF detail error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="GBIF 상세 조회 중 오류가 발생했습니다"
        )


@router.get(
    "/gbif/occurrences/{country_code}",
    summary="국가별 종 출현 데이터",
    description="GBIF에서 특정 국가의 종 출현 데이터를 조회합니다."
)
async def get_gbif_occurrences(
    country_code: str,
    limit: int = Query(100, ge=1, le=1000, description="결과 수"),
    db: Session = Depends(get_db)
):
    """국가별 종 출현 데이터"""
    try:
        async with GBIFService(db) as gbif:
            results = await gbif.get_occurrences_by_country(country_code, limit)

        return {
            "success": True,
            "data": results,
            "total": len(results)
        }

    except Exception as e:
        logger.error(f"GBIF occurrences error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="GBIF 출현 데이터 조회 중 오류가 발생했습니다"
        )


@router.post(
    "/gbif/import",
    summary="GBIF에서 임포트",
    description="GBIF에서 종 데이터를 검색하여 DB에 임포트합니다. 관리자 권한이 필요합니다."
)
async def import_from_gbif(
    query: str = Query(..., description="검색어"),
    country: str = Query(..., description="국가명"),
    region: str = Query(..., description="지역명"),
    limit: int = Query(50, ge=1, le=500, description="임포트할 최대 종 수"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """GBIF에서 종 데이터 임포트"""
    try:
        async with GBIFService(db) as gbif:
            result = await gbif.import_species_from_gbif(query, country, region, limit)

        logger.info(f"GBIF imported by {current_user.username}: {result['imported']} species")

        return {
            "success": True,
            "data": result,
            "message": f"{result['imported']}개의 종이 GBIF에서 임포트되었습니다"
        }

    except Exception as e:
        logger.error(f"GBIF import error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="GBIF 임포트 중 오류가 발생했습니다"
        )

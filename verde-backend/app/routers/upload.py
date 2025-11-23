from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
import logging

from app.database import get_db
from app.dependencies import get_current_active_user, get_current_admin_user
from app.models.user import User
from app.models.species import Species
from app.services.storage_service import storage_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["Upload"])

# 허용된 이미지 형식
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def validate_image(file: UploadFile):
    """이미지 파일 검증"""
    # 확장자 확인
    ext = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
    if f'.{ext}' not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 파일 형식입니다. 허용: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Content-Type 확인
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=400,
            detail="이미지 파일만 업로드할 수 있습니다"
        )


@router.post(
    "/image",
    summary="이미지 업로드",
    description="이미지를 업로드합니다. 자동으로 리사이징되고 썸네일이 생성됩니다."
)
async def upload_image(
    file: UploadFile = File(..., description="업로드할 이미지 파일"),
    folder: str = Form("species", description="저장 폴더"),
    current_user: User = Depends(get_current_active_user)
):
    """이미지 업로드"""
    try:
        # 파일 검증
        validate_image(file)

        # 파일 내용 읽기
        content = await file.read()

        # 파일 크기 확인
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"파일 크기가 너무 큽니다. 최대 {MAX_FILE_SIZE // 1024 // 1024}MB"
            )

        # 업로드
        result = await storage_service.upload_image(
            file_content=content,
            original_filename=file.filename,
            folder=folder
        )

        logger.info(f"Image uploaded by {current_user.username}: {result['filename']}")

        return {
            "success": True,
            "data": result,
            "message": "이미지가 성공적으로 업로드되었습니다"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading image: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="이미지 업로드 중 오류가 발생했습니다"
        )


@router.post(
    "/species/{species_id}/image",
    summary="종 이미지 업로드",
    description="특정 종의 이미지를 업로드하고 연결합니다. 관리자 권한이 필요합니다."
)
async def upload_species_image(
    species_id: int,
    file: UploadFile = File(..., description="업로드할 이미지 파일"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """종 이미지 업로드 및 연결"""
    try:
        # 종 확인
        species = db.query(Species).filter(Species.id == species_id).first()
        if not species:
            raise HTTPException(
                status_code=404,
                detail="생물종을 찾을 수 없습니다"
            )

        # 파일 검증
        validate_image(file)

        # 파일 내용 읽기
        content = await file.read()

        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"파일 크기가 너무 큽니다. 최대 {MAX_FILE_SIZE // 1024 // 1024}MB"
            )

        # 업로드
        result = await storage_service.upload_image(
            file_content=content,
            original_filename=file.filename,
            folder=f"species/{species_id}"
        )

        # 종에 이미지 URL 연결
        species.image_url = result['image_url']
        db.commit()

        logger.info(f"Image uploaded for species {species_id} by {current_user.username}")

        return {
            "success": True,
            "data": {
                "species_id": species_id,
                "species_name": species.name,
                **result
            },
            "message": "이미지가 성공적으로 업로드되었습니다"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading species image: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="이미지 업로드 중 오류가 발생했습니다"
        )


@router.delete(
    "/image",
    summary="이미지 삭제",
    description="업로드된 이미지를 삭제합니다. 관리자 권한이 필요합니다."
)
async def delete_image(
    path: str,
    current_user: User = Depends(get_current_admin_user)
):
    """이미지 삭제"""
    try:
        success = await storage_service.delete_image(path)

        if not success:
            raise HTTPException(
                status_code=404,
                detail="이미지를 찾을 수 없습니다"
            )

        logger.info(f"Image deleted by {current_user.username}: {path}")

        return {
            "success": True,
            "message": "이미지가 삭제되었습니다"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting image: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="이미지 삭제 중 오류가 발생했습니다"
        )

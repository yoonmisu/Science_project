import os
import uuid
import logging
from io import BytesIO
from typing import Optional, Tuple
from datetime import datetime

from PIL import Image
import boto3
from botocore.exceptions import ClientError
from minio import Minio
from minio.error import S3Error

from app.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """S3/MinIO 스토리지 서비스"""

    def __init__(self):
        self.storage_type = getattr(settings, 'STORAGE_TYPE', 'local')
        self.bucket_name = getattr(settings, 'STORAGE_BUCKET', 'verde-images')

        if self.storage_type == 's3':
            self._init_s3()
        elif self.storage_type == 'minio':
            self._init_minio()
        else:
            self._init_local()

    def _init_s3(self):
        """AWS S3 클라이언트 초기화"""
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID', None),
            aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY', None),
            region_name=getattr(settings, 'AWS_REGION', 'ap-northeast-2')
        )
        logger.info("S3 storage initialized")

    def _init_minio(self):
        """MinIO 클라이언트 초기화"""
        self.minio_client = Minio(
            getattr(settings, 'MINIO_ENDPOINT', 'localhost:9000'),
            access_key=getattr(settings, 'MINIO_ACCESS_KEY', 'minioadmin'),
            secret_key=getattr(settings, 'MINIO_SECRET_KEY', 'minioadmin'),
            secure=getattr(settings, 'MINIO_SECURE', False)
        )

        # 버킷이 없으면 생성
        if not self.minio_client.bucket_exists(self.bucket_name):
            self.minio_client.make_bucket(self.bucket_name)
            logger.info(f"Created MinIO bucket: {self.bucket_name}")

        logger.info("MinIO storage initialized")

    def _init_local(self):
        """로컬 스토리지 초기화"""
        self.local_path = getattr(settings, 'LOCAL_STORAGE_PATH', './uploads')
        os.makedirs(self.local_path, exist_ok=True)
        logger.info(f"Local storage initialized at {self.local_path}")

    def _generate_filename(self, original_filename: str) -> str:
        """고유한 파일명 생성"""
        ext = os.path.splitext(original_filename)[1].lower()
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        return f"{timestamp}_{unique_id}{ext}"

    def _resize_image(
        self,
        image_data: bytes,
        max_size: Tuple[int, int] = (1200, 1200),
        quality: int = 85
    ) -> bytes:
        """이미지 리사이징 및 최적화"""
        try:
            img = Image.open(BytesIO(image_data))

            # EXIF 회전 정보 적용
            try:
                from PIL import ExifTags
                for orientation in ExifTags.TAGS.keys():
                    if ExifTags.TAGS[orientation] == 'Orientation':
                        break

                exif = img._getexif()
                if exif:
                    orientation_value = exif.get(orientation)
                    if orientation_value == 3:
                        img = img.rotate(180, expand=True)
                    elif orientation_value == 6:
                        img = img.rotate(270, expand=True)
                    elif orientation_value == 8:
                        img = img.rotate(90, expand=True)
            except (AttributeError, KeyError, IndexError):
                pass

            # RGB 변환 (PNG 투명도 처리)
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            # 리사이징
            img.thumbnail(max_size, Image.Resampling.LANCZOS)

            # JPEG로 저장
            output = BytesIO()
            img.save(output, format='JPEG', quality=quality, optimize=True)
            output.seek(0)

            logger.info(f"Image resized: {img.size}")
            return output.read()

        except Exception as e:
            logger.error(f"Error resizing image: {str(e)}")
            raise

    def _create_thumbnail(
        self,
        image_data: bytes,
        size: Tuple[int, int] = (300, 300),
        quality: int = 80
    ) -> bytes:
        """썸네일 생성"""
        try:
            img = Image.open(BytesIO(image_data))

            if img.mode != 'RGB':
                img = img.convert('RGB')

            img.thumbnail(size, Image.Resampling.LANCZOS)

            output = BytesIO()
            img.save(output, format='JPEG', quality=quality, optimize=True)
            output.seek(0)

            return output.read()

        except Exception as e:
            logger.error(f"Error creating thumbnail: {str(e)}")
            raise

    async def upload_image(
        self,
        file_content: bytes,
        original_filename: str,
        folder: str = "species"
    ) -> dict:
        """이미지 업로드 (리사이징 + 썸네일 생성)"""
        try:
            # 파일명 생성
            filename = self._generate_filename(original_filename)
            thumb_filename = f"thumb_{filename}"

            # 이미지 처리
            resized_image = self._resize_image(file_content)
            thumbnail = self._create_thumbnail(file_content)

            # 경로 설정
            image_path = f"{folder}/{filename}"
            thumb_path = f"{folder}/thumbnails/{thumb_filename}"

            # 스토리지에 업로드
            if self.storage_type == 's3':
                image_url = await self._upload_to_s3(resized_image, image_path)
                thumb_url = await self._upload_to_s3(thumbnail, thumb_path)
            elif self.storage_type == 'minio':
                image_url = await self._upload_to_minio(resized_image, image_path)
                thumb_url = await self._upload_to_minio(thumbnail, thumb_path)
            else:
                image_url = await self._upload_to_local(resized_image, image_path)
                thumb_url = await self._upload_to_local(thumbnail, thumb_path)

            logger.info(f"Image uploaded: {image_path}")

            return {
                "image_url": image_url,
                "thumbnail_url": thumb_url,
                "filename": filename,
                "size": len(resized_image)
            }

        except Exception as e:
            logger.error(f"Error uploading image: {str(e)}")
            raise

    async def _upload_to_s3(self, data: bytes, path: str) -> str:
        """S3에 업로드"""
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=path,
                Body=data,
                ContentType='image/jpeg'
            )
            return f"https://{self.bucket_name}.s3.amazonaws.com/{path}"
        except ClientError as e:
            logger.error(f"S3 upload error: {str(e)}")
            raise

    async def _upload_to_minio(self, data: bytes, path: str) -> str:
        """MinIO에 업로드"""
        try:
            self.minio_client.put_object(
                self.bucket_name,
                path,
                BytesIO(data),
                len(data),
                content_type='image/jpeg'
            )
            endpoint = getattr(settings, 'MINIO_ENDPOINT', 'localhost:9000')
            protocol = 'https' if getattr(settings, 'MINIO_SECURE', False) else 'http'
            return f"{protocol}://{endpoint}/{self.bucket_name}/{path}"
        except S3Error as e:
            logger.error(f"MinIO upload error: {str(e)}")
            raise

    async def _upload_to_local(self, data: bytes, path: str) -> str:
        """로컬에 저장"""
        try:
            full_path = os.path.join(self.local_path, path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            with open(full_path, 'wb') as f:
                f.write(data)

            return f"/uploads/{path}"
        except Exception as e:
            logger.error(f"Local storage error: {str(e)}")
            raise

    async def delete_image(self, path: str) -> bool:
        """이미지 삭제"""
        try:
            if self.storage_type == 's3':
                self.s3_client.delete_object(Bucket=self.bucket_name, Key=path)
            elif self.storage_type == 'minio':
                self.minio_client.remove_object(self.bucket_name, path)
            else:
                full_path = os.path.join(self.local_path, path)
                if os.path.exists(full_path):
                    os.remove(full_path)

            logger.info(f"Image deleted: {path}")
            return True

        except Exception as e:
            logger.error(f"Error deleting image: {str(e)}")
            return False


# 싱글톤 인스턴스
storage_service = StorageService()

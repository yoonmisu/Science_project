"""
데이터 검증 서비스
수집된 생물 데이터의 품질을 검증하고 정제합니다.
"""
import logging
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import httpx
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.species import Species

logger = logging.getLogger(__name__)


class DataValidator:
    """데이터 검증 서비스"""

    # 유효한 좌표 범위
    VALID_LAT_RANGE = (-90, 90)
    VALID_LON_RANGE = (-180, 180)

    # 유효한 카테고리
    VALID_CATEGORIES = {"식물", "동물", "곤충", "해양생물"}

    # 유효한 보전 상태
    VALID_CONSERVATION_STATUS = {"멸종위기", "취약", "준위협", "관심대상", "안전"}

    # 이미지 URL 패턴
    IMAGE_URL_PATTERN = re.compile(
        r'^https?://.*\.(jpg|jpeg|png|gif|webp|svg)(\?.*)?$',
        re.IGNORECASE
    )

    def __init__(self, db: Session):
        self.db = db
        self.validation_results = {
            "total_checked": 0,
            "valid": 0,
            "invalid": 0,
            "fixed": 0,
            "errors": []
        }

    def validate_species(self, species: Species) -> Tuple[bool, List[str]]:
        """
        개별 종 데이터 검증

        Returns:
            (is_valid, list of error messages)
        """
        errors = []

        # 필수 필드 확인
        if not species.name or len(species.name.strip()) == 0:
            errors.append("이름이 비어있습니다")

        if not species.category:
            errors.append("카테고리가 없습니다")
        elif species.category not in self.VALID_CATEGORIES:
            errors.append(f"잘못된 카테고리: {species.category}")

        if not species.country:
            errors.append("국가 정보가 없습니다")

        if not species.region:
            errors.append("지역 정보가 없습니다")

        # 좌표 검증
        if species.latitude is not None:
            if not (self.VALID_LAT_RANGE[0] <= species.latitude <= self.VALID_LAT_RANGE[1]):
                errors.append(f"잘못된 위도: {species.latitude}")

        if species.longitude is not None:
            if not (self.VALID_LON_RANGE[0] <= species.longitude <= self.VALID_LON_RANGE[1]):
                errors.append(f"잘못된 경도: {species.longitude}")

        # 보전 상태 검증
        if species.conservation_status:
            if species.conservation_status not in self.VALID_CONSERVATION_STATUS:
                errors.append(f"잘못된 보전 상태: {species.conservation_status}")

        # 이미지 URL 형식 검증
        if species.image_url:
            if not self.IMAGE_URL_PATTERN.match(species.image_url):
                errors.append(f"잘못된 이미지 URL 형식")

        return len(errors) == 0, errors

    async def check_image_url(self, url: str, timeout: float = 5.0) -> bool:
        """이미지 URL 접근 가능 여부 확인"""
        if not url:
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.head(url, timeout=timeout, follow_redirects=True)
                return response.status_code == 200
        except Exception:
            return False

    def find_duplicates(self) -> List[Dict]:
        """중복 데이터 찾기"""
        # scientific_name 기준 중복 찾기
        duplicates = self.db.query(
            Species.scientific_name,
            func.count(Species.id).label('count'),
            func.array_agg(Species.id).label('ids')
        ).filter(
            Species.scientific_name.isnot(None)
        ).group_by(
            Species.scientific_name
        ).having(
            func.count(Species.id) > 1
        ).all()

        result = []
        for dup in duplicates:
            result.append({
                "scientific_name": dup.scientific_name,
                "count": dup.count,
                "ids": dup.ids
            })

        return result

    def remove_duplicates(self, keep: str = "newest") -> int:
        """
        중복 데이터 제거

        Args:
            keep: "newest" (최신 유지) 또는 "oldest" (가장 오래된 것 유지)

        Returns:
            제거된 레코드 수
        """
        duplicates = self.find_duplicates()
        removed_count = 0

        for dup in duplicates:
            ids = sorted(dup["ids"])

            if keep == "newest":
                # 가장 큰 ID (최신) 유지, 나머지 삭제
                ids_to_delete = ids[:-1]
            else:
                # 가장 작은 ID (가장 오래된 것) 유지
                ids_to_delete = ids[1:]

            if ids_to_delete:
                self.db.query(Species).filter(
                    Species.id.in_(ids_to_delete)
                ).delete(synchronize_session=False)
                removed_count += len(ids_to_delete)

        self.db.commit()
        logger.info(f"Removed {removed_count} duplicate records")
        return removed_count

    def validate_all(self, fix_errors: bool = False) -> Dict:
        """
        전체 데이터 검증

        Args:
            fix_errors: True면 수정 가능한 오류 자동 수정

        Returns:
            검증 결과 요약
        """
        species_list = self.db.query(Species).all()
        invalid_records = []

        for species in species_list:
            self.validation_results["total_checked"] += 1
            is_valid, errors = self.validate_species(species)

            if is_valid:
                self.validation_results["valid"] += 1
            else:
                self.validation_results["invalid"] += 1
                invalid_records.append({
                    "id": species.id,
                    "name": species.name,
                    "errors": errors
                })

                if fix_errors:
                    fixed = self._fix_species(species, errors)
                    if fixed:
                        self.validation_results["fixed"] += 1

        if fix_errors:
            self.db.commit()

        self.validation_results["invalid_records"] = invalid_records[:100]  # 최대 100개만 반환
        return self.validation_results

    def _fix_species(self, species: Species, errors: List[str]) -> bool:
        """수정 가능한 오류 자동 수정"""
        fixed = False

        for error in errors:
            # 잘못된 보전 상태 수정
            if "잘못된 보전 상태" in error:
                species.conservation_status = "관심대상"
                fixed = True

            # 빈 이름 처리
            if "이름이 비어있습니다" in error and species.scientific_name:
                species.name = species.scientific_name
                fixed = True

            # 잘못된 좌표 제거
            if "잘못된 위도" in error:
                species.latitude = None
                species.location = None
                fixed = True

            if "잘못된 경도" in error:
                species.longitude = None
                species.location = None
                fixed = True

        return fixed

    def get_data_quality_report(self) -> Dict:
        """데이터 품질 보고서 생성"""
        total = self.db.query(func.count(Species.id)).scalar()

        # 필드별 완성도
        with_scientific_name = self.db.query(func.count(Species.id)).filter(
            Species.scientific_name.isnot(None)
        ).scalar()

        with_image = self.db.query(func.count(Species.id)).filter(
            Species.image_url.isnot(None)
        ).scalar()

        with_coordinates = self.db.query(func.count(Species.id)).filter(
            Species.latitude.isnot(None),
            Species.longitude.isnot(None)
        ).scalar()

        with_description = self.db.query(func.count(Species.id)).filter(
            Species.description.isnot(None),
            Species.description != ""
        ).scalar()

        # 중복 수
        duplicates = self.find_duplicates()

        return {
            "total_records": total,
            "completeness": {
                "scientific_name": {
                    "count": with_scientific_name,
                    "percentage": round(with_scientific_name / total * 100, 1) if total > 0 else 0
                },
                "image_url": {
                    "count": with_image,
                    "percentage": round(with_image / total * 100, 1) if total > 0 else 0
                },
                "coordinates": {
                    "count": with_coordinates,
                    "percentage": round(with_coordinates / total * 100, 1) if total > 0 else 0
                },
                "description": {
                    "count": with_description,
                    "percentage": round(with_description / total * 100, 1) if total > 0 else 0
                }
            },
            "duplicates": {
                "groups": len(duplicates),
                "total_duplicates": sum(d["count"] - 1 for d in duplicates)
            },
            "generated_at": datetime.utcnow().isoformat()
        }

    async def validate_images_batch(self, limit: int = 100) -> Dict:
        """이미지 URL 일괄 검증"""
        species_with_images = self.db.query(Species).filter(
            Species.image_url.isnot(None)
        ).limit(limit).all()

        results = {
            "checked": 0,
            "valid": 0,
            "invalid": [],
            "fixed": 0
        }

        for species in species_with_images:
            results["checked"] += 1
            is_valid = await self.check_image_url(species.image_url)

            if is_valid:
                results["valid"] += 1
            else:
                results["invalid"].append({
                    "id": species.id,
                    "name": species.name,
                    "url": species.image_url
                })
                # 잘못된 이미지 URL 제거
                species.image_url = None
                results["fixed"] += 1

        self.db.commit()
        return results

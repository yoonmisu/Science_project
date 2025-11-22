from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List, Dict, Any
from app.models.species import Species
from app.models.region_biodiversity import RegionBiodiversity


class SpeciesService:
    def __init__(self, db: Session):
        self.db = db

    def get_species_count_by_region(self) -> Dict[str, int]:
        """지역별 종 수 조회"""
        results = self.db.query(
            Species.region,
            func.count(Species.id).label("count")
        ).group_by(Species.region).all()

        return {r.region: r.count for r in results}

    def get_species_count_by_category(self) -> Dict[str, int]:
        """카테고리별 종 수 조회"""
        results = self.db.query(
            Species.category,
            func.count(Species.id).label("count")
        ).group_by(Species.category).all()

        return {r.category: r.count for r in results}

    def get_biodiversity_summary(self) -> Dict[str, Any]:
        """전체 생물다양성 요약"""
        total_species = self.db.query(Species).count()
        total_endangered = self.db.query(Species).filter(
            Species.is_endangered == True
        ).count()

        by_region = self.get_species_count_by_region()
        by_category = self.get_species_count_by_category()

        return {
            "total_species": total_species,
            "total_endangered": total_endangered,
            "by_region": by_region,
            "by_category": by_category
        }

    def update_region_biodiversity_stats(self, region: str) -> Optional[RegionBiodiversity]:
        """지역 생물다양성 통계 업데이트"""
        region_data = self.db.query(RegionBiodiversity).filter(
            RegionBiodiversity.region == region
        ).first()

        if not region_data:
            return None

        # 각 카테고리별 수 계산
        animal_count = self.db.query(Species).filter(
            Species.region == region, Species.category == "동물"
        ).count()

        plant_count = self.db.query(Species).filter(
            Species.region == region, Species.category == "식물"
        ).count()

        insect_count = self.db.query(Species).filter(
            Species.region == region, Species.category == "곤충"
        ).count()

        marine_count = self.db.query(Species).filter(
            Species.region == region, Species.category == "해양생물"
        ).count()

        endangered_count = self.db.query(Species).filter(
            Species.region == region, Species.is_endangered == True
        ).count()

        total_species = animal_count + plant_count + insect_count + marine_count

        # 업데이트
        region_data.animal_count = animal_count
        region_data.plant_count = plant_count
        region_data.insect_count = insect_count
        region_data.marine_count = marine_count
        region_data.endangered_count = endangered_count
        region_data.total_species = total_species

        self.db.commit()
        self.db.refresh(region_data)

        return region_data

    def search_species(
        self,
        query: str,
        category: Optional[str] = None,
        region: Optional[str] = None,
        limit: int = 20
    ) -> List[Species]:
        """종 검색"""
        from sqlalchemy import or_

        search_query = self.db.query(Species).filter(
            or_(
                Species.name.ilike(f"%{query}%"),
                Species.scientific_name.ilike(f"%{query}%")
            )
        )

        if category:
            search_query = search_query.filter(Species.category == category)
        if region:
            search_query = search_query.filter(Species.region == region)

        return search_query.limit(limit).all()

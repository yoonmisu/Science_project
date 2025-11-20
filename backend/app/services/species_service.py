from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
import redis
import json

from app.models.species import Species, CategoryEnum
from app.schemas.species import SpeciesCreate, SpeciesUpdate
from app.config import get_settings

settings = get_settings()


class SpeciesService:
    def __init__(self, db: Session):
        self.db = db
        try:
            self.redis_client = redis.from_url(settings.redis_url)
        except Exception:
            self.redis_client = None

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None,
        region: Optional[str] = None
    ) -> list[Species]:
        query = self.db.query(Species)

        if category:
            query = query.filter(Species.category == category)
        if region:
            query = query.filter(Species.region == region)

        return query.offset(skip).limit(limit).all()

    def get_by_id(self, species_id: int) -> Optional[Species]:
        # Try cache first
        if self.redis_client:
            cached = self.redis_client.get(f"species:{species_id}")
            if cached:
                return json.loads(cached)

        species = self.db.query(Species).filter(Species.id == species_id).first()

        # Cache the result
        if species and self.redis_client:
            self.redis_client.setex(
                f"species:{species_id}",
                3600,  # 1 hour TTL
                json.dumps(species.__dict__, default=str)
            )

        return species

    def create(self, species_data: SpeciesCreate) -> Species:
        species = Species(**species_data.model_dump())
        self.db.add(species)
        self.db.commit()
        self.db.refresh(species)

        # Invalidate relevant caches
        self._invalidate_caches(species.region, species.category)

        return species

    def update(self, species_id: int, species_data: SpeciesUpdate) -> Optional[Species]:
        species = self.db.query(Species).filter(Species.id == species_id).first()
        if not species:
            return None

        update_data = species_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(species, field, value)

        self.db.commit()
        self.db.refresh(species)

        # Invalidate caches
        if self.redis_client:
            self.redis_client.delete(f"species:{species_id}")
        self._invalidate_caches(species.region, species.category)

        return species

    def delete(self, species_id: int) -> bool:
        species = self.db.query(Species).filter(Species.id == species_id).first()
        if not species:
            return False

        region = species.region
        category = species.category

        self.db.delete(species)
        self.db.commit()

        # Invalidate caches
        if self.redis_client:
            self.redis_client.delete(f"species:{species_id}")
        self._invalidate_caches(region, category)

        return True

    def get_stats(self) -> dict:
        """Get overall statistics"""
        cache_key = "species:stats"

        if self.redis_client:
            cached = self.redis_client.get(cache_key)
            if cached:
                return json.loads(cached)

        total = self.db.query(func.count(Species.id)).scalar()
        endangered = self.db.query(func.count(Species.id)).filter(
            Species.is_endangered == True
        ).scalar()

        by_category = dict(
            self.db.query(Species.category, func.count(Species.id))
            .group_by(Species.category).all()
        )

        by_region = dict(
            self.db.query(Species.region, func.count(Species.id))
            .group_by(Species.region).all()
        )

        stats = {
            "total": total,
            "endangered": endangered,
            "by_category": {str(k): v for k, v in by_category.items()},
            "by_region": by_region
        }

        if self.redis_client:
            self.redis_client.setex(cache_key, 1800, json.dumps(stats))  # 30 min TTL

        return stats

    def _invalidate_caches(self, region: str, category):
        """Invalidate related caches"""
        if not self.redis_client:
            return

        # Invalidate stats cache
        self.redis_client.delete("species:stats")

        # Could add more specific cache invalidation here
        pass

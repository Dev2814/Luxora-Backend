"""
Brand Service (Business Logic Layer)
===================================

Responsibilities:
----------------
• Create brand
• Generate SEO slug
• Handle duplicates
• Apply SEO defaults

Architecture:
-------------
Routes → Service → Repository → DB
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import re

from app.models.brand import Brand
from app.domains.brands.repository import BrandRepository
from app.core.logger import log_event


class BrandService:

    def __init__(self, db: Session):
        self.db = db
        self.repo = BrandRepository(db)

    # ======================================================
    # LIST BRANDS
    # ======================================================

    def list_brands(self):
        try:
            return self.repo.get_all()

        except SQLAlchemyError as e:
            log_event("brand_list_error", level="error", error=str(e))
            raise ValueError("Unable to fetch brands")

    # ======================================================
    # SLUG GENERATOR
    # ======================================================

    def _generate_slug(self, name: str) -> str:
        """
        Convert name → SEO slug

        Example:
        "Nike Shoes" → "nike-shoes"
        """

        slug = re.sub(r'[^a-zA-Z0-9]+', '-', name.lower()).strip('-')

        base_slug = slug
        counter = 1

        while self.repo.get_by_slug(slug):
            slug = f"{base_slug}-{counter}"
            counter += 1

        return slug

    # ======================================================
    # CREATE BRAND
    # ======================================================

    def create_brand(
        self,
        name: str,
        logo_url: str | None,
        meta_title: str | None = None,
        meta_description: str | None = None
    ):
        try:

            # Duplicate check
            if self.repo.get_by_name(name):
                raise ValueError("Brand already exists")

            # Generate slug
            slug = self._generate_slug(name)

            # SEO fallback
            meta_title = meta_title or name
            meta_description = meta_description or f"Shop {name} products at best prices."

            # Create object
            brand = Brand(
                name=name,
                logo=logo_url,
                slug=slug,
                meta_title=meta_title,
                meta_description=meta_description
            )

            self.repo.create(brand)
            self.db.commit()

            log_event("brand_created", name=name, slug=slug)

            return brand

        except ValueError:
            raise

        except SQLAlchemyError as e:
            self.db.rollback()

            log_event("brand_create_error", level="error", error=str(e))
            raise ValueError("Unable to create brand")
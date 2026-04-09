"""
Brand Repository
================

Handles all DB operations.

Principles:
-----------
• NO business logic
• Pure DB access layer
• Optimized queries
"""

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.brand import Brand


class BrandRepository:

    def __init__(self, db: Session):
        self.db = db

    # ======================================================
    # GET ALL BRANDS
    # ======================================================

    def get_all(self):
        """
        Fetch all active brands.
        """

        stmt = (
            select(Brand)
            .where(Brand.is_deleted == False)
            .order_by(Brand.name.asc())
        )

        return self.db.execute(stmt).scalars().all()

    # ======================================================
    # GET BY SLUG
    # ======================================================

    def get_by_slug(self, slug: str):
        stmt = select(Brand).where(Brand.slug == slug)
        return self.db.execute(stmt).scalar_one_or_none()

    # ======================================================
    # GET BY NAME
    # ======================================================

    def get_by_name(self, name: str):
        stmt = select(Brand).where(Brand.name == name)
        return self.db.execute(stmt).scalar_one_or_none()

    # ======================================================
    # CREATE
    # ======================================================

    def create(self, brand: Brand):
        self.db.add(brand)
        self.db.flush()
        return brand
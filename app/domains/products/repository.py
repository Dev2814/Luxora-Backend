"""
Product Repository

Handles all database operations related to products.

Responsibilities:
- Product CRUD operations
- Vendor product queries
- Product lookup by slug
- Soft delete handling
- Pagination support
- Category filtering

Architecture:
    Service Layer → Repository → Database
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.product import Product


class ProductRepository:
    """
    Repository layer responsible for direct database interaction.
    """

    def __init__(self, db: Session):
        self.db = db

    # ==================================================
    # CREATE PRODUCT
    # ==================================================

    def create(self, product: Product) -> Product:
        """
        Add a new product to the database session.

        NOTE:
            Commit should be handled by the service layer.
        """
        self.db.add(product)
        return product

    # ==================================================
    # GET PRODUCT BY ID
    # ==================================================

    def get_by_id(self, product_id: int) -> Optional[Product]:
        """
        Fetch a single product by ID.
        Excludes soft-deleted products.
        """
        return (
            self.db.query(Product)
            .filter(
                Product.id == product_id,
                Product.is_deleted.is_(False)
            )
            .first()
        )

    # ==================================================
    # GET PRODUCT BY SLUG
    # ==================================================

    def get_by_slug(self, slug: str) -> Optional[Product]:
        """
        Retrieve product using SEO slug.
        Used for product detail pages.
        """
        return (
            self.db.query(Product)
            .filter(
                Product.slug == slug,
                Product.is_deleted.is_(False),
                Product.is_active.is_(True)
            )
            .first()
        )

    # ==================================================
    # LIST PRODUCTS (PAGINATION)
    # ==================================================

    def list(
        self,
        skip: int = 0,
        limit: int = 20
    ) -> List[Product]:
        """
        Retrieve paginated product list.
        """
        return (
            self.db.query(Product)
            .filter(
                Product.is_deleted.is_(False),
                Product.is_active.is_(True)
            )
            .order_by(Product.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    # ==================================================
    # LIST PRODUCTS BY CATEGORY
    # ==================================================

    def list_by_category(
        self,
        category_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> List[Product]:
        """
        Retrieve products belonging to a category.
        """
        return (
            self.db.query(Product)
            .filter(
                Product.category_id == category_id,
                Product.is_deleted.is_(False),
                Product.is_active.is_(True)
            )
            .order_by(Product.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    # ==================================================
    # LIST PRODUCTS BY VENDOR
    # ==================================================

    def list_by_vendor(
        self,
        vendor_id: int,
        skip: int = 0,
        limit: int = 50
    ) -> List[Product]:
        """
        Fetch products owned by a specific vendor.
        """
        return (
            self.db.query(Product)
            .filter(
                Product.vendor_id == vendor_id,
                Product.is_deleted.is_(False)
            )
            .order_by(Product.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    # ==================================================
    # COUNT PRODUCTS BY VENDOR
    # ==================================================

    def count_by_vendor(self, vendor_id: int) -> int:
        """
        Count total products owned by a vendor.
        Useful for analytics and pagination.
        """
        return (
            self.db.query(Product)
            .filter(
                Product.vendor_id == vendor_id,
                Product.is_deleted.is_(False)
            )
            .count()
        )

    # ==================================================
    # UPDATE PRODUCT
    # ==================================================

    def update(self, product: Product, data: dict) -> Product:
        """
        Update product fields dynamically.
        """
        allowed_fields = {
            "name",
            "description",
            "price",
            "compare_price",
            "brand_id",
            "category_id",
            "is_active"
        }

        for key, value in data.items():
            if key in allowed_fields:
                setattr(product, key, value)
                
        return product

    # ==================================================
    # SOFT DELETE PRODUCT
    # ==================================================

    def soft_delete(self, product: Product) -> Product:
        """
        Soft delete a product.
        The product remains in the database
        for auditing and analytics.
        """
        product.is_deleted = True
        return product

    # ==================================================
    # TRANSACTION HELPERS
    # ← These were missing from your actual file on disk
    # ==================================================

    def commit(self):
        """
        Commit current database transaction.
        Called by service layer after all DB operations complete.
        """
        self.db.commit()

    def rollback(self):
        """
        Rollback transaction in case of failure.
        Called by service layer inside except blocks.
        """
        self.db.rollback()
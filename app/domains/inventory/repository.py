"""
Inventory Repository
====================

Enterprise-grade repository responsible for all database
operations related to inventory management.

Responsibilities
----------------
• Create inventory records for product variants
• Retrieve inventory data
• Update stock and reservation values
• Provide vendor-scoped inventory queries
• Provide admin-level inventory visibility
• Detect low-stock items

Design Principles
----------------
• Repository pattern (data access only)
• No business logic inside repository
• Service layer controls transactions
• Supports multi-vendor marketplace architecture

Architecture
------------
Routes → Service → Repository → Database
"""

from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload

from app.models.inventory import Inventory
from app.models.product_variant import ProductVariant
from app.models.product import Product


class InventoryRepository:
    """
    Repository responsible for all direct database operations
    related to inventory records.
    """

    def __init__(self, db: Session):
        self.db = db

    # =========================================================
    # CREATE INVENTORY
    # =========================================================

    def create(self, inventory: Inventory) -> Inventory:
        """
        Persist a new inventory record.

        Each product variant must have exactly ONE inventory record.

        Example
        -------
        Variant → iPhone 15 128GB
        Inventory → stock = 100
        """

        self.db.add(inventory)
        self.db.flush()

        return inventory

    # =========================================================
    # GET INVENTORY BY VARIANT
    # =========================================================

    def get_by_variant_id(self, variant_id: int) -> Optional[Inventory]:
        """
        Retrieve inventory record for a specific product variant.
        """

        stmt = (
            select(Inventory)
            .where(Inventory.variant_id == variant_id)
        )

        return self.db.execute(stmt).scalar_one_or_none()

    # =========================================================
    # GET INVENTORY WITH VARIANT + PRODUCT
    # =========================================================

    def get_with_variant(self, variant_id: int) -> Optional[Inventory]:
        """
        Retrieve inventory along with variant and product details.

        Useful for:
        • Admin dashboards
        • Inventory analytics
        """

        stmt = (
            select(Inventory)
            .options(
                joinedload(Inventory.variant)
                .joinedload(ProductVariant.product)
            )
            .where(Inventory.variant_id == variant_id)
        )

        return self.db.execute(stmt).unique().scalar_one_or_none()

    # =========================================================
    # LIST INVENTORY (ADMIN)
    # =========================================================

    def list_all(
        self,
        skip: int = 0,
        limit: int = 50
    ) -> List[Inventory]:
        """
        Retrieve inventory across ALL vendors.

        Admin-only operation.
        """

        stmt = (
            select(Inventory)
            .options(
                joinedload(Inventory.variant)
                .joinedload(ProductVariant.product)
            )
            .offset(skip)
            .limit(limit)
        )

        result = self.db.execute(stmt).unique().scalars().all()
        return list(result)

    # =========================================================
    # LIST INVENTORY BY VENDOR
    # =========================================================

    def list_by_vendor(
        self,
        vendor_id: int,
        skip: int = 0,
        limit: int = 50
    ) -> List[Inventory]:
        """
        Retrieve inventory belonging to a specific vendor.

        Ensures vendor isolation in multi-vendor marketplaces.
        """

        stmt = (
            select(Inventory)
            .join(ProductVariant)
            .join(Product)
            .where(Product.vendor_id == vendor_id)
            .options(
                joinedload(Inventory.variant)
                .joinedload(ProductVariant.product)
                .joinedload(Product.images)
            )
            .offset(skip)
            .limit(limit)
        )

        result = self.db.execute(stmt).unique().scalars().all()
        return list(result)

    # =========================================================
    # UPDATE INVENTORY
    # =========================================================

    def update(
        self,
        inventory: Inventory,
        update_data: dict
    ) -> Inventory:
        """
        Dynamically update inventory fields.

        Example
        -------
        update(inventory, {"stock": 200})
        """

        for field, value in update_data.items():
            setattr(inventory, field, value)

        self.db.flush()

        return inventory

    # =========================================================
    # LOW STOCK ITEMS
    # =========================================================

    def get_low_stock_items(self) -> List[Inventory]:
        """
        Retrieve all inventory items that are below
        their configured low-stock threshold.

        Used for:
        • Admin monitoring
        • Vendor dashboards
        • Email alert systems
        """

        stmt = (
            select(Inventory)
            .where(Inventory.stock <= Inventory.low_stock_threshold)
            .options(
                joinedload(Inventory.variant)
                .joinedload(ProductVariant.product)
            )
        )

        result = self.db.execute(stmt).unique().scalars().all()
        return list(result)
    

    def count_low_stock_by_vendor(self, vendor_id: int) -> int:
        stmt = (
            select(func.count(Inventory.id))
            .join(ProductVariant)
            .join(Product)
            .where(
                Product.vendor_id == vendor_id,
                Inventory.stock <= Inventory.low_stock_threshold
            )
        )

        return self.db.execute(stmt).scalar() or 0

    # =========================================================
    # DELETE INVENTORY
    # =========================================================

    def delete(self, inventory: Inventory) -> None:
        """
        Permanently remove an inventory record.

        Normally triggered when a product variant is deleted.
        """

        self.db.delete(inventory)

    def get_low_stock_by_vendor(self, vendor_id: int):
        stmt = (
            select(Inventory)
            .join(ProductVariant)
            .join(Product)
            .where(
                Product.vendor_id == vendor_id,
                Inventory.stock <= Inventory.low_stock_threshold
            )
        )
        return self.db.execute(stmt).scalars().all()
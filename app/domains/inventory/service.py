"""
Inventory Service
=================

Enterprise‑grade inventory management service.

Responsibilities
----------------
• Create inventory records
• Increase stock (vendor restock)
• Decrease stock (admin adjustment / order completion)
• Reserve stock (checkout process)
• Release reserved stock (order cancellation)
• Prevent overselling
• Detect low stock alerts

Security Rules
--------------
• Vendors can only increase stock of their products
• Admins can decrease stock
• System reserves stock during checkout

Architecture
------------
Routes → Service → Repository → Database
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select

from app.models.inventory import Inventory
from app.models.product_variant import ProductVariant
from app.models.product import Product
from app.models.vendor_profile import VendorProfile

from app.domains.inventory.repository import InventoryRepository
from app.core.logger import log_event


class InventoryService:

    def __init__(self, db: Session):
        self.db = db
        self.inventory_repo = InventoryRepository(db)

    # =========================================================
    # INTERNAL LOCK (PREVENT RACE CONDITIONS)
    # =========================================================

    def _lock_inventory(self, variant_id: int) -> Inventory:
        """
        Lock inventory row to prevent concurrent updates.

        This prevents overselling when many customers
        purchase the same product simultaneously.
        """

        stmt = (
            select(Inventory)
            .where(Inventory.variant_id == variant_id)
            .with_for_update()
        )

        inventory = self.db.execute(stmt).scalar_one_or_none()

        if not inventory:
            raise ValueError("Inventory record not found")

        return inventory

    # =========================================================
    # CREATE INVENTORY (ADMIN)
    # =========================================================

    def create_inventory(
        self,
        variant_id: int,
        stock: int,
        low_stock_threshold: int
    ) -> Inventory:

        try:

            existing = self.inventory_repo.get_by_variant_id(variant_id)

            if existing:
                raise ValueError("Inventory already exists for this variant")

            inventory = Inventory(
                variant_id=variant_id,
                stock=stock,
                reserved_stock=0,
                low_stock_threshold=low_stock_threshold
            )

            self.inventory_repo.create(inventory)

            self.db.commit()
            self.db.refresh(inventory)

            log_event(
                "inventory_created",
                variant_id=variant_id,
                stock=stock
            )

            return inventory

        except SQLAlchemyError as e:

            self.db.rollback()

            log_event(
                "inventory_create_error",
                level="critical",
                error=str(e)
            )

            raise ValueError("Unable to create inventory")

    # =========================================================
    # GET INVENTORY
    # =========================================================

    def get_inventory(self, variant_id: int) -> Inventory:

        # inventory = self.inventory_repo.get_by_variant_id(variant_id)
        inventory = self.inventory_repo.get_with_variant(variant_id)

        if not inventory:
            raise ValueError("Inventory record not found")

        variant = inventory.variant
        product = variant.product

        primary_image = None
        if product.images:
            for img in product.images:
                if img.is_primary:
                    primary_image = img.image_url
                    break

        return {
            "id": inventory.id,
            "variant_id": inventory.variant_id,

            "product": {
                "id": product.id,
                "name": product.name,
                "primary_image": primary_image
            },

            "variant": {
                "name": variant.name,
                "sku": variant.sku,
                "price": float(variant.price)
            },

            "stock": inventory.stock,
            "reserved_stock": inventory.reserved_stock,
            "available_stock": inventory.available_stock,
            "low_stock_threshold": inventory.low_stock_threshold,

            "is_low_stock": inventory.available_stock <= inventory.low_stock_threshold
        }

    # =========================================================
    # INCREASE STOCK (VENDOR RESTOCK)
    # =========================================================

    def increase_stock(self, variant_id: int, quantity: int, user_id: int) -> Inventory:
        """
        Increase stock for a product variant (Vendor Restock)

        Security:
        - Ensures vendor can only modify their own products

        Concurrency:
        - Uses row-level locking to prevent race conditions
        """

        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero")

        try:
            # ---------------------------------------------------------
            # Validate vendor ownership BEFORE acquiring DB lock
            # ---------------------------------------------------------
            self._validate_vendor_access(variant_id, user_id)

            # ---------------------------------------------------------
            # Lock inventory row (critical for concurrent safety)
            # ---------------------------------------------------------
            inventory = self._lock_inventory(variant_id)

            # ---------------------------------------------------------
            # Apply stock increase
            # ---------------------------------------------------------
            inventory.stock += quantity

            # ---------------------------------------------------------
            # Persist changes
            # ---------------------------------------------------------
            self.db.commit()
            self.db.refresh(inventory)

            # ---------------------------------------------------------
            # Log audit event
            # ---------------------------------------------------------
            log_event(
                "inventory_stock_increased",
                variant_id=variant_id,
                quantity=quantity
            )

            return inventory

        except SQLAlchemyError as e:
            self.db.rollback()

            log_event(
                "inventory_increase_error",
                level="error",
                error=str(e)
            )

            raise ValueError("Unable to increase stock")
        
    def list_vendor_inventory(self, user_id: int, page: int, limit: int):
        offset = (page - 1) * limit

        # 🔥 FIX: convert user_id → vendor_id
        vendor = self.db.query(VendorProfile).filter(
            VendorProfile.user_id == user_id
        ).first()


        if not vendor:
            raise ValueError("Vendor not found")

        low_stock_count = self.inventory_repo.count_low_stock_by_vendor(vendor.id)

        items = self.inventory_repo.list_by_vendor(
            vendor.id,
            offset,
            limit
        )

        result = []

        for inv in items:
            variant = inv.variant
            product = variant.product

            # -----------------------------
            # PRIMARY IMAGE
            # -----------------------------
            primary_image = None
            if product.images:
                for img in product.images:
                    if img.is_primary:
                        primary_image = img.image_url
                        break

            result.append({
                "id": inv.id,
                "variant_id": inv.variant_id,

                "product": {
                    "id": product.id,
                    "name": product.name,
                    "primary_image": primary_image
                },

                "variant": {
                    "name": variant.name,
                    "sku": variant.sku,
                    "price": float(variant.price)
                },

                "stock": inv.stock,
                "reserved_stock": inv.reserved_stock,
                "available_stock": inv.available_stock,
                "low_stock_threshold": inv.low_stock_threshold,

                # 🔥 ADD THIS
                "is_low_stock": inv.available_stock <= inv.low_stock_threshold
            })


        return {
            "total": len(result),
            "page": page,
            "limit": limit,
            "low_stock_count": low_stock_count,
            "items": result
        }
        
    def _validate_vendor_access(self, variant_id: int, user_id: int):
        stmt = (
            select(ProductVariant)
            .join(Product)
            .where(
                ProductVariant.id == variant_id,
                Product.vendor_id == user_id
            )
        )
        variant = self.db.execute(stmt).scalar_one_or_none()

        if not variant:
            raise ValueError("Unauthorized access to this product")
        
    def get_vendor_low_stock(self, vendor_id: int):

        return self.inventory_repo.get_low_stock_by_vendor(vendor_id)

    # =========================================================
    # DECREASE STOCK (ADMIN)
    # =========================================================

    def decrease_stock(self, variant_id: int, quantity: int) -> Inventory:

        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero")

        try:

            inventory = self._lock_inventory(variant_id)

            if quantity > inventory.stock:
                raise ValueError("Insufficient stock")

            inventory.stock -= quantity

            self.db.commit()
            self.db.refresh(inventory)

            self._check_low_stock(inventory)

            log_event(
                "inventory_stock_decreased",
                variant_id=variant_id,
                quantity=quantity
            )

            return inventory

        except SQLAlchemyError as e:

            self.db.rollback()

            log_event(
                "inventory_decrease_error",
                level="error",
                error=str(e)
            )

            raise ValueError("Unable to decrease stock")

    # =========================================================
    # RESERVE STOCK (CHECKOUT)
    # =========================================================

    def reserve_stock(self, variant_id: int, quantity: int) -> Inventory:

        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero")

        try:

            inventory = self._lock_inventory(variant_id)

            available = inventory.stock - inventory.reserved_stock

            if quantity > available:
                raise ValueError("Insufficient stock")

            inventory.reserved_stock += quantity

            self.db.commit()
            self.db.refresh(inventory)

            log_event(
                "inventory_reserved",
                variant_id=variant_id,
                quantity=quantity
            )

            return inventory

        except SQLAlchemyError as e:

            self.db.rollback()

            log_event(
                "inventory_reserve_error",
                level="error",
                error=str(e)
            )

            raise ValueError("Unable to reserve stock")

    # =========================================================
    # RELEASE RESERVED STOCK
    # =========================================================

    def release_reserved_stock(self, variant_id: int, quantity: int) -> Inventory:

        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero")

        try:

            inventory = self._lock_inventory(variant_id)

            if quantity > inventory.reserved_stock:
                raise ValueError("Invalid reserved stock release")

            inventory.reserved_stock -= quantity

            self.db.commit()
            self.db.refresh(inventory)

            log_event(
                "inventory_reservation_released",
                variant_id=variant_id,
                quantity=quantity
            )

            return inventory

        except SQLAlchemyError as e:

            self.db.rollback()

            log_event(
                "inventory_release_error",
                level="error",
                error=str(e)
            )

            raise ValueError("Unable to release reserved stock")

    # =========================================================
    # LIST INVENTORY (ADMIN)
    # =========================================================

    def list_inventory(self, page: int = 1, limit: int = 20):

        offset = (page - 1) * limit

        items = self.inventory_repo.list_all(offset, limit)

        total = len(items)

        return {
            "total": total,
            "page": page,
            "limit": limit,
            "items": items
        }

    # =========================================================
    # LOW STOCK ITEMS
    # =========================================================

    def get_low_stock_items(self):

        return self.inventory_repo.get_low_stock_items()
    
    # =========================================================
    # LOW STOCK DETECTION
    # =========================================================

    def _check_low_stock(self, inventory: Inventory):

        if inventory.stock <= inventory.low_stock_threshold:

            log_event(
                "low_stock_warning",
                level="warning",
                variant_id=inventory.variant_id,
                stock=inventory.stock
            )
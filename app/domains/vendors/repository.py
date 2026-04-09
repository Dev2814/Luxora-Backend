"""
Vendor Repository

Handles all database operations related to vendors.

Responsibilities:
- Vendor profile retrieval
- Vendor creation (vendor apply)
- Vendor profile updates
- Vendor product management
- Admin vendor approval / rejection
- Vendor product pagination
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import func
from typing import Optional

from app.models.vendor_profile import VendorProfile, VendorStatus
from app.models.user import User
from app.models.product import Product
from sqlalchemy.orm import joinedload
from app.models.product_variant import ProductVariant


class VendorRepository:
    """
    Data access layer for vendor related queries.
    """

    def __init__(self, db: Session):
        self.db = db

    # ======================================================
    # CREATE VENDOR PROFILE
    # ======================================================

    def create_vendor(self, vendor: VendorProfile) -> VendorProfile:
        """
        Create vendor profile when a user applies to become a vendor.
        """

        try:
            self.db.add(vendor)
            self.db.flush()   # safer than commit inside repo
            return vendor

        except SQLAlchemyError:
            self.db.rollback()
            raise

    # ======================================================
    # GET VENDOR BY USER ID
    # ======================================================

    def get_vendor_by_user_id(self, user_id: int) -> Optional[VendorProfile]:
        """
        Fetch vendor profile using user ID.
        """

        return (
            self.db.query(VendorProfile)
            .filter(VendorProfile.user_id == user_id)
            .first()
        )

    # ======================================================
    # GET VENDOR BY ID
    # ======================================================

    def get_vendor_by_id(self, vendor_id: int) -> Optional[VendorProfile]:
        """
        Retrieve vendor profile using vendor ID.
        """

        return (
            self.db.query(VendorProfile)
            .filter(VendorProfile.id == vendor_id)
            .first()
        )

    # ======================================================
    # UPDATE VENDOR PROFILE
    # ======================================================

    def update_vendor(self, vendor: VendorProfile, data: dict) -> VendorProfile:
        """
        Update vendor profile fields.
        """

        try:

            for field, value in data.items():

                # Prevent updating protected fields
                if field in ["id", "user_id", "created_at"]:
                    continue

                setattr(vendor, field, value)

            self.db.flush()
            self.db.refresh(vendor)

            return vendor

        except SQLAlchemyError:
            self.db.rollback()
            raise

    # ======================================================
    # UPDATE USER CONTACT INFO
    # ======================================================

    def update_user_contact(
        self,
        user: User,
        email: Optional[str] = None,
        phone: Optional[str] = None
    ) -> User:
        """
        Update user contact information.
        """

        try:

            if email:
                user.email = email

            if phone:
                user.phone = phone

            self.db.flush()
            self.db.refresh(user)

            return user

        except SQLAlchemyError:
            self.db.rollback()
            raise

    # ======================================================
    # ADMIN APPROVE VENDOR
    # ======================================================

    def approve_vendor(self, vendor: VendorProfile) -> VendorProfile:
        """
        Approve vendor after admin review.
        """

        try:

            vendor.verification_status = VendorStatus.APPROVED
            vendor.verified_at = func.now()

            self.db.flush()
            self.db.refresh(vendor)

            return vendor

        except SQLAlchemyError:
            self.db.rollback()
            raise

    # ======================================================
    # ADMIN REJECT VENDOR
    # ======================================================

    def reject_vendor(
        self,
        vendor: VendorProfile,
        reason: str
    ) -> VendorProfile:
        """
        Reject vendor application.
        """

        try:

            vendor.verification_status = VendorStatus.REJECTED
            vendor.rejection_reason = reason

            self.db.flush()
            self.db.refresh(vendor)

            return vendor

        except SQLAlchemyError:
            self.db.rollback()
            raise

    # ======================================================
    # LIST VENDOR PRODUCTS (PAGINATED)
    # ======================================================


    def get_vendor_products(
        self,
        vendor_id: int,
        page: int = 1,
        limit: int = 20
    ):
        """
        Retrieve vendor products with optimized eager loading.
        """

        offset = (page - 1) * limit

        base_query = (
            self.db.query(Product)
            .options(
                # -----------------------------
                # LOAD IMAGES
                # -----------------------------
                joinedload(Product.images),

                # -----------------------------
                # LOAD VARIANTS + INVENTORY
                # -----------------------------
                joinedload(Product.variants)
                .joinedload(ProductVariant.inventory)   # IMPORTANT
            )
            .filter(
                Product.vendor_id == vendor_id,
                Product.is_deleted.is_(False)
            )
        )

        total = base_query.count()

        products = (
            base_query
            .order_by(Product.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        return {
            "total": total,
            "page": page,
            "limit": limit,
            "items": products
        }

    # ======================================================
    # GET SINGLE VENDOR PRODUCT
    # ======================================================

    def get_vendor_product(
        self,
        vendor_id: int,
        product_id: int
    ) -> Optional[Product]:
        """
        Retrieve a single vendor product.
        """

        return (
            self.db.query(Product)
            .filter(
                Product.id == product_id,
                Product.vendor_id == vendor_id,
                Product.is_deleted.is_(False)
            )
            .first()
        )

    # ======================================================
    # UPDATE PRODUCT
    # ======================================================

    def update_product(self, product: Product, data: dict) -> Product:
        """
        Update vendor product details.
        """

        try:

            for field, value in data.items():
                setattr(product, field, value)

            self.db.flush()
            self.db.refresh(product)

            return product

        except SQLAlchemyError:
            self.db.rollback()
            raise

    # ======================================================
    # SOFT DELETE PRODUCT
    # ======================================================

    def delete_product(self, product: Product) -> Product:
        """
        Soft delete vendor product.

        Responsibilities:
        - Mark product as deleted
        - Prevent duplicate delete
        - Keep transaction control in service layer
        """

        # -----------------------------
        # PREVENT DOUBLE DELETE
        # -----------------------------
        if product.is_deleted:
            raise ValueError("Product already deleted")

        # -----------------------------
        # SOFT DELETE
        # -----------------------------
        product.is_deleted = True

        # Optional (enterprise)
        # product.deleted_at = datetime.utcnow()

        # -----------------------------
        # FLUSH ONLY (NO COMMIT HERE)
        # -----------------------------
        self.db.delete(product)
        self.db.flush() 

        return product
"""
Vendor Service

Handles vendor business logic.

Responsibilities:
- Vendor onboarding (apply)
- Vendor profile retrieval
- Vendor profile updates
- Vendor product management
- Admin vendor approval / rejection
- Vendor ownership validation
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.domains.vendors.repository import VendorRepository
from app.models.vendor_profile import VendorProfile, VendorStatus
from app.models.product_attribute import ProductAttributeMap, ProductAttributeValue
from app.models.user import User, UserRole
from app.core.logger import log_event


class VendorService:
    """
    Business logic layer for vendor operations.
    """

    def __init__(self, db: Session):
        self.db = db
        self.repo = VendorRepository(db)

    # ======================================================
    # INTERNAL HELPER
    # ======================================================

    def _get_vendor_or_error(self, user_id: int) -> VendorProfile:
        """
        Ensures the user is a vendor.
        """

        vendor = self.repo.get_vendor_by_user_id(user_id)

        if not vendor:
            raise ValueError("You are not a vendor")

        return vendor

    # ======================================================
    # VENDOR APPLY
    # ======================================================

    def apply_vendor(self, user_id: int, payload):

        try:

            existing = self.repo.get_vendor_by_user_id(user_id)

            if existing:
                raise ValueError("Vendor profile already exists")

            data = payload.model_dump()

            user = self.db.query(User).filter(User.id == user_id).first()

            if not user:
                raise ValueError("User not found")

            vendor = VendorProfile(
                user_id=user_id,
                store_name=data.get("store_name"),
                store_slug=data.get("store_slug"),
                store_description=data.get("store_description"),
                business_name=data.get("business_name"),
                gst_number=data.get("gst_number"),
                business_address=data.get("business_address"),
                verification_status=VendorStatus.PENDING
            )

            created = self.repo.create_vendor(vendor)

            user.role = UserRole.VENDOR

            self.db.commit()

            log_event(
                "vendor_application_created",
                vendor_id=created.id,
                user_id=user_id
            )

            return created

        except SQLAlchemyError as e:

            self.db.rollback()

            log_event(
                "vendor_apply_error",
                level="error",
                error=str(e)
            )

            raise ValueError("Unable to submit vendor application")

    # ======================================================
    # GET VENDOR PROFILE
    # ======================================================

    def get_vendor_profile(self, user_id: int):
        """
        Retrieve vendor profile along with user contact details.
        """

        vendor = self._get_vendor_or_error(user_id)

        # ---------------------------------------------------------
        # Fetch associated user (for email & phone)
        # ---------------------------------------------------------
        user = self.db.query(User).filter(User.id == user_id).first()

        # ---------------------------------------------------------
        # Attach additional fields dynamically
        # ---------------------------------------------------------
        vendor.email = user.email if user else None
        vendor.phone = user.phone if user else None

        return vendor
    # ======================================================
    # UPDATE VENDOR PROFILE
    # ======================================================

    def update_vendor_profile(self, user_id: int, payload):

        try:

            vendor = self._get_vendor_or_error(user_id)

            data = payload.model_dump(exclude_unset=True)

            updated = self.repo.update_vendor(vendor, data)

            log_event(
                "vendor_profile_updated",
                vendor_id=vendor.id
            )

            return updated

        except SQLAlchemyError as e:

            self.db.rollback()

            log_event(
                "vendor_update_error",
                level="error",
                error=str(e)
            )

            raise ValueError("Unable to update vendor profile")

    # ======================================================
    # ADMIN APPROVE VENDOR
    # ======================================================

    def approve_vendor(self, vendor_id: int):

        vendor = self.repo.get_vendor_by_id(vendor_id)

        if not vendor:
            raise ValueError("Vendor not found")

        approved = self.repo.approve_vendor(vendor)

        log_event(
            "vendor_approved",
            vendor_id=vendor_id
        )

        return approved

    # ======================================================
    # ADMIN REJECT VENDOR
    # ======================================================

    def reject_vendor(self, vendor_id: int, reason: str):

        vendor = self.repo.get_vendor_by_id(vendor_id)

        if not vendor:
            raise ValueError("Vendor not found")

        rejected = self.repo.reject_vendor(vendor, reason)

        log_event(
            "vendor_rejected",
            vendor_id=vendor_id,
            reason=reason
        )

        return rejected

    # ======================================================
    # LIST VENDOR PRODUCTS
    # ======================================================
    
    def get_vendor_products(self, user_id: int, page: int, limit: int):
        """
        Returns vendor products with controlled response structure.
        """

        vendor = self._get_vendor_or_error(user_id)

        # Get raw data from repo
        result = self.repo.get_vendor_products(vendor.id, page, limit)

        products = result.get("items", [])
        total = result.get("total", 0)

        response_items = []

        for product in products:

            # -------------------------------
            # PRIMARY IMAGE
            # -------------------------------
            primary_image = None
            images_data = []

            for img in product.images:
                images_data.append({
                    "id": img.id,
                    "image_url": img.image_url,
                    "is_primary": img.is_primary,
                    "sort_order": img.sort_order
                })

                if img.is_primary:
                    primary_image = img.image_url

            # -------------------------------
            # VARIANTS (MINIMAL)
            # -------------------------------
            variants_data = []
            total_stock = 0

            for variant in product.variants:
                variants_data.append({
                    "id": variant.id,
                    "name": variant.name,
                    "sku": variant.sku,
                    "price": float(variant.price)
                })

                # -------------------------------
                # INVENTORY CALCULATION
                # -------------------------------
                if hasattr(variant, "inventory") and variant.inventory:
                    total_stock += variant.inventory.stock

            # -------------------------------
            # FINAL PRODUCT OBJECT
            # -------------------------------
            response_items.append({
                "id": product.id,
                "name": product.name,
                "slug": product.slug,
                "description": product.description,

                "price": float(product.price) if product.price else 0,
                "compare_price": float(product.compare_price) if product.compare_price else None,

                "brand_id": product.brand_id,
                "category_id": product.category_id,

                "status": "active" if product.is_active else "inactive",

                "primary_image": primary_image,

                "images": images_data,
                "variants": variants_data,

                "total_stock": total_stock
            })

        return {
            "total": total,
            "page": page,
            "limit": limit,
            "items": response_items
        }

    # ======================================================
    # GET SINGLE VENDOR PRODUCT
    # ======================================================

    def get_vendor_product(self, user_id: int, product_id: int):
        """
        Retrieve a single vendor product with enriched variant data.

        Includes:
        - Images
        - Variants
        - Variant Attributes
        - Inventory (stock + status)
        """

        vendor = self._get_vendor_or_error(user_id)

        product = self.repo.get_vendor_product(
            vendor.id,
            product_id
        )

        if not product:
            raise ValueError("Product not found or access denied")

        # -----------------------------
        # PRIMARY IMAGE
        # -----------------------------
        primary_image = None
        images_data = []

        for img in product.images:
            if img.is_deleted:
                continue

            images_data.append({
                "id": img.id,
                "image_url": img.image_url,
                "is_primary": img.is_primary,
                "sort_order": img.sort_order
            })

            if img.is_primary:
                primary_image = img.image_url

        # -----------------------------
        # VARIANTS (ENRICHED)
        # -----------------------------
        variants_data = []
        total_stock = 0

        for v in product.variants:
            if v.is_deleted:
                continue

            # -----------------------------
            # STOCK
            # -----------------------------
            stock = 0
            if v.inventory:
                stock = v.inventory.stock or 0
                total_stock += stock

            # -----------------------------
            # STOCK STATUS
            # -----------------------------
            if stock <= 0:
                stock_status = "out_of_stock"
            elif stock <= 5:
                stock_status = "low_stock"
            else:
                stock_status = "in_stock"

            # -----------------------------
            # ATTRIBUTES
            # -----------------------------
            attributes_data = []

            if hasattr(v, "attribute_maps") and v.attribute_maps:
                for attr_map in v.attribute_maps:

                    attr_val = attr_map.attribute_value

                    if not attr_val or attr_val.is_deleted:
                        continue

                    attributes_data.append({
                        "attribute": attr_val.attribute.name,
                        "value": attr_val.value
                    })

            # -----------------------------
            # FINAL VARIANT
            # -----------------------------
            variants_data.append({
                "id": v.id,
                "name": v.name,
                "sku": v.sku,
                "price": float(v.price),

                "attributes": attributes_data,
                "stock_status": stock_status,
                "available_stock": stock
            })

        # -----------------------------
        # FINAL RESPONSE
        # -----------------------------
        return {
            "id": product.id,
            "name": product.name,
            "slug": product.slug,
            "description": product.description,

            "price": float(product.price) if product.price else 0,
            "compare_price": float(product.compare_price) if product.compare_price else None,

            "brand_id": product.brand_id,
            "category_id": product.category_id,

            "status": "active" if product.is_active else "inactive",

            "primary_image": primary_image,

            "images": images_data,
            "variants": variants_data,

            "total_stock": total_stock
        }

    # ======================================================
    # UPDATE VENDOR PRODUCT
    # ======================================================

    def update_vendor_product(self, user_id: int, product_id: int, payload):
        """
        Enterprise-grade product update
        """

        try:
            vendor = self._get_vendor_or_error(user_id)

            product = self.repo.get_vendor_product(vendor.id, product_id)

            if not product:
                raise ValueError("Product not found or access denied")

            data = payload.model_dump(exclude_unset=True)

            # -------------------------
            # VALIDATE BRAND & CATEGORY
            # -------------------------
            from app.models.brand import Brand
            from app.models.category import Category

            if "brand_id" in data:
                if not self.db.query(Brand).filter(Brand.id == data["brand_id"]).first():
                    raise ValueError("Invalid brand_id")

            if "category_id" in data:
                if not self.db.query(Category).filter(Category.id == data["category_id"]).first():
                    raise ValueError("Invalid category_id")

            # -------------------------
            # UPDATE PRODUCT
            # -------------------------
            self.repo.update_product(product, data)

            # -------------------------
            # VARIANTS LOGIC
            # -------------------------
            if "variants" in data:

                from app.models.product_variant import ProductVariant
                from app.models.inventory import Inventory
                from app.models.product_attribute import ProductAttributeValue
                import uuid

                # DELETE REMOVED
                incoming_ids = {
                    v["id"] for v in data["variants"] if v.get("id")
                }

                for existing in product.variants:
                    if existing.id not in incoming_ids:
                        existing.is_deleted = True

                existing_variants = {v.id: v for v in product.variants}

                for v_data in data["variants"]:

                    # -------------------------
                    # UPDATE EXISTING
                    # -------------------------
                    if v_data.get("id") in existing_variants:

                        variant = existing_variants[v_data["id"]]

                        variant.name = v_data["name"]
                        variant.price = v_data["price"]

                        if variant.inventory:
                            variant.inventory.stock = v_data["stock"]

                        # ATTRIBUTES
                        self.db.query(ProductAttributeMap).filter(
                            ProductAttributeMap.variant_id == variant.id
                        ).delete(synchronize_session=False)
                        unique_attr_ids = set(v_data.get("attribute_value_ids", []))
                        for attr_id in unique_attr_ids:
                            self.db.add(ProductAttributeMap(
                                variant_id=variant.id,
                                attribute_value_id=attr_id
                            ))

                    # -------------------------
                    # CREATE NEW
                    # -------------------------
                    else:
                        new_variant = ProductVariant(
                            product_id=product.id,
                            name=v_data["name"],
                            price=v_data["price"],
                            sku=f"SKU-{product.id}-{uuid.uuid4().hex[:8].upper()}"
                        )

                        self.db.add(new_variant)
                        self.db.flush()

                        self.db.add(Inventory(
                            variant_id=new_variant.id,
                            stock=v_data["stock"]
                        ))

                        for attr_id in v_data.get("attribute_value_ids", []):
                            self.db.add(ProductAttributeMap(
                                variant_id=new_variant.id,
                                attribute_value_id=attr_id
                            ))

            # -------------------------
            # COMMIT
            # -------------------------
            self.db.commit()

            log_event(
                "vendor_product_updated",
                vendor_id=vendor.id,
                product_id=product_id
            )

            return {"message": "Product updated successfully"}

        except Exception as e:
            self.db.rollback()

            log_event(
                "vendor_product_update_failed",
                level="error",
                error=str(e),
                product_id=product_id
            )

            raise ValueError(str(e))

    # ======================================================
    # DELETE VENDOR PRODUCT
    # ======================================================

    def delete_vendor_product(self, user_id: int, product_id: int):

        vendor = self._get_vendor_or_error(user_id)

        product = self.repo.get_vendor_product(
            vendor.id,
            product_id
        )

        if not product:
            raise ValueError("Product not found or access denied")

        self.repo.delete_product(product)

        self.db.commit()
        
        log_event(
            "vendor_product_deleted",
            vendor_id=vendor.id,
            product_id=product_id
        )   

        return {
            "message": f"Product '{product.name}' deleted successfully"
        }
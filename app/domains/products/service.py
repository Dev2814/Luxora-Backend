"""
Product Service

Handles product business logic.

Architecture:
    Routes → Service → Repository → Database
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from slugify import slugify
from typing import List
import uuid

from fastapi import UploadFile

from app.models.product import Product
from app.models.product_image import ProductImage
from app.models.product_variant import ProductVariant
from app.models.product_attribute import ProductAttributeMap
from app.models.inventory import Inventory
from app.domains.products.repository import ProductRepository
from app.domains.categories.service import CategoryService
from app.core.logger import log_event
from app.core.storage import save_file          # ← same utility used in brand route


ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGES_PER_PRODUCT = 10


class ProductService:

    def __init__(self, db: Session):
        self.db = db
        self.repo = ProductRepository(db)
        self.category_service = CategoryService(db)

    def _attach_stock(self, variant):
        inventory = variant.inventory

        stock = 0
        if inventory:
            stock = inventory.stock or 0

        if stock <= 0:
            variant.stock_status = "out_of_stock"
        elif stock <= 5:
            variant.stock_status = "low_stock"
        else:
            variant.stock_status = "in_stock"

        variant.available_stock = stock
        
    # ==================================================
    # GENRATE SKU
    # ==================================================

    def _generate_sku(self, product_id: int) -> str:
        return f"SKU-{product_id}-{uuid.uuid4().hex[:8].upper()}"

    # ==================================================
    # CREATE PRODUCT
    # ==================================================

    def create_product(self, vendor_id: int, payload):

        try:
            # -----------------------------
            # GENERATE UNIQUE SLUG
            # -----------------------------
            slug = slugify(payload.name)
            existing = self.repo.get_by_slug(slug)
            if existing:
                slug = f"{slug}-{vendor_id}"

            # -----------------------------
            # VALIDATE CATEGORY
            # -----------------------------
            if payload.category_id:
                category = self.category_service.repo.get_by_id(payload.category_id)
                if not category:
                    raise ValueError("Invalid category")

            # -----------------------------
            # CREATE PRODUCT
            # -----------------------------
            product = Product(
                vendor_id=vendor_id,
                name=payload.name,
                slug=slug,
                description=payload.description,
                price=payload.price,
                compare_price=payload.compare_price,
                brand_id=payload.brand_id,
                category_id=payload.category_id,
            )

            self.repo.create(product)
            self.db.flush()

            # -----------------------------
            # VARIANTS + INVENTORY
            # -----------------------------
            if payload.variants:
                for var in payload.variants:

                    variant = ProductVariant(
                        product_id=product.id,
                        name=var.name,
                        sku=self._generate_sku(product.id),
                        price=var.price
                    )
                    self.db.add(variant)
                    self.db.flush()

                    # ✅ INVENTORY
                    inventory = Inventory(
                        variant_id=variant.id,
                        stock=var.stock or 0,
                        reserved_stock=0,
                        low_stock_threshold=5
                    )
                    self.db.add(inventory)

                    # 🔥 NEW: ATTRIBUTE MAPPING
                    if hasattr(var, "attribute_value_ids"):
                        for value_id in var.attribute_value_ids:
                            mapping = ProductAttributeMap(
                                variant_id=variant.id,
                                attribute_value_id=value_id
                            )
                            self.db.add(mapping)

            
            self.repo.commit()

            self.db.refresh(product)

            log_event("product_created", product_id=product.id, vendor_id=vendor_id)

            return self.get_product(product.id)

        except SQLAlchemyError as e:
            self.repo.rollback()
            log_event("product_create_error", level="critical", error=str(e))
            raise ValueError("Unable to create product")
        
    # ==================================================
    # UPLOAD PRODUCT IMAGES
    # ==================================================

    def upload_product_images(
        self,
        vendor_id: int,
        product_id: int,
        images: List[UploadFile]
    ):
        """
        Upload and attach multiple images to an existing product.

        Rules:
        - Vendor must own the product
        - Max 10 images per product total
        - Supported: JPEG, PNG, WEBP
        - First uploaded image becomes primary if no primary exists yet
        """
        try:
            # -----------------------------
            # FETCH + AUTHORIZE PRODUCT
            # -----------------------------
            product = self.repo.get_by_id(product_id)

            if not product:
                raise ValueError("Product not found")

            if product.vendor_id != vendor_id:
                raise ValueError("Unauthorized: you do not own this product")

            # -----------------------------
            # CHECK IMAGE COUNT LIMIT
            # -----------------------------
            existing_count = (
                self.db.query(ProductImage)
                .filter(
                    ProductImage.product_id == product_id,
                    ProductImage.is_deleted.is_(False)
                )
                .count()
            )

            if existing_count + len(images) > MAX_IMAGES_PER_PRODUCT:
                raise ValueError(
                    f"Cannot upload {len(images)} images. "
                    f"Product already has {existing_count} images. "
                    f"Max allowed: {MAX_IMAGES_PER_PRODUCT}."
                )

            # -----------------------------
            # CHECK IF PRIMARY EXISTS
            # -----------------------------
            has_primary = (
                self.db.query(ProductImage)
                .filter(
                    ProductImage.product_id == product_id,
                    ProductImage.is_primary.is_(True),
                    ProductImage.is_deleted.is_(False)
                )
                .first()
            ) is not None

            # -----------------------------
            # SAVE EACH IMAGE
            # -----------------------------
            saved_images = []

            for index, image_file in enumerate(images):

                # Validate file type
                if image_file.content_type not in ALLOWED_IMAGE_TYPES:
                    raise ValueError(
                        f"File '{image_file.filename}' has unsupported type "
                        f"'{image_file.content_type}'. Allowed: JPEG, PNG, WEBP."
                    )

                # Save to storage (same utility as brand logo)
                image_url = save_file(image_file, folder="products")

                # First image becomes primary if no primary exists yet
                is_primary = (not has_primary) and (index == 0)

                product_image = ProductImage(
                    product_id=product_id,
                    image_url=image_url,
                    is_primary=is_primary,
                    sort_order=existing_count + index,
                )

                self.db.add(product_image)
                saved_images.append(product_image)

            self.db.commit()

            for img in saved_images:
                self.db.refresh(img)

            log_event(
                "product_images_uploaded",
                product_id=product_id,
                vendor_id=vendor_id,
                count=len(saved_images)
            )

            # Return upload summary
            all_images = (
                self.db.query(ProductImage)
                .filter(
                    ProductImage.product_id == product_id,
                    ProductImage.is_deleted.is_(False)
                )
                .order_by(ProductImage.sort_order)
                .all()
            )

            return {
                "product_id": product_id,
                "uploaded_count": len(saved_images),
                "images": all_images
            }

        except SQLAlchemyError as e:
            self.db.rollback()
            log_event("product_image_upload_error", level="critical", error=str(e))
            raise ValueError("Unable to upload images")


    # ==================================================
    # GET PRODUCT
    # ==================================================

    def get_product(self, product_id: int):
        product = self.repo.get_by_id(product_id)
        if not product:
            raise ValueError("Product not found")

        # 🔥 Build structured response
        for variant in product.variants:

            self._attach_stock(variant)

            attribute_maps = (
                self.db.query(ProductAttributeMap)
                .filter(ProductAttributeMap.variant_id == variant.id)
                .all()
            )

            attributes = []
            for mapping in attribute_maps:
                value = mapping.attribute_value
                attribute = value.attribute

                attributes.append({
                    "attribute": attribute.name,
                    "value": value.value
                })

            # attach dynamically
            variant.attributes = attributes

        return product

    # ==================================================
    # UPDATE PRODUCT
    # ==================================================

    def update_product(self, vendor_id: int, product_id: int, payload):
        try:
            product = self.repo.get_by_id(product_id)

            if not product:
                raise ValueError("Product not found")

            if product.vendor_id != vendor_id:
                raise ValueError("Unauthorized product access")

            updated = self.repo.update(product, payload.model_dump(exclude_unset=True))
            self.repo.commit()

            log_event("product_updated", product_id=product_id, vendor_id=vendor_id)

            return updated

        except SQLAlchemyError as e:
            self.repo.rollback()
            log_event("product_update_error", level="error", error=str(e))
            raise ValueError("Unable to update product")


    # ==================================================
    # DELETE PRODUCT
    # ==================================================

    def delete_product(self, vendor_id: int, product_id: int):
        try:
            product = self.repo.get_by_id(product_id)

            if not product:
                raise ValueError("Product not found")

            if product.vendor_id != vendor_id:
                raise ValueError("Unauthorized product access")

            deleted = self.repo.soft_delete(product)
            self.repo.commit()

            log_event("product_deleted", product_id=product_id, vendor_id=vendor_id)

            return deleted

        except SQLAlchemyError as e:
            self.repo.rollback()
            log_event("product_delete_error", level="error", error=str(e))
            raise ValueError("Unable to delete product")


    # ==================================================
    # FILTER PRODUCTS
    # ==================================================

    def filter_products(
        self,
        category_id=None,
        brand_id=None,
        min_price=None,
        max_price=None,
        sort=None,
        page=1,
        limit=20
    ):
        query = self.db.query(Product).filter(Product.is_deleted.is_(False))

        if category_id:
            category_ids = self.category_service.get_descendant_ids(category_id)
            query = query.filter(Product.category_id.in_(category_ids))

        if brand_id:
            query = query.filter(Product.brand_id == brand_id)

        if min_price:
            query = query.filter(Product.price >= min_price)

        if max_price:
            query = query.filter(Product.price <= max_price)

        if sort == "price_low_high":
            query = query.order_by(Product.price.asc())
        elif sort == "price_high_low":
            query = query.order_by(Product.price.desc())
        elif sort == "newest":
            query = query.order_by(Product.created_at.desc())

        offset = (page - 1) * limit
        total = query.count()
        products = query.offset(offset).limit(limit).all()
        for product in products:
            for variant in product.variants:
                self._attach_stock(variant)

        return {
            "total": total,
            "page": page,
            "limit": limit,
            "items": products
        }


    # ==================================================
    # LIST PRODUCTS
    # ==================================================

    def list_products(self, page: int = 1, limit: int = 20):
        try:
            offset = (page - 1) * limit
            query = self.db.query(Product).filter(Product.is_deleted.is_(False))
            total = query.count()
            products = query.offset(offset).limit(limit).all()
            for product in products:
                for variant in product.variants:
                    self._attach_stock(variant)

            return {
                "total": total,
                "page": page,
                "limit": limit,
                "items": products
            }

        except SQLAlchemyError as e:
            log_event("product_list_error", level="error", error=str(e))
            raise ValueError("Unable to fetch products")
"""
Wishlist Service
================

Handles business logic for wishlist.

Responsibilities
----------------
• Create wishlist if not exists
• Add/remove items
• Prevent duplicates
• Validate product variant
• Return enriched wishlist data

Architecture
------------
Routes → Service → Repository → DB
"""

from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.models.wishlist import Wishlist
from app.models.wishlist_item import WishlistItem
from app.models.product_variant import ProductVariant
from app.models.product import Product

from app.domains.Wishlist.repository import WishlistRepository
from app.core.logger import log_event


class WishlistService:
    """
    Service responsible for wishlist operations.
    """

    def __init__(self, db: Session):
        self.db = db
        self.repo = WishlistRepository(db)

    # ======================================================
    # INTERNAL — GET OR CREATE WISHLIST
    # ======================================================

    def _get_or_create_wishlist(self, user_id: int) -> Wishlist:
        """
        Retrieve existing wishlist or create new one.
        """

        wishlist = self.repo.get_by_user_id(user_id)

        if not wishlist:
            wishlist = Wishlist(user_id=user_id)
            self.repo.create(wishlist)

        return wishlist

    # ======================================================
    # ADD TO WISHLIST
    # ======================================================

    def add_to_wishlist(self, user_id: int, variant_id: int):
        """
        Add product variant to wishlist.
        """

        try:

            # Validate variant (modern query)
            variant = self.db.execute(
                select(ProductVariant).where(ProductVariant.id == variant_id)
            ).unique().scalar_one_or_none()

            if not variant:
                raise ValueError("Product variant not found")

            wishlist = self._get_or_create_wishlist(user_id)

            # Prevent duplicate
            existing = self.repo.get_item(wishlist.id, variant_id)

            if existing:
                return {"message": "Already in wishlist"}

            item = WishlistItem(
                wishlist_id=wishlist.id,
                variant_id=variant_id
            )

            self.repo.add_item(item)

            self.db.commit()

            log_event(
                "wishlist_item_added",
                user_id=user_id,
                variant_id=variant_id
            )

            return {"message": "Added to wishlist"}

        except ValueError:
            raise

        except SQLAlchemyError as e:

            self.db.rollback()

            log_event(
                "wishlist_add_error",
                level="error",
                error=str(e)
            )

            raise ValueError("Unable to add item")

    # ======================================================
    # REMOVE FROM WISHLIST
    # ======================================================

    def remove_from_wishlist(self, user_id: int, variant_id: int):
        """
        Remove item from wishlist.
        """

        try:

            wishlist = self.repo.get_by_user_id(user_id)

            if not wishlist:
                raise ValueError("Wishlist not found")

            item = self.repo.get_item(wishlist.id, variant_id)

            if not item:
                raise ValueError("Item not found")

            self.repo.remove_item(item)

            self.db.commit()

            log_event(
                "wishlist_item_removed",
                user_id=user_id,
                variant_id=variant_id
            )

            return {"message": "Removed from wishlist"}

        except ValueError:
            raise

        except SQLAlchemyError as e:

            self.db.rollback()

            log_event(
                "wishlist_remove_error",
                level="error",
                error=str(e)
            )

            raise ValueError("Unable to remove item")

    # ======================================================
    # GET WISHLIST (OPTIMIZED)
    # ======================================================

    def get_wishlist(self, user_id: int):
        """
        Optimized wishlist fetch.

        Features:
        • No N+1 queries
        • Includes product + image + stock
        • Schema-aligned response
        """

        try:

            wishlist = self.repo.get_by_user_id(user_id)

            if not wishlist:
                return {
                    "items": [],
                    "total_items": 0
                }

            stmt = (
                select(WishlistItem)
                .where(WishlistItem.wishlist_id == wishlist.id)
                .options(
                    # Variant + Product
                    joinedload(WishlistItem.variant)
                    .joinedload(ProductVariant.product)
                    .selectinload(Product.images),

                    # Inventory
                    joinedload(WishlistItem.variant)
                    .joinedload(ProductVariant.inventory)
                )
            )

            items = self.db.execute(stmt).unique().scalars().all()

            response_items = []

            for item in items:

                variant = item.variant
                product = variant.product

                # -------------------------------
                # IMAGE RESOLUTION
                # -------------------------------
                image_url = None

                if product.images:
                    image_url = next(
                        (img.image_url for img in product.images if img.is_primary),
                        product.images[0].image_url
                    )

                # -------------------------------
                # STOCK CHECK
                # -------------------------------
                is_in_stock = (
                    variant.inventory.available_stock > 0
                    if variant.inventory and variant.inventory.available_stock is not None
                    else False
                )

                # ===============================
                # ✅ NEW: GET ATTRIBUTES
                # ===============================
                attributes = []

                if variant.attribute_values:
                    for attr_value in variant.attribute_values:
                        attributes.append({
                            "attribute": attr_value.attribute.name,
                            "value": attr_value.value
                        })

                # -------------------------------
                # BUILD RESPONSE
                # -------------------------------
                response_items.append({
                    "id": item.id,
                    "variant_id": variant.id,
                    "product_id": product.id,
                    "product_name": product.name,
                    "price": float(variant.price),
                    "compare_price": float(product.compare_price) if getattr(product, "compare_price", None) else None,
                    "image": image_url,
                    "attributes": attributes, 
                    "created_at": item.created_at,
                    "is_in_stock": is_in_stock
                })

            return {
                "items": response_items,
                "total_items": len(response_items)
            }

        except Exception as e:

            log_event(
                "wishlist_fetch_error",
                level="error",
                error=str(e)
            )

            raise ValueError("Unable to fetch wishlist")
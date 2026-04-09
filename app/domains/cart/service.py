"""
Cart Service
============

Handles business logic for customer shopping cart.

Responsibilities
----------------
• Create cart automatically for user
• Add items to cart
• Update item quantity
• Remove item from cart
• Retrieve cart items
• Clear cart
• Validate inventory availability

Design Principles
-----------------
• Business logic only
• Repository handles DB operations
• Service manages transactions
• Logging and error handling

Architecture
------------
Routes → Service → Repository → Database
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.inventory import Inventory
from app.models.product_variant import ProductVariant
from app.models.product import Product
from app.models.product_attribute import ProductAttributeValue

from app.domains.cart.repository import CartRepository
from app.core.logger import log_event
from sqlalchemy.orm import joinedload, selectinload

MAX_CART_QUANTITY = 10

class CartService:
    """
    Business logic layer for cart operations.
    """

    def __init__(self, db: Session):
        self.db = db
        self.repo = CartRepository(db)

    # ======================================================
    # GET OR CREATE CART
    # ======================================================

    def get_or_create_cart(self, user_id: int) -> Cart:
        """
        Retrieve cart for user or create one if it doesn't exist.
        """

        cart = self.repo.get_cart_by_user(user_id)

        if not cart:
            cart = Cart(user_id=user_id)
            cart = self.repo.create_cart(cart)

            self.db.commit()
            self.db.refresh(cart)

            log_event(
                "cart_created",
                user_id=user_id,
                cart_id=cart.id
            )

        return cart

    # ======================================================
    # GET CART ITEMS
    # ======================================================

    def get_cart_items(self, user_id: int):

        cart = self.get_or_create_cart(user_id)

        # ===============================
        # OPTIMIZED QUERY (NO N+1)
        # ===============================
        items = (
            self.db.query(CartItem)
            .filter(CartItem.cart_id == cart.id)
            .options(
                joinedload(CartItem.variant)
                .joinedload(ProductVariant.product)
                .selectinload(Product.images),

                joinedload(CartItem.variant)
                .selectinload(ProductVariant.attribute_values)
                .joinedload(ProductAttributeValue.attribute)
            )
            .all()
        )

        response = []

        for item in items:

            variant = item.variant
            product = variant.product

            # -------------------------------
            # IMAGE
            # -------------------------------
            image_url = None
            if product.images:
                image_url = next(
                    (img.image_url for img in product.images if img.is_primary),
                    product.images[0].image_url
                )

            # -------------------------------
            # ATTRIBUTES
            # -------------------------------
            attributes = []
            if variant.attribute_values:
                for val in variant.attribute_values:
                    attributes.append({
                        "attribute": val.attribute.name,
                        "value": val.value
                    })

            # -------------------------------
            # RESPONSE
            # -------------------------------
            response.append({
                "id": item.id,
                "cart_id": item.cart_id,
                "variant_id": variant.id,
                "quantity": item.quantity,

                "product_id": product.id,
                "product_name": product.name,
                "price": float(variant.price),
                "compare_price": float(product.compare_price) if product.compare_price else None,
                "image": image_url,
                "attributes": attributes
            })

        return response

    # ======================================================
    # ADD ITEM TO CART
    # ======================================================

    def add_item(self, user_id: int, variant_id: int, quantity: int):

        try:

            cart = self.get_or_create_cart(user_id)

            # -------------------------------
            # INVENTORY
            # -------------------------------
            inventory = (
                self.db.query(Inventory)
                .filter(Inventory.variant_id == variant_id)
                .one_or_none()
            )

            if not inventory:
                raise ValueError("Inventory not found")

            available_stock = inventory.available_stock

            # ❌ OUT OF STOCK
            if available_stock <= 0:
                raise ValueError("Product is out of stock")

            # -------------------------------
            # LIMIT QUANTITY
            # -------------------------------
            if quantity > available_stock:
                quantity = available_stock

            if quantity > MAX_CART_QUANTITY:
                quantity = MAX_CART_QUANTITY

            # -------------------------------
            # CHECK EXISTING ITEM
            # -------------------------------
            item = self.repo.get_item_by_variant(cart.id, variant_id)

            if item:
                new_quantity = item.quantity + quantity

                # limit by stock
                if new_quantity > available_stock:
                    new_quantity = available_stock

                # limit by max cart
                if new_quantity > MAX_CART_QUANTITY:
                    new_quantity = MAX_CART_QUANTITY

                item = self.repo.update_item(
                    item,
                    {"quantity": new_quantity}
                )

            else:
                item = CartItem(
                    cart_id=cart.id,
                    variant_id=variant_id,
                    quantity=quantity
                )

                item = self.repo.add_item(item)

            self.db.commit()
            self.db.refresh(item)

            return item

        except SQLAlchemyError as e:
            self.db.rollback()
            raise ValueError("Unable to add item to cart")
        
    # ======================================================
    # UPDATE ITEM QUANTITY
    # ======================================================

    def update_item(self, user_id: int, variant_id: int, quantity: int):

        try:

            cart = self.get_or_create_cart(user_id)

            item = self.repo.get_item_by_variant(cart.id, variant_id)

            if not item:
                raise ValueError("Item not found in cart")

            # -------------------------------
            # INVENTORY
            # -------------------------------
            inventory = (
                self.db.query(Inventory)
                .filter(Inventory.variant_id == variant_id)
                .one_or_none()
            )

            if not inventory:
                raise ValueError("Inventory not found")

            available_stock = inventory.available_stock

            # ❌ OUT OF STOCK
            if available_stock <= 0:
                raise ValueError("Product is out of stock")

            # -------------------------------
            # LIMIT QUANTITY
            # -------------------------------
            if quantity > available_stock:
                quantity = available_stock

            if quantity > MAX_CART_QUANTITY:
                quantity = MAX_CART_QUANTITY

            # ❌ ZERO SAFETY
            if quantity <= 0:
                raise ValueError("Invalid quantity")

            item = self.repo.update_item(
                item,
                {"quantity": quantity}
            )

            self.db.commit()
            self.db.refresh(item)

            return item

        except SQLAlchemyError as e:
            self.db.rollback()
            raise ValueError("Unable to update cart item")
        
    # ======================================================
    # REMOVE ITEM FROM CART
    # ======================================================

    # def remove_item(self, user_id: int, variant_id: int):

    #     try:

    #         cart = self.get_or_create_cart(user_id)

    #         item = self.repo.get_item_by_variant(cart.id, variant_id)

    #         if not item:
    #             raise ValueError("Item not found in cart")

    #         self.repo.delete_item(item)

    #         self.db.commit()

    #         log_event(
    #             "cart_item_removed",
    #             user_id=user_id,
    #             variant_id=variant_id
    #         )

    #         return True

    #     except SQLAlchemyError as e:

    #         self.db.rollback()

    #         log_event(
    #             "cart_remove_error",
    #             level="error",
    #             error=str(e)
    #         )

    #         raise ValueError("Unable to remove item from cart")
        
    
    def remove_item_by_id(self, user_id: int, item_id: int):

        cart = self.get_or_create_cart(user_id)

        item = (
            self.db.query(CartItem)
            .filter(
                CartItem.id == item_id,
                CartItem.cart_id == cart.id
            )
            .one_or_none()
        )

        if not item:
            raise ValueError("Item not found")

        self.repo.delete_item(item)

        self.db.commit()

        log_event(
            "cart_item_removed",
            user_id=user_id,
            item_id=item_id
        )

        return True

    # ======================================================
    # CLEAR CART
    # ======================================================

    def clear_cart(self, user_id: int):

        try:

            cart = self.get_or_create_cart(user_id)

            self.repo.clear_cart(cart.id)

            self.db.commit()

            log_event(
                "cart_cleared",
                user_id=user_id
            )

            return True

        except SQLAlchemyError as e:

            self.db.rollback()

            log_event(
                "cart_clear_error",
                level="error",
                error=str(e)
            )

            raise ValueError("Unable to clear cart")
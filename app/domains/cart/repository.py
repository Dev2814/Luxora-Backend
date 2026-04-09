"""
Cart Repository
===============

Handles all database operations related to the shopping cart.

Responsibilities
----------------
• Create a cart
• Retrieve cart by user
• Retrieve cart items
• Add items to cart
• Update cart item quantity
• Remove items from cart
• Clear cart

Design Principles
-----------------
• Repository pattern
• No business logic
• Service layer controls transactions

Architecture
------------
Routes → Service → Repository → Database
"""

from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.cart import Cart
from app.models.cart_item import CartItem


class CartRepository:
    """
    Repository responsible for database operations
    related to carts and cart items.
    """

    def __init__(self, db: Session):
        self.db = db

    # ======================================================
    # CREATE CART
    # ======================================================

    def create_cart(self, cart: Cart) -> Cart:
        """
        Create a new cart for a user.
        """

        self.db.add(cart)
        self.db.flush()

        return cart

    # ======================================================
    # GET CART BY USER
    # ======================================================

    def get_cart_by_user(self, user_id: int) -> Optional[Cart]:
        """
        Retrieve cart associated with a user.
        """

        stmt = (
            select(Cart)
            .where(Cart.user_id == user_id)
        )

        return self.db.execute(stmt).scalar_one_or_none()

    # ======================================================
    # GET CART ITEMS
    # ======================================================

    def get_cart_items(self, cart_id: int) -> List[CartItem]:
        """
        Retrieve all items inside a cart.
        """

        stmt = (
            select(CartItem)
            .where(CartItem.cart_id == cart_id)
        )

        return list(self.db.execute(stmt).scalars().all())

    # ======================================================
    # GET CART ITEM BY VARIANT
    # ======================================================

    def get_item_by_variant(
        self,
        cart_id: int,
        variant_id: int
    ) -> Optional[CartItem]:
        """
        Retrieve cart item by variant.
        Used to prevent duplicate cart items.
        """

        stmt = (
            select(CartItem)
            .where(
                CartItem.cart_id == cart_id,
                CartItem.variant_id == variant_id
            )
        )

        return self.db.execute(stmt).scalar_one_or_none()

    # ======================================================
    # ADD ITEM
    # ======================================================

    def add_item(self, item: CartItem) -> CartItem:
        """
        Add a new item to cart.
        """

        self.db.add(item)
        self.db.flush()

        return item

    # ======================================================
    # UPDATE ITEM
    # ======================================================

    def update_item(
        self,
        item: CartItem,
        update_data: dict
    ) -> CartItem:
        """
        Update cart item fields dynamically.
        """

        for field, value in update_data.items():
            setattr(item, field, value)

        self.db.flush()

        return item

    # ======================================================
    # DELETE ITEM
    # ======================================================

    def delete_item(self, item: CartItem) -> None:
        """
        Remove item from cart.
        """

        self.db.delete(item)

    # ======================================================
    # CLEAR CART
    # ======================================================

    def clear_cart(self, cart_id: int):
        """
        Remove all items from cart.
        """

        stmt = (
            select(CartItem)
            .where(CartItem.cart_id == cart_id)
        )

        items = self.db.execute(stmt).scalars().all()

        for item in items:
            self.db.delete(item)
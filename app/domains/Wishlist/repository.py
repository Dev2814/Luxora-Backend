"""
Wishlist Repository
===================

Handles all database operations related to wishlist.

Design:
• Pure DB layer
• No business logic
• Safe for eager loading
"""

from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.wishlist import Wishlist
from app.models.wishlist_item import WishlistItem


class WishlistRepository:
    def __init__(self, db: Session):
        self.db = db

    # ======================================================
    # GET WISHLIST BY USER
    # ======================================================

    def get_by_user_id(self, user_id: int) -> Optional[Wishlist]:

        stmt = (
            select(Wishlist)
            .where(Wishlist.user_id == user_id)
        )

        return self.db.execute(stmt).unique().scalar_one_or_none()

    # ======================================================
    # CREATE
    # ======================================================

    def create(self, wishlist: Wishlist) -> Wishlist:

        self.db.add(wishlist)
        self.db.flush()
        return wishlist

    # ======================================================
    # GET ITEM
    # ======================================================

    def get_item(
        self,
        wishlist_id: int,
        variant_id: int
    ) -> Optional[WishlistItem]:

        stmt = (
            select(WishlistItem)
            .where(
                WishlistItem.wishlist_id == wishlist_id,
                WishlistItem.variant_id == variant_id
            )
            # 🔥 CRITICAL FIX → avoid implicit eager loading issues
            .execution_options(populate_existing=True)
        )

        return self.db.execute(stmt).unique().scalar_one_or_none()

    # ======================================================
    # ADD ITEM
    # ======================================================

    def add_item(self, item: WishlistItem) -> WishlistItem:

        self.db.add(item)
        self.db.flush()
        return item

    # ======================================================
    # REMOVE ITEM
    # ======================================================

    def remove_item(self, item: WishlistItem) -> None:

        self.db.delete(item)
        self.db.flush()

    # ======================================================
    # GET ALL ITEMS
    # ======================================================

    def get_items(self, wishlist_id: int) -> List[WishlistItem]:

        stmt = (
            select(WishlistItem)
            .where(WishlistItem.wishlist_id == wishlist_id)
            # 🔥 avoid duplicate row explosion
            .execution_options(populate_existing=True)
        )

        return self.db.execute(stmt).unique().scalars().all()
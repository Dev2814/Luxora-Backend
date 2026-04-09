"""
User Address Repository
=======================

Handles all database operations related to user addresses.

Responsibilities
----------------
• Create new addresses
• Retrieve addresses for a user
• Retrieve a specific address
• Update address information
• Delete addresses

Design Principles
-----------------
• Repository pattern
• No business logic inside repository
• Service layer manages transactions

Architecture
------------
Routes → Service → Repository → Database
"""

from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.user_address import UserAddress


class AddressRepository:
    """
    Repository responsible for direct database
    operations related to user addresses.
    """

    def __init__(self, db: Session):
        self.db = db

    # =========================================================
    # CREATE ADDRESS
    # =========================================================

    def create(self, address: UserAddress) -> UserAddress:
        """
        Persist a new user address.
        """

        self.db.add(address)
        self.db.flush()

        return address

    # =========================================================
    # GET ADDRESS BY ID
    # =========================================================

    def get_by_id(self, address_id: int) -> Optional[UserAddress]:
        """
        Retrieve a specific address by primary key.
        """

        stmt = (
            select(UserAddress)
            .where(UserAddress.id == address_id)
        )

        return self.db.execute(stmt).scalar_one_or_none()

    # =========================================================
    # GET ADDRESSES BY USER
    # =========================================================

    def get_by_user_id(self, user_id: int) -> List[UserAddress]:
        """
        Retrieve all addresses belonging to a user.
        """

        stmt = (
            select(UserAddress)
            .where(UserAddress.user_id == user_id)
        )

        return list(self.db.execute(stmt).scalars().all())

    # =========================================================
    # UPDATE ADDRESS
    # =========================================================

    def update(
        self,
        address: UserAddress,
        update_data: dict
    ) -> UserAddress:
        """
        Dynamically update address fields.
        """

        for field, value in update_data.items():
            setattr(address, field, value)

        self.db.flush()

        return address

    # =========================================================
    # DELETE ADDRESS
    # =========================================================

    def delete(self, address: UserAddress) -> None:
        """
        Permanently remove an address.
        """

        self.db.delete(address)

    # =========================================================
    # CLEAR DEFAULT ADDRESS
    # =========================================================

    def clear_default(self, user_id: int):
        """
        Remove default flag from existing addresses
        when a new default address is set.
        """

        stmt = (
            select(UserAddress)
            .where(
                UserAddress.user_id == user_id,
                UserAddress.is_default == True
            )
        )

        addresses = self.db.execute(stmt).scalars().all()

        for addr in addresses:
            addr.is_default = False

        self.db.flush()
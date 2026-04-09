"""
User Address Service
====================

Handles business logic for user address management.

Responsibilities
----------------
• Create new address
• Retrieve user addresses
• Update address
• Delete address
• Manage default address logic

Design Principles
-----------------
• Business logic only
• Repository handles database operations
• Service manages transactions
• Proper logging for errors and events

Architecture
------------
Routes → Service → Repository → Database
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.user_address import UserAddress
from app.domains.addresses.repository import AddressRepository
from app.core.logger import log_event


class AddressService:
    """
    Business logic layer for user address operations.
    """

    def __init__(self, db: Session):
        self.db = db
        self.repo = AddressRepository(db)

    # =========================================================
    # CREATE ADDRESS
    # =========================================================

    def create_address(self, user_id: int, payload):

        try:

            data = payload.model_dump()

            # If new address is default → remove previous default
            if data.get("is_default"):
                self.repo.clear_default(user_id)

            address = UserAddress(
                user_id=user_id,
                label=data.get("label"),
                full_name=data.get("full_name"),
                phone_number=data.get("phone_number"),
                address_line1=data.get("address_line1"),
                address_line2=data.get("address_line2"),
                city=data.get("city"),
                state=data.get("state"),
                postal_code=data.get("postal_code"),
                country=data.get("country"),
                is_default=data.get("is_default", False)
            )

            created = self.repo.create(address)

            self.db.commit()
            self.db.refresh(created)

            log_event(
                "address_created",
                user_id=user_id,
                address_id=created.id
            )

            return created

        except SQLAlchemyError as e:

            self.db.rollback()

            log_event(
                "address_create_error",
                level="error",
                error=str(e)
            )

            raise ValueError("Unable to create address")

    # =========================================================
    # GET USER ADDRESSES
    # =========================================================

    def get_user_addresses(self, user_id: int):

        addresses = self.repo.get_by_user_id(user_id)

        return addresses

    # =========================================================
    # GET SINGLE ADDRESS
    # =========================================================

    def get_address(self, user_id: int, address_id: int):

        address = self.repo.get_by_id(address_id)

        if not address or address.user_id != user_id:
            raise ValueError("Address not found")

        return address

    # =========================================================
    # UPDATE ADDRESS
    # =========================================================

    def update_address(self, user_id: int, address_id: int, payload):

        try:

            address = self.repo.get_by_id(address_id)

            if not address or address.user_id != user_id:
                raise ValueError("Address not found")

            update_data = payload.model_dump(exclude_unset=True)

            # If setting new default address
            if update_data.get("is_default"):
                self.repo.clear_default(user_id)

            updated = self.repo.update(address, update_data)

            self.db.commit()
            self.db.refresh(updated)

            log_event(
                "address_updated",
                user_id=user_id,
                address_id=address_id
            )

            return updated

        except SQLAlchemyError as e:

            self.db.rollback()

            log_event(
                "address_update_error",
                level="error",
                error=str(e)
            )

            raise ValueError("Unable to update address")

    # =========================================================
    # DELETE ADDRESS
    # =========================================================

    def delete_address(self, user_id: int, address_id: int):

        try:

            address = self.repo.get_by_id(address_id)

            if not address or address.user_id != user_id:
                raise ValueError("Address not found")

            was_default = address.is_default

            # Delete address
            self.repo.delete(address)
            self.db.flush()

            # -------------------------------------------------
            # If deleted address was default → assign new one
            # -------------------------------------------------

            if was_default:

                remaining = self.repo.get_by_user_id(user_id)

                if remaining:
                    remaining[0].is_default = True

            self.db.commit()

            log_event(
                "address_deleted",
                user_id=user_id,
                address_id=address_id
            )

            return True

        except SQLAlchemyError as e:

            self.db.rollback()

            log_event(
                "address_delete_error",
                level="error",
                error=str(e)
            )

            raise ValueError("Unable to delete address")
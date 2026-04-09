"""
Customer Service
================

Handles all business logic related to customer profiles.

Responsibilities
----------------
• Customer profile creation
• Retrieve customer profile
• Update customer information
• Prevent duplicate profiles
• Provide admin-level customer listing

Design Principles
----------------
• Business logic layer only
• Repository handles database operations
• Service manages transactions
• Proper error logging

Architecture
------------
Routes → Service → Repository → Database
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.customer_profile import CustomerProfile
from app.domains.customers.repository import CustomerRepository
from app.core.logger import log_event


class CustomerService:
    """
    Business logic layer responsible for customer profile operations.
    """

    def __init__(self, db: Session):
        self.db = db
        self.repo = CustomerRepository(db)

    # =========================================================
    # CREATE CUSTOMER PROFILE
    # =========================================================

    def create_customer_profile(self, user_id: int, payload):
        """
        Create a customer profile for a user.

        Ensures that each user can only have one profile.
        """

        try:

            existing = self.repo.get_by_user_id(user_id)

            if existing:
                raise ValueError("Customer profile already exists")

            data = payload.model_dump()

            customer = CustomerProfile(
                user_id=user_id,
                full_name=data.get("full_name"),
                gender=data.get("gender"),
                date_of_birth=data.get("date_of_birth")
            )

            created = self.repo.create(customer)

            self.db.commit()
            self.db.refresh(created)

            log_event(
                "customer_profile_created",
                customer_id=created.id,
                user_id=user_id
            )

            return created

        except SQLAlchemyError as e:

            self.db.rollback()

            log_event(
                "customer_create_error",
                level="error",
                error=str(e)
            )

            raise ValueError("Unable to create customer profile")

    # =========================================================
    # GET CUSTOMER PROFILE
    # =========================================================

    def get_customer_profile(self, user_id: int):
        """
        Retrieve customer profile using user ID.
        """

        customer = self.repo.get_by_user_id(user_id)

        if not customer:
            raise ValueError("Customer profile not found")

        return customer

    # =========================================================
    # UPDATE CUSTOMER PROFILE
    # =========================================================

    def update_customer_profile(self, user_id: int, payload):
        """
        Update customer profile information.
        """

        try:

            customer = self.repo.get_by_user_id(user_id)

            if not customer:
                raise ValueError("Customer profile not found")

            update_data = payload.model_dump(exclude_unset=True)

            updated = self.repo.update(customer, update_data)

            self.db.commit()
            self.db.refresh(updated)

            log_event(
                "customer_profile_updated",
                customer_id=customer.id,
                user_id=user_id
            )

            return updated

        except SQLAlchemyError as e:

            self.db.rollback()

            log_event(
                "customer_update_error",
                level="error",
                error=str(e)
            )

            raise ValueError("Unable to update customer profile")

    # =========================================================
    # LIST CUSTOMERS (ADMIN)
    # =========================================================

    def list_customers(self, page: int = 1, limit: int = 20):
        """
        Retrieve paginated list of customers.

        Used for admin dashboards and analytics.
        """

        try:

            skip = (page - 1) * limit

            customers = self.repo.list_customers(skip, limit)

            return {
                "total": len(customers),
                "page": page,
                "limit": limit,
                "items": customers
            }

        except SQLAlchemyError as e:

            log_event(
                "customer_list_error",
                level="error",
                error=str(e)
            )

            raise ValueError("Unable to fetch customers")

    # =========================================================
    # DELETE CUSTOMER PROFILE
    # =========================================================

    def delete_customer_profile(self, user_id: int):
        """
        Remove customer profile.

        Normally used by admin systems.
        """

        try:

            customer = self.repo.get_by_user_id(user_id)

            if not customer:
                raise ValueError("Customer profile not found")

            self.repo.delete(customer)

            self.db.commit()

            log_event(
                "customer_profile_deleted",
                customer_id=customer.id,
                user_id=user_id
            )

            return True

        except SQLAlchemyError as e:

            self.db.rollback()

            log_event(
                "customer_delete_error",
                level="error",
                error=str(e)
            )

            raise ValueError("Unable to delete customer profile")
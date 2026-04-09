"""
Customer Repository
===================

Handles all database operations related to CustomerProfile.

Responsibilities
----------------
• Create customer profiles
• Retrieve customer profiles
• Update customer data
• Delete customer profiles
• Provide admin-level listing

Design Principles
-----------------
• Repository pattern
• No business logic
• Service layer manages transactions

Architecture
------------
API → Service → Repository → Database
"""

from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.customer_profile import CustomerProfile


class CustomerRepository:
    """
    Repository responsible for all direct database
    interactions related to CustomerProfile.
    """

    def __init__(self, db: Session):
        self.db = db

    # ======================================================
    # CREATE CUSTOMER PROFILE
    # ======================================================

    def create(self, customer: CustomerProfile) -> CustomerProfile:
        """
        Persist a new customer profile.

        Called during customer onboarding.
        """

        self.db.add(customer)
        self.db.flush()

        return customer

    # ======================================================
    # GET CUSTOMER BY USER ID
    # ======================================================

    def get_by_user_id(self, user_id: int) -> Optional[CustomerProfile]:
        """
        Retrieve a customer profile using the associated user ID.
        """

        stmt = (
            select(CustomerProfile)
            .where(CustomerProfile.user_id == user_id)
        )

        return self.db.execute(stmt).scalar_one_or_none()

    # ======================================================
    # GET CUSTOMER BY ID
    # ======================================================

    def get_by_id(self, customer_id: int) -> Optional[CustomerProfile]:
        """
        Retrieve customer profile using primary key.
        """

        stmt = (
            select(CustomerProfile)
            .where(CustomerProfile.id == customer_id)
        )

        return self.db.execute(stmt).scalar_one_or_none()

    # ======================================================
    # UPDATE CUSTOMER PROFILE
    # ======================================================

    def update(
        self,
        customer: CustomerProfile,
        update_data: dict
    ) -> CustomerProfile:
        """
        Dynamically update customer profile fields.
        """

        for field, value in update_data.items():
            setattr(customer, field, value)

        self.db.flush()

        return customer

    # ======================================================
    # LIST CUSTOMERS (ADMIN USE)
    # ======================================================

    def list_customers(
        self,
        skip: int = 0,
        limit: int = 50
    ) -> List[CustomerProfile]:
        """
        Retrieve paginated list of customers.

        Used for:
        • Admin dashboards
        • Analytics
        """

        stmt = (
            select(CustomerProfile)
            .offset(skip)
            .limit(limit)
        )

        return list(self.db.execute(stmt).scalars().all())

    # ======================================================
    # DELETE CUSTOMER PROFILE
    # ======================================================

    def delete(self, customer: CustomerProfile) -> None:
        """
        Permanently remove a customer profile.
        """

        self.db.delete(customer)
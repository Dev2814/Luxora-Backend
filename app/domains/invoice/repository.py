"""
Invoice Repository
==================

Handles all database operations related to invoices.

Responsibilities:
-----------------
• Create invoice records
• Fetch invoice by order
• Fetch invoices by user
• Ensure efficient querying
• Maintain clean transaction boundaries

Architecture:
-------------
Service Layer → Repository → Database

Design Principles:
------------------
• No business logic (only DB operations)
• Reusable query methods
• Optimized joins for performance
• Safe transaction handling
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError

from app.models.invoice import Invoice
from app.models.order import Order


class InvoiceRepository:
    """
    Repository responsible for Invoice persistence
    and retrieval operations.
    """

    def __init__(self, db: Session):
        self.db = db

    # =========================================================
    # CREATE INVOICE
    # =========================================================
    def create(self, invoice: Invoice) -> Invoice:
        """
        Persist a new invoice record.

        Args:
            invoice (Invoice): Invoice instance

        Returns:
            Invoice: Saved invoice object
        """
        try:
            self.db.add(invoice)
            self.db.flush()  # Get ID without committing
            return invoice

        except SQLAlchemyError as e:
            self.db.rollback()
            raise e

    # =========================================================
    # GET INVOICE BY ORDER
    # =========================================================
    def get_by_order(self, order_id: int) -> Invoice | None:
        """
        Fetch invoice associated with a specific order.

        Args:
            order_id (int): Order ID

        Returns:
            Invoice | None
        """
        return (
            self.db.query(Invoice)
            .options(
                joinedload(Invoice.order)  # eager load order
            )
            .filter(Invoice.order_id == order_id)
            .first()
        )

    # =========================================================
    # GET INVOICES BY USER
    # =========================================================
    def get_by_user(self, user_id: int) -> list[Invoice]:
        """
        Fetch all invoices belonging to a user.

        Args:
            user_id (int): User ID

        Returns:
            list[Invoice]
        """
        return (
            self.db.query(Invoice)
            .join(Invoice.order)
            .options(
                joinedload(Invoice.order)
            )
            .filter(Order.user_id == user_id)
            .order_by(Invoice.created_at.desc())
            .all()
        )

    # =========================================================
    # CHECK EXISTING INVOICE
    # =========================================================
    def exists_by_order(self, order_id: int) -> bool:
        """
        Check if invoice already exists for an order.

        Used for idempotency.

        Args:
            order_id (int)

        Returns:
            bool
        """
        return (
            self.db.query(Invoice.id)
            .filter(Invoice.order_id == order_id)
            .first()
            is not None
        )

    # =========================================================
    # DELETE INVOICE (RARE USE)
    # =========================================================
    def delete(self, invoice: Invoice):
        """
        Delete an invoice record.

        NOTE:
        Usually avoided in production systems
        (financial records should be immutable).

        Args:
            invoice (Invoice)
        """
        try:
            self.db.delete(invoice)
            self.db.flush()

        except SQLAlchemyError as e:
            self.db.rollback()
            raise e

    # =========================================================
    # COMMIT TRANSACTION
    # =========================================================
    def commit(self):
        """
        Commit current transaction.
        """
        try:
            self.db.commit()
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e

    # =========================================================
    # ROLLBACK TRANSACTION
    # =========================================================
    def rollback(self):
        """
        Rollback current transaction.
        """
        self.db.rollback()

"""
Order Repository
================

Handles all database operations related to orders.

Responsibilities
----------------
• Create orders
• Create order items
• Retrieve orders
• Retrieve order by ID
• List user orders

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

from app.models.order import Order
from app.models.order_item import OrderItem


class OrderRepository:
    """
    Repository responsible for database operations
    related to orders and order items.
    """

    def __init__(self, db: Session):
        self.db = db

    # ======================================================
    # CREATE ORDER
    # ======================================================

    def create_order(self, order: Order) -> Order:
        """
        Persist a new order.
        """

        self.db.add(order)
        self.db.flush()

        return order

    # ======================================================
    # CREATE ORDER ITEM
    # ======================================================

    def create_order_item(self, item: OrderItem) -> OrderItem:
        """
        Persist an order item.
        """

        self.db.add(item)
        self.db.flush()

        return item

    # ======================================================
    # GET ORDER BY ID
    # ======================================================

    def get_order_by_id(self, order_id: int) -> Optional[Order]:
        """
        Retrieve order by primary key.
        """

        stmt = (
            select(Order)
            .where(Order.id == order_id)
        )

        return self.db.execute(stmt).scalar_one_or_none()

    # ======================================================
    # GET USER ORDERS
    # ======================================================

    def get_orders_by_user(self, user_id: int) -> List[Order]:
        """
        Retrieve all orders belonging to a user.
        """

        stmt = (
            select(Order)
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
        )

        return list(self.db.execute(stmt).scalars().all())

    # ======================================================
    # GET ORDER ITEMS
    # ======================================================

    def get_order_items(self, order_id: int) -> List[OrderItem]:
        """
        Retrieve items belonging to an order.
        """

        stmt = (
            select(OrderItem)
            .where(OrderItem.order_id == order_id)
        )

        return list(self.db.execute(stmt).scalars().all())
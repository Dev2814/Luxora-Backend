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
from app.models.product_variant import ProductVariant
from app.models.product import Product
from app.models.order_timeline import OrderTimeline


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
    
    # ======================================================
    # GET VENDOR ORDERS 
    # ======================================================

    def get_vendor_order(self, vendor_id: int, order_id: int):
        """
        Fetch order for a vendor.

        Ensures:
        - Order belongs to vendor products
        - Proper join path used (NO ambiguity)
        """

        return (
            self.db.query(Order)
            .join(OrderItem, OrderItem.order_id == Order.id)
            .join(ProductVariant, ProductVariant.id == OrderItem.variant_id)
            .join(Product, Product.id == ProductVariant.product_id)
            .filter(
                Order.id == order_id,
                Product.vendor_id == vendor_id
            )
            .first()
        )
    
    # ======================================================
    # UPDATE ORDER STATUS
    # ======================================================

    def update_order_status(self, order: Order, status: str):
        """
        Update order status.
        """
        order.status = status
        self.db.flush()
        return order
    
    # ======================================================
    # LIST VENDOR ORDERS
    # ======================================================

    def get_vendor_orders(self, vendor_id: int):
        """
        Fetch all orders related to a vendor.
        """

        return (
            self.db.query(Order)
            .join(OrderItem, OrderItem.order_id == Order.id)
            .join(ProductVariant, ProductVariant.id == OrderItem.variant_id)
            .join(Product, Product.id == ProductVariant.product_id)
            .filter(Product.vendor_id == vendor_id)
            .distinct()
            .all()
        )
    
    # ======================================================
    # LAST TIMELINE ENTRY
    # ======================================================

    def get_last_timeline(self, order_id: int):
        """
        Fetch latest timeline entry for order.
        """

        return (
            self.db.query(OrderTimeline)
            .filter(OrderTimeline.order_id == order_id)
            .order_by(OrderTimeline.created_at.desc())
            .first()
        )


    # ======================================================
    # ADD ORDER TIMELINE
    # ======================================================

    def add_order_timeline(self, order_id: int, status: str):
        """
        Create a new timeline entry for order.

        This is append-only log.
        """

        timeline = OrderTimeline(
            order_id=order_id,
            status=status
        )

        self.db.add(timeline)
        self.db.flush()

    # ======================================================
    # GET ORDER TIMELINE
    # ======================================================

    def get_order_timeline(self, order_id: int):
        """
        Fetch full timeline for an order.
        """

        return (
            self.db.query(OrderTimeline)
            .filter(OrderTimeline.order_id == order_id)
            .order_by(OrderTimeline.created_at.asc())
            .all()
        )
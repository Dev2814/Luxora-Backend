"""
Vendor Analytics Repository
==========================

Handles all DB queries related to vendor analytics.

IMPORTANT:
Uses Order → OrderItem → Product → Vendor relationship
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.product_variant import ProductVariant

class VendorAnalyticsRepository:

    def __init__(self, db: Session):
        self.db = db

    # ----------------------------------------
    # TOTAL ORDERS
    # ----------------------------------------
    def get_total_orders(self, vendor_id: int) -> int:
        return (
            self.db.query(func.count(func.distinct(Order.id)))
            .join(OrderItem, Order.id == OrderItem.order_id)
            .join(ProductVariant, ProductVariant.id == OrderItem.variant_id)
            .join(Product, Product.id == ProductVariant.product_id)
            .filter(Product.vendor_id == vendor_id)
            .scalar()
        )

    # ----------------------------------------
    # PENDING ORDERS
    # ----------------------------------------
    def get_pending_orders(self, vendor_id: int) -> int:
        return (
            self.db.query(func.count(func.distinct(Order.id)))
            .join(OrderItem, Order.id == OrderItem.order_id)
            .join(ProductVariant, ProductVariant.id == OrderItem.variant_id)
            .join(Product, Product.id == ProductVariant.product_id)
            .filter(
                Product.vendor_id == vendor_id,
                Order.status.in_(["pending", "processing"])
            )
            .scalar()
        )

    # ----------------------------------------
    # TOTAL SALES
    # ----------------------------------------
    def get_total_sales(self, vendor_id: int) -> float:
        return (
            self.db.query(func.coalesce(func.sum(OrderItem.subtotal), 0.0))
            .join(ProductVariant, ProductVariant.id == OrderItem.variant_id)
            .join(Product, Product.id == ProductVariant.product_id)
            .filter(Product.vendor_id == vendor_id)
            .scalar()
        )

    # ----------------------------------------
    # REVENUE CHART
    # ----------------------------------------
    def get_revenue_chart(self, vendor_id: int):
        return (
            self.db.query(
                func.date(Order.created_at).label("date"),
                func.sum(OrderItem.subtotal).label("revenue")
            )
            .join(OrderItem, Order.id == OrderItem.order_id)
            .join(ProductVariant, ProductVariant.id == OrderItem.variant_id)
            .join(Product, Product.id == ProductVariant.product_id)
            .filter(Product.vendor_id == vendor_id)
            .group_by(func.date(Order.created_at))
            .order_by(func.date(Order.created_at))
            .all()
        )
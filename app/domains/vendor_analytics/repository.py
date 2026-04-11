"""
Vendor Analytics Repository
==========================

Handles all DB queries related to vendor analytics.

IMPORTANT:
Uses Order → OrderItem → Product → Vendor relationship
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.order import Order, PaymentStatus
from app.models.order_item import OrderItem
from app.models.inventory import Inventory
from app.models.product import Product
from app.models.product_variant import ProductVariant
from datetime import datetime, timedelta
from app.models.product_variant import ProductVariant

class VendorAnalyticsRepository:

    def __init__(self, db: Session):
        self.db = db

    # ----------------------------------------
    # TOTAL ORDERS
    # ----------------------------------------

    def get_total_products(self, vendor_id: int) -> int:
        """
        Count total products owned by vendor.
        """
        return self.db.query(Product).filter(
            Product.vendor_id == vendor_id
        ).count()
    

    # ----------------------------------------
    # TOTAL SALES
    # ----------------------------------------

    def get_total_orders(self, vendor_id: int) -> int:
        return (
            self.db.query(Order.id)
            .join(OrderItem, OrderItem.order_id == Order.id)
            .join(ProductVariant, ProductVariant.id == OrderItem.variant_id)
            .join(Product, Product.id == ProductVariant.product_id)
            .filter(Product.vendor_id == vendor_id)
            .distinct()
            .count()
        )
    
    # ----------------------------------------
    # TOTAL REVENUE 
    # ----------------------------------------

    def get_total_revenue(self, vendor_id: int) -> float:
        total = (
            self.db.query(func.sum(OrderItem.subtotal))
            .join(ProductVariant, ProductVariant.id == OrderItem.variant_id)
            .join(Product, Product.id == ProductVariant.product_id)
            .filter(Product.vendor_id == vendor_id)
            .scalar()
        )

        return float(total or 0)
    

    # ----------------------------------------
    # REVENUE CHART
    # ----------------------------------------

    def get_revenue_chart(self, vendor_id: int, days: int = 7):
            """
            Returns daily revenue for last N days
            """

            start_date = datetime.utcnow() - timedelta(days=days)

            results = (
                self.db.query(
                    func.date(Order.created_at).label("date"),
                    func.sum(OrderItem.subtotal).label("revenue")
                )
                .join(OrderItem, OrderItem.order_id == Order.id)
                .join(ProductVariant, ProductVariant.id == OrderItem.variant_id)
                .join(Product, Product.id == ProductVariant.product_id)
                .filter(
                    Product.vendor_id == vendor_id,
                    Order.created_at >= start_date
                )
                .group_by(func.date(Order.created_at))
                .order_by(func.date(Order.created_at))
                .all()
            )

            return results
    
    # ----------------------------------------
    # lOW STOCK COUNT
    # ----------------------------------------

    def get_low_stock_count(self, vendor_id: int) -> int:
        return (
            self.db.query(Inventory.id)
            .join(ProductVariant, ProductVariant.id == Inventory.variant_id)
            .join(Product, Product.id == ProductVariant.product_id)
            .filter(
                Product.vendor_id == vendor_id,
                Inventory.stock <= Inventory.low_stock_threshold
            )
            .count()
        )

    # ----------------------------------------
    # LOW STOCK PRODUCTS
    # ----------------------------------------
    def get_low_stock_products(self, vendor_id: int, page: int, limit: int):
        """
        Fetch low stock variants for a vendor.

        Logic:
        - Inventory.available_stock <= threshold
        - Variant → Product → Vendor
        """

        offset = (page - 1) * limit

        query = (
            self.db.query(
                Product.id.label("product_id"),
                Product.name.label("product_name"),
                ProductVariant.id.label("variant_id"),
                ProductVariant.name.label("variant_name"),
                Inventory.stock,
                Inventory.low_stock_threshold
            )
            .join(ProductVariant, ProductVariant.id == Inventory.variant_id)
            .join(Product, Product.id == ProductVariant.product_id)
            .filter(
                Product.vendor_id == vendor_id,
                Inventory.stock <= Inventory.low_stock_threshold
            )
        )

        total = query.count()

        results = (
            query
            .offset(offset)
            .limit(limit)
            .all()
        )

        return results, total
    
    # ----------------------------------------
    # VENDOR EARNINGS
    # ----------------------------------------

    def get_vendor_earnings(self, vendor_id: int):
        """
        Calculate vendor earnings summary.
        """

        # -------------------------------
        # TOTAL REVENUE
        # -------------------------------
        total_revenue = (
            self.db.query(func.sum(OrderItem.subtotal))
            .join(ProductVariant, ProductVariant.id == OrderItem.variant_id)
            .join(Product, Product.id == ProductVariant.product_id)
            .filter(Product.vendor_id == vendor_id)
            .scalar()
        ) or 0

        # -------------------------------
        # TOTAL ORDERS
        # -------------------------------
        total_orders = (
            self.db.query(Order.id)
            .join(OrderItem, OrderItem.order_id == Order.id)
            .join(ProductVariant, ProductVariant.id == OrderItem.variant_id)
            .join(Product, Product.id == ProductVariant.product_id)
            .filter(Product.vendor_id == vendor_id)
            .distinct()
            .count()
        )

        # -------------------------------
        # PAID REVENUE
        # -------------------------------
        paid_revenue = (
            self.db.query(func.sum(OrderItem.subtotal))
            .join(Order, Order.id == OrderItem.order_id)
            .join(ProductVariant, ProductVariant.id == OrderItem.variant_id)
            .join(Product, Product.id == ProductVariant.product_id)
            .filter(
                Product.vendor_id == vendor_id,
                Order.payment_status == PaymentStatus.PAID
            )
            .scalar()
        ) or 0

        # -------------------------------
        # PENDING REVENUE
        # -------------------------------
        pending_revenue = (
            self.db.query(func.sum(OrderItem.subtotal))
            .join(Order, Order.id == OrderItem.order_id)
            .join(ProductVariant, ProductVariant.id == OrderItem.variant_id)
            .join(Product, Product.id == ProductVariant.product_id)
            .filter(
                Product.vendor_id == vendor_id,
                Order.payment_status == PaymentStatus.PENDING
            )
            .scalar()
        ) or 0

        return {
            "total_revenue": float(total_revenue),
            "total_orders": total_orders,
            "paid_revenue": float(paid_revenue),
            "pending_revenue": float(pending_revenue),
        }
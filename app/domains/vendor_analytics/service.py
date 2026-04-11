"""
Vendor Analytics Service
=======================

Business logic layer for vendor dashboard.
"""

from app.domains.vendor_analytics.repository import VendorAnalyticsRepository


class VendorAnalyticsService:

    def __init__(self, db):
        self.repo = VendorAnalyticsRepository(db)

    def get_dashboard(self, vendor_id: int):
        """
        Get vendor dashboard summary.

        Combines:
        • Product count
        • Order count
        • Revenue
        • Low stock alerts
        """

        return {
            "total_products": self.repo.get_total_products(vendor_id),
            "total_orders": self.repo.get_total_orders(vendor_id),
            "total_revenue": self.repo.get_total_revenue(vendor_id),
            "low_stock_count": self.repo.get_low_stock_count(vendor_id),
        }
    
    def get_revenue_chart(self, vendor_id: int, days: int):
        data = self.repo.get_revenue_chart(vendor_id, days)

        return {
            "data": [
                {
                    "date": str(row.date),
                    "revenue": float(row.revenue or 0)
                }
                for row in data
            ]
        }
    

    def get_low_stock(self, vendor_id: int, page: int, limit: int):
        results, total = self.repo.get_low_stock_products(
            vendor_id, page, limit
        )

        return {
            "items": [
                {
                    "product_id": r.product_id,
                    "product_name": r.product_name,
                    "variant_id": r.variant_id,
                    "variant_name": r.variant_name,
                    "stock": r.stock,
                    "threshold": r.low_stock_threshold
                }
                for r in results
            ],
            "total": total,
            "page": page,
            "limit": limit
        }
    
    # ----------------------------------------
    # VENDOR EARNINGS   
    # ----------------------------------------

    def get_earnings(self, vendor_id: int):
        return self.repo.get_vendor_earnings(vendor_id)
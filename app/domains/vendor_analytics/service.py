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

        total_orders = self.repo.get_total_orders(vendor_id)
        pending_orders = self.repo.get_pending_orders(vendor_id)
        total_sales = self.repo.get_total_sales(vendor_id)

        chart_data = self.repo.get_revenue_chart(vendor_id)

        revenue_chart = [
            {
                "date": str(row.date),
                "revenue": float(row.revenue)
            }
            for row in chart_data
        ]

        return {
            "total_orders": total_orders,
            "pending_orders": pending_orders,
            "total_sales": total_sales,
            "revenue_chart": revenue_chart
        }
"""
Order Scheduler (FINAL PRODUCTION VERSION)
=========================================

Features:
---------
• Enum-safe
• Timezone-safe (local time)
• Production timing rules
• No duplicate timeline entries
• Fully logged
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.core.logger import log_event
from app.models.order import Order, OrderStatus
from app.models.order_timeline import OrderTimeline


def auto_update_orders(db: Session):

    try:
        # ==================================================
        # USE LOCAL TIME (IMPORTANT)
        # ==================================================
        now = datetime.now()

        log_event(
            "scheduler_cycle_started",
            level="info",
            timestamp=str(now)
        )

        # ==================================================
        # FETCH ACTIVE ORDERS ONLY
        # ==================================================
        orders = db.query(Order).filter(
            Order.status.in_([
                OrderStatus.PENDING,
                OrderStatus.CONFIRMED,
                OrderStatus.SHIPPED
            ])
        ).all()

        log_event(
            "scheduler_orders_fetched",
            level="info",
            total_orders=len(orders)
        )

        processed = 0

        for order in orders:

            status = order.status.value
            last_update = order.status_updated_at

            if not last_update:
                continue

            # ==================================================
            # TIME DIFFERENCE
            # ==================================================
            time_diff = now - last_update

            log_event(
                "debug_order_check",
                level="info",
                order_id=order.id,
                status=status,
                last_update=str(last_update),
                now=str(now),
                diff=str(time_diff)
            )

            # ==================================================
            # PRODUCTION TIMING RULES
            # ==================================================
            if status == "pending" and time_diff < timedelta(minutes=5):
                continue

            if status == "confirmed" and time_diff < timedelta(minutes=30):
                continue

            if status == "shipped" and time_diff < timedelta(days=1):
                continue

            # ==================================================
            # GET LAST TIMELINE
            # ==================================================
            last_timeline = db.query(OrderTimeline).filter(
                OrderTimeline.order_id == order.id
            ).order_by(OrderTimeline.created_at.desc()).first()

            # ==================================================
            # PENDING → CONFIRMED
            # ==================================================
            if status == "pending":

                if last_timeline and last_timeline.status == "confirmed":
                    continue

                order.status = OrderStatus.CONFIRMED
                order.status_updated_at = now

                log_event(
                    "order_auto_confirmed",
                    level="info",
                    order_id=order.id
                )

                db.add(OrderTimeline(
                    order_id=order.id,
                    status="confirmed"
                ))

                processed += 1

            # ==================================================
            # CONFIRMED → SHIPPED
            # ==================================================
            elif status == "confirmed":

                if last_timeline and last_timeline.status == "shipped":
                    continue

                order.status = OrderStatus.SHIPPED
                order.status_updated_at = now

                log_event(
                    "order_auto_shipped",
                    level="info",
                    order_id=order.id
                )

                db.add(OrderTimeline(
                    order_id=order.id,
                    status="shipped"
                ))

                processed += 1

            # ==================================================
            # SHIPPED → DELIVERED
            # ==================================================
            elif status == "shipped":

                if last_timeline and last_timeline.status == "delivered":
                    continue

                order.status = OrderStatus.DELIVERED
                order.status_updated_at = now

                log_event(
                    "order_auto_delivered",
                    level="info",
                    order_id=order.id
                )

                db.add(OrderTimeline(
                    order_id=order.id,
                    status="delivered"
                ))

                processed += 1

        # ==================================================
        # COMMIT
        # ==================================================
        db.commit()

        log_event(
            "scheduler_cycle_completed",
            level="info",
            processed_orders=processed
        )

    except Exception as e:

        log_event(
            "scheduler_failed",
            level="critical",
            error=str(e)
        )
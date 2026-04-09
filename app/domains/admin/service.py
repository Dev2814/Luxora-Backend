"""
Admin Service

Handles administrative business logic.

Architecture:
Routes → Service → Repository → Database

Responsibilities:
- Vendor moderation (approve / reject)
- Brand management
- User moderation
- Platform analytics
- Admin activity logging
- Email notifications
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

from app.domains.admin.repository import AdminRepository
from app.domains.admin.activity_service import AdminActivityService
from app.models.vendor_profile import VendorStatus
from app.models.user import AccountStatus,User

from app.models.brand import Brand

from app.infrastructure.email.service import send_email
from app.core.logger import log_event


class AdminService:

    def __init__(self, db: Session):

        self.db = db
        self.repo = AdminRepository(db)
        self.activity = AdminActivityService(db)

    # ==================================================
    # VENDOR APPROVAL
    # ==================================================

    def approve_vendor(self, vendor_id: int, admin_id: int):

        """
        Approve vendor account.

        Steps:
        1. Validate vendor
        2. Mark vendor verified
        3. Send approval email
        4. Log admin activity
        """

        
        try:

            vendor = self.repo.get_vendor_by_id(vendor_id)

            if not vendor:
                raise ValueError("Vendor not found")

            # FIX: check enum properly
            if vendor.verification_status == VendorStatus.APPROVED:
                raise ValueError("Vendor already approved")

            vendor.verification_status = VendorStatus.APPROVED
            vendor.verified_at = datetime.utcnow()

            self.repo.commit()

            send_email(
                to_email=vendor.user.email,
                subject="Your Vendor Account Has Been Approved",
                template_name="vendor_approved.html",
                context={
                    "business_name": vendor.business_name,
                    "title": "Your Vendor Request Approved",
                    "year": datetime.utcnow().year
                }
            )

            self.activity.log_activity(
                admin_id=admin_id,
                action="vendor_approved",
                target_type="vendor",
                target_id=vendor_id
            )

            log_event(
                "vendor_approved",
                admin_id=admin_id,
                vendor_id=vendor_id
            )

            return {"message": "Vendor approved successfully"}

        except ValueError:
            raise

        except SQLAlchemyError as e:

            self.repo.rollback()

            log_event(
                "vendor_approval_db_error",
                level="critical",
                vendor_id=vendor_id,
                error=str(e)
            )

            raise ValueError("Unable to approve vendor")


    # ==================================================
    # REJECT VENDOR
    # ==================================================

    def reject_vendor(self, vendor_id: int, reason: str, admin_id: int):

        """
        Reject vendor registration.
        """

        try:

            vendor = self.repo.get_vendor_by_id(vendor_id)

            if not vendor:
                raise ValueError("Vendor not found")

            vendor.verification_status = VendorStatus.REJECTED
            vendor.rejection_reason = reason

            self.repo.commit()

            send_email(
                to_email=vendor.user.email,
                subject="Vendor Application Rejected",
                template_name="vendor_rejected.html",
                context={
                    "business_name": vendor.business_name,
                    "reason": reason,
                    "title": "Your Vendor Request Rejected",
                    "year": datetime.utcnow().year
                }
            )

            self.activity.log_activity(
                admin_id=admin_id,
                action="vendor_rejected",
                target_type="vendor",
                target_id=vendor_id,
                metadata={"reason": reason}
            )

            log_event(
                "vendor_rejected",
                admin_id=admin_id,
                vendor_id=vendor_id
            )

            return {"message": "Vendor rejected successfully"}

        except ValueError:
            raise

        except SQLAlchemyError as e:

            self.repo.rollback()

            log_event(
                "vendor_reject_db_error",
                level="critical",
                vendor_id=vendor_id,
                error=str(e)
            )

            raise ValueError("Unable to reject vendor")
        

    # ==================================================
    # GET PENDING VENDORS
    # ==================================================

    def get_pending_vendors(self):

        """
        Fetch vendors awaiting approval.
        """

        try:

                vendors = self.repo.get_pending_vendors()

                result = [
                    {
                        "vendor_id": v.id,
                        "user_id": v.user_id,
                        "user_email": v.user.email,
                        "business_name": v.business_name,
                        "business_address": v.business_address,
                        "gst_number": v.gst_number,
                        "verification_status": v.verification_status.value
                    }
                    for v in vendors
                ]

                log_event(
                    "admin_viewed_pending_vendors",
                    total=len(result)
                )

                return result

        except SQLAlchemyError as e:

            log_event(
                "pending_vendors_fetch_error",
                level="critical",
                error=str(e)
            )

            raise ValueError("Unable to fetch pending vendors")

    # ==================================================
    # CREATE BRAND
    # ==================================================

    def create_brand(self, name: str, logo: str, admin_id: int):

        """
        Create a new brand.
        """

        try:

            name = name.strip().lower()

            existing = self.repo.get_brand_by_name(name)

            if existing:
                raise ValueError("Brand already exists")

            brand = Brand(name=name, logo=logo)

            self.repo.create_brand(brand)
            self.repo.commit()

            # Activity log
            self.activity.log_activity(
                admin_id=admin_id,
                action="brand_created",
                target_type="brand",
                target_id=brand.id
            )

            log_event(
                "brand_created",
                admin_id=admin_id,
                brand_id=brand.id
            )

            return {"message": "Brand created successfully"}

        except ValueError:
            raise

        except SQLAlchemyError as e:

            self.repo.rollback()

            log_event(
                "brand_create_db_error",
                level="critical",
                error=str(e)
            )

            raise ValueError("Unable to create brand")

    # ==================================================
    # LIST BRANDS
    # ==================================================

    def list_brands(self):

        """
        Fetch all brands.
        """

        try:

            brands = self.repo.list_brands()

            return [
                {
                    "id": b.id,
                    "name": b.name,
                    "logo": b.logo
                }
                for b in brands
            ]

        except Exception as e:

            log_event(
                "list_brands_error",
                level="critical",
                error=str(e)
            )

            raise ValueError("Unable to fetch brands")

    # ==================================================
    # DELETE BRAND
    # ==================================================

    def delete_brand(self, brand_id: int, admin_id: int):

        """
        Remove brand from platform.
        """

        try:

            brand = self.repo.get_brand_by_id(brand_id)

            if not brand:
                raise ValueError("Brand not found")

            self.repo.delete_brand(brand)
            self.repo.commit()

            # Activity log
            self.activity.log_activity(
                admin_id=admin_id,
                action="brand_deleted",
                target_type="brand",
                target_id=brand_id
            )

            log_event(
                "brand_deleted",
                admin_id=admin_id,
                brand_id=brand_id
            )

            return {"message": "Brand deleted successfully"}

        except ValueError:
            raise

        except SQLAlchemyError as e:

            self.repo.rollback()

            log_event(
                "delete_brand_db_error",
                level="critical",
                brand_id=brand_id,
                error=str(e)
            )

            raise ValueError("Unable to delete brand")

    # ==================================================
    # PLATFORM ANALYTICS
    # ==================================================

    def get_platform_stats(self):

        """
        Return platform analytics summary.
        """

        try:

            stats = {
                "total_users": self.repo.count_total_users(),
                "total_vendors": self.repo.count_total_vendors(),
                "total_buyers": self.repo.count_total_Buyers(),
                "approved_vendors": self.repo.count_approved_vendors(),
                "pending_vendors": self.repo.count_pending_vendors()
            }

            log_event("admin_viewed_platform_stats")

            return stats

        except Exception as e:

            log_event(
                "platform_stats_error",
                level="critical",
                error=str(e)
            )

            raise ValueError("Unable to fetch platform statistics")

    # ==================================================
    # DEACTIVATE USER
    # ==================================================


    def deactivate_user(self, user_id: int, admin_id: int, reason: str | None = None):

        """
        Deactivate user account and notify via email.
        """

        try:

            user = self.repo.get_user_by_id(user_id)

            if not user:
                raise ValueError("User not found")

            # Prevent duplicate deactivation
            if user.status == AccountStatus.DISABLED:
                raise ValueError("User already deactivated")

            user.status = AccountStatus.DISABLED

            # --------------------------------------------------
            # DEFAULT REASON
            # --------------------------------------------------

            if not reason:
                reason = "Your account has been deactivated due to a violation of platform policies."

            # --------------------------------------------------
            # UPDATE USER STATUS
            # --------------------------------------------------

            user.is_active = False

            self.repo.commit()

            # --------------------------------------------------
            # SEND EMAIL
            # --------------------------------------------------

            send_email(
                to_email=user.email,
                subject="Your Luxora Account Has Been Deactivated",
                template_name="account_deactivated.html",
                context={
                    "name": user.first_name if hasattr(user, "first_name") else "User",
                    "reason": reason,
                    "year": datetime.utcnow().year
                }
            )

            # --------------------------------------------------
            # ADMIN ACTIVITY LOG
            # --------------------------------------------------

            self.activity.log_activity(
                admin_id=admin_id,
                action="user_deactivated",
                target_type="user",
                target_id=user_id,
                metadata={"reason": reason}
            )

            log_event(
                "user_deactivated",
                admin_id=admin_id,
                user_id=user_id,
                reason=reason
            )

            return {"message": "User deactivated successfully"}

        except ValueError:
            raise

        except SQLAlchemyError as e:

            self.repo.rollback()

            log_event(
                "user_deactivate_error",
                level="critical",
                user_id=user_id,
                error=str(e)
            )

            raise ValueError("Unable to deactivate user")
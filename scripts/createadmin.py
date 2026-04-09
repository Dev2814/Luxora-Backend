
"""
Admin Bootstrap Script (Static Version)

Creates the initial super admin account using predefined values.
Run only once during system setup.

Usage:
    python createadmin.py
"""

from app.infrastructure.database.session import SessionLocal
from app.models.user import User, UserRole, AccountStatus
from app.models.admin_profile import AdminProfile, AdminRole
from app.core.security import hash_password
from app.core.logger import log_event


# --------------------------------------------------
# STATIC CONFIG (CHANGE HERE)
# --------------------------------------------------

ADMIN_CONFIG = {
    "email": "pdev3590@gmail.com",
    "phone": "9999999999",
    "password": "Admin@123",   # ⚠️ Change in production
}


def create_admin():

    db = SessionLocal()

    try:
        print("\n🚀 Luxora Admin Bootstrap (Static Mode)\n")

        email = ADMIN_CONFIG["email"].strip().lower()
        phone = ADMIN_CONFIG["phone"].strip()
        password = ADMIN_CONFIG["password"]

        existing = db.query(User).filter(User.email == email).first()

        if existing:
            print("⚠️ Admin already exists")
            return

        # --------------------------------------------------
        # CREATE USER
        # --------------------------------------------------

        user = User(
            email=email,
            phone=phone,
            password_hash=hash_password(password),
            role=UserRole.ADMIN,
            status=AccountStatus.ACTIVE,
            is_verified=True
        )

        db.add(user)
        db.flush()

        # --------------------------------------------------
        # CREATE ADMIN PROFILE
        # --------------------------------------------------

        admin_profile = AdminProfile(
            user_id=user.id,
            department="platform",
            role=AdminRole.SUPER_ADMIN,
            access_level="full"
        )

        db.add(admin_profile)

        db.commit()

        log_event(
            "initial_admin_created",
            user_id=user.id,
            email=email
        )

        print("\n✅ Admin created successfully!")
        print(f"Email: {email}")

    except Exception as e:

        db.rollback()

        log_event(
            "admin_creation_failed",
            level="critical",
            error=str(e)
        )

        print("❌ Admin creation failed:", str(e))

    finally:
        db.close()


if __name__ == "__main__":
    create_admin()
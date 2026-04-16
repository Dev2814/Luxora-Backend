import sys
import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# ussers 
from app.models.base import Base
import app.models.user 
import app.models.user_sessions
import app.models.user_address
import app.models.customer_profile
import app.models.vendor_profile
import app.models.admin_profile 
import app.models.admin_activity_log
import app.models.login_history

# Wishlist
import app.models.wishlist
import app.models.wishlist_item

# Category
import app.models.category

# Products
import app.models.brand
import app.models.product
import app.models.product_variant
import app.models.product_image
import app.models.inventory
import app.models.product_attribute
import app.models.review
import app.models.review_helpful

# Cart
import app.models.cart
import app.models.cart_item

# Orders
import app.models.order
import app.models.order_item
import app.models.order_timeline

# Invoice
import app.models.invoice

# Payments
import app.models

# Coupons
import app.models.coupon
import app.models.coupon_usage

# Notifications
# import app.models.notification


# this is the Alembic Config object
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
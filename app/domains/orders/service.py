"""
Order Service
=============

Handles checkout logic and order creation.

Responsibilities
----------------
• Convert cart to order
• Validate inventory
• Create order and order items
• Calculate totals
• Reserve inventory
• Clear cart after checkout

Design Principles
-----------------
• Business logic only
• Repository handles database operations
• Service manages transactions
• Logging and error handling

Architecture
------------
Routes → Service → Repository → Database
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.inventory import Inventory
from app.models.product_variant import ProductVariant
from app.models.product import Product
from app.models.product_attribute import ProductAttributeValue

from app.domains.orders.repository import OrderRepository
from app.domains.cart.repository import CartRepository

from app.core.logger import log_event
from sqlalchemy.orm import joinedload, selectinload

from app.infrastructure.invoice.service import InvoiceService


class OrderService:
    """
    Business logic layer for checkout and order creation.
    """

    def __init__(self, db: Session):
        self.db = db
        self.order_repo = OrderRepository(db)
        self.cart_repo = CartRepository(db)

        self.invoice_service = InvoiceService(self.db)

    # ======================================================
    # CREATE ORDER FROM CART (CHECKOUT)
    # ======================================================

    def checkout(self, user_id: int, address_id: int):

        try:

            # --------------------------------------------------
            # GET USER CART
            # --------------------------------------------------

            cart = self.cart_repo.get_cart_by_user(user_id)

            if not cart:
                raise ValueError("Cart not found")

            cart_items = self.cart_repo.get_cart_items(cart.id)

            if not cart_items:
                raise ValueError("Cart is empty")

            # --------------------------------------------------
            # VALIDATE INVENTORY
            # --------------------------------------------------

            total_amount = 0
            order_items_data = []

            for item in cart_items:

                inventory = (
                    self.db.query(Inventory)
                    .filter(Inventory.variant_id == item.variant_id)
                    .one_or_none()
                )

                if not inventory:
                    raise ValueError("Inventory not found")

                if inventory.stock < item.quantity:
                    raise ValueError("Not enough stock available")

                # get variant price
                variant = item.variant

                price = variant.price
                subtotal = price * item.quantity

                total_amount += subtotal

                order_items_data.append({
                    "variant_id": item.variant_id,
                    "quantity": item.quantity,
                    "price_snapshot": price,
                    "subtotal": subtotal
                })

            # --------------------------------------------------
            # CREATE ORDER
            # --------------------------------------------------

            order = Order(
                user_id=user_id,
                address_id=address_id,
                total_amount=total_amount
            )

            order = self.order_repo.create_order(order)

            # --------------------------------------------------
            # CREATE ORDER ITEMS
            # --------------------------------------------------

            for item_data in order_items_data:

                order_item = OrderItem(
                    order_id=order.id,
                    variant_id=item_data["variant_id"],
                    quantity=item_data["quantity"],
                    price_snapshot=item_data["price_snapshot"],
                    subtotal=item_data["subtotal"]
                )

                self.order_repo.create_order_item(order_item)

            # --------------------------------------------------
            # UPDATE INVENTORY
            # --------------------------------------------------

            for item in cart_items:

                inventory = (
                    self.db.query(Inventory)
                    .filter(Inventory.variant_id == item.variant_id)
                    .one()
                )

                inventory.stock -= item.quantity

            # --------------------------------------------------
            # CLEAR CART
            # --------------------------------------------------

            self.cart_repo.clear_cart(cart.id)

            # --------------------------------------------------
            # COMMIT TRANSACTION
            # --------------------------------------------------

            self.db.commit()

            self.db.refresh(order)

            log_event(
                "order_created",
                user_id=user_id,
                order_id=order.id,
                total_amount=str(total_amount)
            )

            items = self.order_repo.get_order_items(order.id)
            order_items = []

            for item in items:
                variant = item.variant
                product = variant.product

                order_items.append({
                    "id": item.id,
                    "order_id": order.id,
                    "variant_id": variant.id,
                    "quantity": item.quantity,
                    "price_snapshot": item.price_snapshot,
                    "subtotal": item.subtotal,

                    "product_id": product.id,
                    "product_name": product.name,
                    "compare_price": product.compare_price,
                    "image": None,  # optional for now
                    "attributes": []
                })

            return {
                "id": order.id,
                "user_id": order.user_id,
                "address_id": order.address_id,
                "total_amount": order.total_amount,
                "items": order_items
            }

        except SQLAlchemyError as e:

            self.db.rollback()

            log_event(
                "checkout_database_error",
                level="error",
                error=str(e)
            )

            raise ValueError("Checkout failed")

        except ValueError as e:

            self.db.rollback()

            raise e
        
    # ======================================================
    # CREATE ORDER fROM PRODUCT (CHECKOUT)
    # ======================================================
        
    def buy_now(self, user_id: int, variant_id: int, quantity: int, address_id: int):

        try:

            # -------------------------------
            # INVENTORY
            # -------------------------------
            inventory = (
                self.db.query(Inventory)
                .filter(Inventory.variant_id == variant_id)
                .one_or_none()
            )

            if not inventory:
                raise ValueError("Inventory not found")

            available_stock = inventory.available_stock

            if available_stock <= 0:
                raise ValueError("Product is out of stock")

            if quantity > available_stock:
                quantity = available_stock

            # -------------------------------
            # GET VARIANT
            # -------------------------------
            variant = inventory.variant

            price = variant.price
            subtotal = price * quantity

            # -------------------------------
            # CREATE ORDER
            # -------------------------------
            order = Order(
                user_id=user_id,
                address_id=address_id,
                total_amount=subtotal
            )

            order = self.order_repo.create_order(order)

            # -------------------------------
            # CREATE ORDER ITEM
            # -------------------------------
            order_item = OrderItem(
                order_id=order.id,
                variant_id=variant_id,
                quantity=quantity,
                price_snapshot=price,
                subtotal=subtotal
            )

            self.order_repo.create_order_item(order_item)

            # -------------------------------
            # UPDATE STOCK
            # -------------------------------
            inventory.stock -= quantity

            self.db.commit()
            self.db.refresh(order)

            return order

        except Exception as e:
            self.db.rollback()
            raise ValueError("Buy now failed")
        
    def get_orders(self, user_id: int):

        orders = (
            self.db.query(Order)
            .filter(Order.user_id == user_id)
            .options(
                selectinload(Order.items)
                .joinedload(OrderItem.variant)
                .joinedload(ProductVariant.product)
                .selectinload(Product.images),

                selectinload(Order.items)
                .joinedload(OrderItem.variant)
                .selectinload(ProductVariant.attribute_values)
                .joinedload(ProductAttributeValue.attribute)
            )
            .all()
        )

        order_list = []

        for order in orders:

            order_items = []

            for item in order.items:

                variant = item.variant
                product = variant.product

                # -------------------------
                # IMAGE
                # -------------------------
                image_url = None
                if product.images:
                    image_url = next(
                        (img.image_url for img in product.images if img.is_primary),
                        product.images[0].image_url
                    )

                # -------------------------
                # ATTRIBUTES
                # -------------------------
                attributes = []
                if variant.attribute_values:
                    for val in variant.attribute_values:
                        attributes.append({
                            "attribute": val.attribute.name,
                            "value": val.value
                        })

                # -------------------------
                # ITEM RESPONSE
                # -------------------------
                order_items.append({
                    "id": item.id,
                    "order_id": order.id,
                    "variant_id": variant.id,
                    "quantity": item.quantity,
                    "price_snapshot": item.price_snapshot,
                    "subtotal": item.subtotal,

                    "product_id": product.id,
                    "product_name": product.name,
                    "compare_price": product.compare_price,
                    "image": image_url,
                    "attributes": attributes
                })

            order_list.append({
                "id": order.id,
                "user_id": order.user_id,
                "address_id": order.address_id,
                "status": order.status.value,
                "payment_status": order.payment_status.value,
                "total_amount": order.total_amount,
                "items": order_items
            })

        return order_list    
    
    # ======================================================
    # GET SINGLE ORDER
    # ======================================================

    def get_single_order(self, order_id: int):

        order = (
            self.db.query(Order)
            .filter(Order.id == order_id)
            .options(
                selectinload(Order.items)
                .joinedload(OrderItem.variant)
                .joinedload(ProductVariant.product)
                .selectinload(Product.images),

                selectinload(Order.items)
                .joinedload(OrderItem.variant)
                .selectinload(ProductVariant.attribute_values)
                .joinedload(ProductAttributeValue.attribute)
            )
            .first()
        )

        if not order:
            return None

        order_items = []

        for item in order.items:

            variant = item.variant
            product = variant.product

            # IMAGE
            image_url = None
            if product.images:
                image_url = next(
                    (img.image_url for img in product.images if img.is_primary),
                    product.images[0].image_url
                )

            # ATTRIBUTES
            attributes = []
            if variant.attribute_values:
                for val in variant.attribute_values:
                    attributes.append({
                        "attribute": val.attribute.name,
                        "value": val.value
                    })

            order_items.append({
                "id": item.id,
                "order_id": order.id,
                "variant_id": variant.id,
                "quantity": item.quantity,
                "price_snapshot": item.price_snapshot,
                "subtotal": item.subtotal,

                "product_id": product.id,
                "product_name": product.name,
                "compare_price": product.compare_price,
                "image": image_url,
                "attributes": attributes
            })

        return {
            "id": order.id,
            "user_id": order.user_id,
            "address_id": order.address_id,
            "status": order.status.value,
            "payment_status": order.payment_status.value,
            "total_amount": order.total_amount,
            "items": order_items
        }
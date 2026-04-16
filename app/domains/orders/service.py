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

from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.inventory import Inventory
from app.models.product_variant import ProductVariant
from app.models.product import Product
from app.models.product_attribute import ProductAttributeValue

from app.domains.orders.repository import OrderRepository
from app.domains.cart.repository import CartRepository

from app.core.logger import log_event
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.sql import func

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
            

            self.order_repo.add_order_timeline(order.id, "pending")

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
                "status": order.status.value,
                "payment_status": order.payment_status.value,
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
            self.order_repo.add_order_timeline(order.id, "pending")

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
    
    # ======================================================
    # GET VENDOR ORDER
    # ======================================================

    def get_vendor_order_details(self, vendor_id: int, order_id: int):
        """
        Fetch full order details for vendor.
        """

        order = self.order_repo.get_vendor_order(vendor_id, order_id)

        if not order:
            raise ValueError("Order not found")

        items = []

        for item in order.items:
            variant = item.variant
            product = variant.product

            # -------------------------------
            # GET PRIMARY IMAGE
            # -------------------------------
            primary_image = None

            if product and product.images:
                for img in product.images:
                    if not img.is_deleted and img.is_primary:
                        primary_image = img.image_url
                        break

                # fallback (optional but safe)
                if not primary_image:
                    for img in product.images:
                        if not img.is_deleted:
                            primary_image = img.image_url
                            break

            items.append({
                "product_name": product.name,
                "variant_name": variant.name,
                "quantity": item.quantity,
                "price": float(item.price_snapshot),
                "subtotal": float(item.subtotal),
                "image": primary_image   
            })

        # -------------------------------
        # CUSTOMER INFO
        # -------------------------------
        customer_profile = order.user.customer_profile

        customer_phone = order.user.phone if hasattr(order.user, "phone") else None

        # -------------------------------
        # SHIPPING ADDRESS
        # -------------------------------
        address = order.address

        shipping_address = {
            "full_name": address.full_name if address else None,
            "phone": address.phone_number if address else None,
            "address_line": (
                f"{address.address_line1}, {address.address_line2}"
                if address and address.address_line2
                else address.address_line1 if address else None
            ),
            "city": address.city if address else None,
            "state": address.state if address else None,
            "postal_code": address.postal_code if address else None,
            "country": address.country if address else None,
        }

        # -------------------------------
        # FINAL RESPONSE
        # -------------------------------
        return {
            "order_id": order.id,
            "status": order.status.value,
            "payment_status": order.payment_status.value,
            "total_amount": float(order.total_amount),
            "created_at": str(order.created_at),

            "customer": {
                "name": customer_profile.full_name if customer_profile else "Guest",
                "email": order.user.email,
                "phone": customer_phone
            },

            "shipping_address": shipping_address,

            "items": items
        }

    # ======================================================
    # UPDATE ORDER STATUS
    # ======================================================

    def update_order_status(self, vendor_id: int, order_id: int, new_status: str):
        """
        Update order status and create timeline entry.

        Enterprise Features:
        -------------------
        • Validates status transitions
        • Prevents duplicate timeline entries
        • Transaction-safe operation
        • Vendor ownership validation
        """

        # --------------------------------------------------
        # FETCH ORDER (WITH VALIDATION)
        # --------------------------------------------------
        order = self.order_repo.get_vendor_order(vendor_id, order_id)

        if not order:
            raise ValueError("Order not found or access denied")

        current_status = order.status.value.lower()
        new_status = new_status.lower()

        # --------------------------------------------------
        # VALIDATE TRANSITION
        # --------------------------------------------------
        VALID_TRANSITIONS = {
            "pending": ["confirmed", "cancelled"],
            "confirmed": ["shipped", "cancelled"],
            "shipped": ["delivered"],
            "delivered": [],
            "cancelled": []
        }
        # --------------------------------------------------
        # IGNORE SAME STATUS UPDATE
        # --------------------------------------------------
        if current_status == new_status:
            return {
                "message": "Order already in this status",
                "order_id": order.id,
                "current_status": current_status
            }

        if new_status not in VALID_TRANSITIONS.get(current_status, []):
            raise ValueError(f"Invalid transition: {current_status} → {new_status}")

        # --------------------------------------------------
        # PREVENT DUPLICATE TIMELINE ENTRY
        # --------------------------------------------------
        last_timeline = self.order_repo.get_last_timeline(order_id)

        if last_timeline and last_timeline.status == new_status:
            raise ValueError("Duplicate status update")

        # --------------------------------------------------
        # UPDATE ORDER STATUS
        # --------------------------------------------------

        order.status = OrderStatus(new_status)
        order.status_updated_at = func.now()
 
        # --------------------------------------------------
        # ADD TIMELINE ENTRY
        # --------------------------------------------------
 
        self.order_repo.add_order_timeline(
            order_id=order.id,
            status=new_status
        )

        # --------------------------------------------------
        # COMMIT TRANSACTION
        # --------------------------------------------------
        self.db.commit()

        return {
            "message": "Order status updated successfully",
            "order_id": order.id,
            "new_status": new_status
        }
    
    # ======================================================
    # VENDOR ORDER LIST
    # ======================================================

    def get_vendor_orders(self, vendor_id: int):
        """
        Get all vendor orders (list view).
        """

        orders = self.order_repo.get_vendor_orders(vendor_id)

        result = []

        for order in orders:
            result.append({
                "order_id": order.id,
                "customer_name": order.user.customer_profile.full_name if order.user.customer_profile else "Guest",
                "total_amount": float(order.total_amount),
                "status": order.status.value,
                "payment_status": order.payment_status.value,
                "created_at": str(order.created_at)
            })

        return {
            "items": result
        }
    
    # ======================================================
    # GET ORDER TIMELINE
    # ======================================================

    def get_order_timeline(self, vendor_id: int, order_id: int):
        """
        Get order timeline (vendor view).
        """

        # -------------------------------
        # VALIDATE ORDER OWNERSHIP
        # -------------------------------
        order = self.order_repo.get_vendor_order(vendor_id, order_id)

        if not order:
            raise ValueError("Order not found")

        # -------------------------------
        # FETCH TIMELINE
        # -------------------------------
        timeline = self.order_repo.get_order_timeline(order_id)

        return {
            "items": [
                {
                    "status": t.status,
                    "created_at": str(t.created_at)
                }
                for t in timeline
            ]
        }
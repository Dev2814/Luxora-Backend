from fastapi import APIRouter
from app.api.v1.auth.routes import router as auth_router
from app.api.v1.users.routes import router as users_router
from app.api.v1.admin.routes import router as admin_router
from app.api.v1.categories.routes import router as category_router
from app.api.v1.products.routes import router as product_router
from app.api.v1.brands.routes import router as brand_router
from app.api.v1.attributes.routes import router as attribute_router
from app.api.v1.vendors.routes import router as vendor_router
from app.api.v1.vendor_analytics.routes import router as vendor_analytics_router
from app.api.v1.inventory.routes import router as inventory_router
from app.api.v1.search.routes import router as search_router
from app.api.v1.customers.routes import router as customers_router
from app.api.v1.addresses.routes import router as addresses_router
from app.api.v1.cart.routes import router as cart_router
from app.api.v1.orders.routes import router as orders_router
from app.api.v1.payments.routes import router as payments_router
from app.api.v1.wishlist.routes import router as wishlist_router
from app.api.v1.reviews.routes import router as reviews_router
from app.api.v1.coupons.routes import router as coupons_router
from app.api.v1.notifications.routes import router as notifications_router



api_router = APIRouter()

api_router.include_router(auth_router)

api_router.include_router(users_router)

api_router.include_router(admin_router)

api_router.include_router(brand_router)

api_router.include_router(category_router)

api_router.include_router(product_router)

api_router.include_router(attribute_router)

api_router.include_router(vendor_router)

api_router.include_router(vendor_analytics_router)

api_router.include_router(search_router)

api_router.include_router(inventory_router) 

api_router.include_router(customers_router)

api_router.include_router(addresses_router)

api_router.include_router(cart_router)

api_router.include_router(orders_router)

api_router.include_router(payments_router)

api_router.include_router(wishlist_router)

api_router.include_router(reviews_router)

api_router.include_router(coupons_router)

api_router.include_router(notifications_router)
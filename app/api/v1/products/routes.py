"""
Product Routes

API endpoints for product management.

Responsibilities:
- Public product browsing
- Vendor product management
- Product filtering
- Multiple image upload (separate endpoint)

Architecture:
    Routes → Service → Repository → Database
"""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional, List

from app.api.deps import get_db
from app.api.deps_auth import get_current_user

from app.core.permissions import require_verified_vendor
from app.core.logger import log_event

from app.domains.products.service import ProductService
from app.models.vendor_profile import VendorProfile

from app.api.v1.products.schemas import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductListResponse,
    ProductImageUploadResponse,
)

router = APIRouter(
    prefix="/products",
    tags=["Products"]
)


# ==================================================
# SERVICE DEPENDENCY
# ==================================================

def get_product_service(db: Session = Depends(get_db)) -> ProductService:
    return ProductService(db)


# ==================================================
# FILTER PRODUCTS (PUBLIC)
# ==================================================

@router.get(
    "/search",
    response_model=ProductListResponse,
    summary="Filter Products"
)
def filter_products(
    category_id: Optional[int] = Query(default=None),
    brand_id: Optional[int] = Query(default=None),
    min_price: Optional[float] = Query(default=None),
    max_price: Optional[float] = Query(default=None),
    sort: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, le=100),
    service: ProductService = Depends(get_product_service)
):
    try:
        return service.filter_products(
            category_id=category_id,
            brand_id=brand_id,
            min_price=min_price,
            max_price=max_price,
            sort=sort,
            page=page,
            limit=limit
        )
    except ValueError as e:
        log_event("product_filter_error", level="warning", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


# ==================================================
# LIST PRODUCTS (PUBLIC)
# ==================================================

@router.get(
    "/",
    response_model=ProductListResponse,
    summary="List Products"
)
def list_products(
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=100),
    service: ProductService = Depends(get_product_service)
):
    try:
        return service.list_products(page, limit)
    except ValueError as e:
        log_event("product_list_error", level="warning", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


# ==================================================
# GET PRODUCT (PUBLIC)
# ==================================================

@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Get Product Details"
)
def get_product(
    product_id: int,
    service: ProductService = Depends(get_product_service)
):
    try:
        return service.get_product(product_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ==================================================
# CREATE PRODUCT (VENDOR)
# Step 1: Send product data as clean JSON
# Step 2: Upload images via /{product_id}/images
# ==================================================

@router.post(
    "/",
    response_model=ProductResponse,
    summary="Create Product",
    dependencies=[Depends(require_verified_vendor())]
)
def create_product(
    payload: ProductCreate,                          # ← clean JSON body, works perfectly in Swagger
    current_user=Depends(get_current_user),
    service: ProductService = Depends(get_product_service)
):
    """
    Create a new product (JSON only).

    After creating the product, upload images separately via:
        POST /products/{product_id}/images
    """
    try:
        vendor = (
            service.db.query(VendorProfile)
            .filter(VendorProfile.user_id == current_user["user_id"])
            .first()
        )

        if not vendor:
            raise HTTPException(status_code=403, detail="You are not a vendor")

        product = service.create_product(vendor.id, payload)

        return service.get_product(product.id)

    except ValueError as e:
        log_event("product_create_api_error", level="warning", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


# ==================================================
# UPLOAD PRODUCT IMAGES (VENDOR)
# Step 2: Upload multiple images for a created product
# ==================================================

@router.post(
    "/{product_id}/images",
    response_model=ProductImageUploadResponse,
    summary="Upload Product Images",
    dependencies=[Depends(require_verified_vendor())]
)
def upload_product_images(
    product_id: int,
    images: List[UploadFile] = File(...),            # ← multi-file upload, works cleanly in Swagger
    current_user=Depends(get_current_user),
    service: ProductService = Depends(get_product_service)
):
    """
    Upload one or more images for an existing product.

    - First image is automatically set as primary.
    - Supports JPEG, PNG, WEBP.
    - Max 10 images per product.
    """
    try:
        vendor = (
            service.db.query(VendorProfile)
            .filter(VendorProfile.user_id == current_user["user_id"])
            .first()
        )

        if not vendor:
            raise HTTPException(status_code=403, detail="You are not a vendor")

        return service.upload_product_images(
            vendor_id=vendor.id,
            product_id=product_id,
            images=images
        )

    except ValueError as e:
        log_event("product_image_upload_error", level="warning", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


# # ==================================================
# # UPDATE PRODUCT (VENDOR)
# # ==================================================

# @router.put(
#     "/{product_id}",
#     response_model=ProductResponse,
#     summary="Update Product",
#     dependencies=[Depends(require_verified_vendor())]
# )
# def update_product(
#     product_id: int,
#     payload: ProductUpdate,
#     current_user=Depends(get_current_user),
#     service: ProductService = Depends(get_product_service)
# ):
#     try:
#         vendor = (
#             service.db.query(VendorProfile)
#             .filter(VendorProfile.user_id == current_user["user_id"])
#             .first()
#         )

#         if not vendor:
#             raise HTTPException(status_code=403, detail="You are not a vendor")

#         return service.update_product(vendor.id, product_id, payload)

#     except ValueError as e:
#         log_event("product_update_api_error", level="warning", error=str(e))
#         raise HTTPException(status_code=400, detail=str(e))


# # ==================================================
# # DELETE PRODUCT (VENDOR)
# # ==================================================

# @router.delete(
#     "/{product_id}",
#     summary="Delete Product",
#     dependencies=[Depends(require_verified_vendor())]
# )
# def delete_product(
#     product_id: int,
#     current_user=Depends(get_current_user),
#     service: ProductService = Depends(get_product_service)
# ):
#     try:
#         vendor = (
#             service.db.query(VendorProfile)
#             .filter(VendorProfile.user_id == current_user["user_id"])
#             .first()
#         )

#         if not vendor:
#             raise HTTPException(status_code=403, detail="You are not a vendor")

#         service.delete_product(vendor.id, product_id)
#         return {"message": "Product deleted successfully"}

#     except ValueError as e:
#         log_event("product_delete_api_error", level="warning", error=str(e))
#         raise HTTPException(status_code=400, detail=str(e))
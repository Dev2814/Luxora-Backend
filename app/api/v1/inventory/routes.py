# """
# Inventory Routes
# ================

# API endpoints responsible for inventory management.

# Responsibilities
# ----------------
# • Vendors restock their products
# • Admin manages global inventory
# • Checkout system reserves stock
# • Admin monitors low stock items

# Role Access
# -----------
# Vendor
#     • GET /inventory/{variant_id}
#     • POST /inventory/{variant_id}/increase

# Admin
#     • POST /inventory
#     • POST /inventory/{variant_id}/decrease
#     • GET /inventory
#     • GET /inventory/low-stock

# System / Order Service
#     • POST /inventory/{variant_id}/reserve
#     • POST /inventory/{variant_id}/release

# Architecture
# ------------
# Routes → Service → Repository → Database
# """

# from fastapi import APIRouter, Depends, HTTPException, Query
# from sqlalchemy.orm import Session
# from typing import List

# from app.api.deps import get_db
# from app.api.deps_auth import get_current_user
# from app.core.permissions import require_roles, require_verified_vendor
# from app.core.logger import log_event

# from app.domains.inventory.service import InventoryService

# from app.api.v1.inventory.schemas import (
#     InventoryCreate,
#     InventoryResponse,
#     InventoryListResponse,
#     StockAdjustment
# )

# router = APIRouter(
#     prefix="/inventory",
#     tags=["Inventory"]
# )

# # =========================================================
# # SERVICE DEPENDENCY
# # =========================================================

# def get_inventory_service(db: Session = Depends(get_db)) -> InventoryService:
#     return InventoryService(db)

# # =========================================================
# # LOW STOCK ITEMS (ADMIN)
# # =========================================================

# @router.get(
#     "/low-stock",
#     response_model=List[InventoryResponse],
#     summary="Get Low Stock Items (Admin Only)",
#     dependencies=[Depends(require_roles("admin"))]
# )
# def get_low_stock_items(
#     service: InventoryService = Depends(get_inventory_service)
# ):
#     """
#     Retrieve all inventory items that are below
#     the configured low stock threshold.

#     Accessible only by administrators.
#     """

#     try:

#         return service.get_low_stock_items()

#     except HTTPException as e:

#         if e.status_code == 403:

#             log_event(
#                 "inventory_admin_access_denied",
#                 level="warning",
#                 error="Non-admin attempted admin API access"
#             )

#             raise HTTPException(
#                 status_code=403,
#                 detail="You are not able to use this service. Only admin can access it."
#             )

#         raise e

#     except ValueError as e:

#         log_event(
#             "inventory_low_stock_validation_error",
#             level="warning",
#             error=str(e)
#         )

#         raise HTTPException(status_code=400, detail=str(e))

#     except Exception as e:

#         log_event(
#             "inventory_low_stock_server_error",
#             level="critical",
#             error=str(e)
#         )

#         raise HTTPException(
#             status_code=500,
#             detail="Unable to fetch low stock items"
#         )

# # =========================================================
# # GET INVENTORY BY VARIANT
# # =========================================================

# @router.get(
#     "/{variant_id}",
#     response_model=InventoryResponse,
#     summary="Get Inventory for Variant"
# )
# def get_inventory(
#     variant_id: int,
#     service: InventoryService = Depends(get_inventory_service)
# ):

#     try:

#         return service.get_inventory(variant_id)

#     except ValueError as e:

#         log_event(
#             "inventory_fetch_error",
#             level="warning",
#             error=str(e)
#         )

#         raise HTTPException(status_code=404, detail=str(e))

#     except Exception as e:

#         log_event(
#             "inventory_fetch_server_error",
#             level="critical",
#             error=str(e)
#         )

#         raise HTTPException(
#             status_code=500,
#             detail="Unable to fetch inventory"
#         )

# # =========================================================
# # CREATE INVENTORY (ADMIN)
# # =========================================================

# @router.post(
#     "/",
#     response_model=InventoryResponse,
#     summary="Create Inventory (Admin Only)",
#     dependencies=[Depends(require_roles("admin"))]
# )
# def create_inventory(
#     payload: InventoryCreate,
#     service: InventoryService = Depends(get_inventory_service)
# ):

#     try:

#         return service.create_inventory(
#             variant_id=payload.variant_id,
#             stock=payload.stock,
#             low_stock_threshold=payload.low_stock_threshold
#         )

#     except HTTPException as e:

#         if e.status_code == 403:

#             log_event(
#                 "inventory_admin_access_denied",
#                 level="warning",
#                 error="Non-admin attempted admin API access"
#             )

#             raise HTTPException(
#                 status_code=403,
#                 detail="You are not able to use this service. Only admin can access it."
#             )

#         raise e

#     except ValueError as e:

#         log_event(
#             "inventory_create_validation_error",
#             level="warning",
#             error=str(e)
#         )

#         raise HTTPException(status_code=400, detail=str(e))

#     except Exception as e:

#         log_event(
#             "inventory_create_server_error",
#             level="critical",
#             error=str(e)
#         )

#         raise HTTPException(
#             status_code=500,
#             detail="Unable to create inventory"
#         )

# # =========================================================
# # INCREASE STOCK (VENDOR)
# # =========================================================

# @router.post(
#     "/{variant_id}/increase",
#     response_model=InventoryResponse,
#     summary="Increase Stock (Vendor Restock)",
#     dependencies=[Depends(require_verified_vendor())]
# )
# def increase_stock(
#     variant_id: int,
#     payload: StockAdjustment,
#     service: InventoryService = Depends(get_inventory_service),
#     current_user=Depends(get_current_user)
# ):
#     try:
#         return service.increase_stock(
#             variant_id=variant_id,
#             quantity=payload.quantity,
#             user_id=current_user["user_id"]
#         )

#     except ValueError as e:

#         log_event(
#             "inventory_increase_validation_error",
#             level="warning",
#             error=str(e)
#         )

#         raise HTTPException(status_code=400, detail=str(e))

#     except Exception as e:

#         log_event(
#             "inventory_increase_server_error",
#             level="critical",
#             error=str(e)
#         )

#         raise HTTPException(
#             status_code=500,
#             detail="Unable to increase stock"
#         )
    
# @router.get(
#     "/vendor",
#     response_model=InventoryListResponse,
#     summary="Vendor Inventory",
#     dependencies=[Depends(require_verified_vendor())]
# )
# def list_vendor_inventory(
#     page: int = Query(1, ge=1),
#     limit: int = Query(20, le=100),
#     service: InventoryService = Depends(get_inventory_service),
#     current_user=Depends(get_current_user)
# ):
#     return service.list_vendor_inventory(
#         vendor_id=current_user["user_id"],
#         page=page,
#         limit=limit
#     )

# # =========================================================
# # DECREASE STOCK (ADMIN)
# # =========================================================

# @router.post(
#     "/{variant_id}/decrease",
#     response_model=InventoryResponse,
#     summary="Decrease Stock (Admin Only)",
#     dependencies=[Depends(require_roles("admin"))]
# )
# def decrease_stock(
#     variant_id: int,
#     payload: StockAdjustment,
#     service: InventoryService = Depends(get_inventory_service)
# ):

#     try:

#         return service.decrease_stock(
#             variant_id=variant_id,
#             quantity=payload.quantity
#         )

#     except HTTPException as e:

#         if e.status_code == 403:

#             log_event(
#                 "inventory_admin_access_denied",
#                 level="warning",
#                 error="Non-admin attempted admin API access"
#             )

#             raise HTTPException(
#                 status_code=403,
#                 detail="You are not able to use this service. Only admin can access it."
#             )

#         raise e

#     except ValueError as e:

#         log_event(
#             "inventory_decrease_validation_error",
#             level="warning",
#             error=str(e)
#         )

#         raise HTTPException(status_code=400, detail=str(e))

#     except Exception as e:

#         log_event(
#             "inventory_decrease_server_error",
#             level="critical",
#             error=str(e)
#         )

#         raise HTTPException(
#             status_code=500,
#             detail="Unable to decrease stock"
#         )

# # =========================================================
# # RESERVE STOCK (CHECKOUT SYSTEM)
# # =========================================================

# @router.post(
#     "/{variant_id}/reserve",
#     response_model=InventoryResponse,
#     summary="Reserve Stock (Checkout Process)"
# )
# def reserve_stock(
#     variant_id: int,
#     payload: StockAdjustment,
#     service: InventoryService = Depends(get_inventory_service)
# ):

#     try:

#         return service.reserve_stock(
#             variant_id=variant_id,
#             quantity=payload.quantity
#         )

#     except ValueError as e:

#         log_event(
#             "inventory_reserve_validation_error",
#             level="warning",
#             error=str(e)
#         )

#         raise HTTPException(status_code=400, detail=str(e))

#     except Exception as e:

#         log_event(
#             "inventory_reserve_server_error",
#             level="critical",
#             error=str(e)
#         )

#         raise HTTPException(
#             status_code=500,
#             detail="Unable to reserve stock"
#         )

# # =========================================================
# # RELEASE RESERVED STOCK
# # =========================================================

# @router.post(
#     "/{variant_id}/release",
#     response_model=InventoryResponse,
#     summary="Release Reserved Stock"
# )
# def release_reserved_stock(
#     variant_id: int,
#     payload: StockAdjustment,
#     service: InventoryService = Depends(get_inventory_service)
# ):

#     try:

#         return service.release_reserved_stock(
#             variant_id=variant_id,
#             quantity=payload.quantity
#         )

#     except ValueError as e:

#         log_event(
#             "inventory_release_validation_error",
#             level="warning",
#             error=str(e)
#         )

#         raise HTTPException(status_code=400, detail=str(e))

#     except Exception as e:

#         log_event(
#             "inventory_release_server_error",
#             level="critical",
#             error=str(e)
#         )

#         raise HTTPException(
#             status_code=500,
#             detail="Unable to release reserved stock"
#         )

# # =========================================================
# # LIST INVENTORY (ADMIN)
# # =========================================================

# @router.get(
#     "/",
#     response_model=InventoryListResponse,
#     summary="List Inventory (Admin Only)",
#     dependencies=[Depends(require_roles("admin"))]
# )
# def list_inventory(
#     page: int = Query(1, ge=1),
#     limit: int = Query(20, le=100),
#     service: InventoryService = Depends(get_inventory_service)
# ):

#     try:

#         return service.list_inventory(page, limit)

#     except HTTPException as e:

#         if e.status_code == 403:

#             log_event(
#                 "inventory_admin_access_denied",
#                 level="warning",
#                 error="Non-admin attempted admin API access"
#             )

#             raise HTTPException(
#                 status_code=403,
#                 detail="You are not able to use this service. Only admin can access it."
#             )

#         raise e

#     except Exception as e:

#         log_event(
#             "inventory_list_server_error",
#             level="critical",
#             error=str(e)
#         )

#         raise HTTPException(
#             status_code=500,
#             detail="Unable to fetch inventory list"
#         )



"""
Inventory Routes
================

API endpoints responsible for inventory management.

Responsibilities
----------------
• Vendors restock their products
• Admin manages global inventory
• Checkout system reserves stock
• Admin monitors low stock items

Role Access
-----------
Vendor
    • GET /inventory/{variant_id}
    • POST /inventory/{variant_id}/increase

Admin
    • POST /inventory
    • POST /inventory/{variant_id}/decrease
    • GET /inventory
    • GET /inventory/low-stock

System / Order Service
    • POST /inventory/{variant_id}/reserve
    • POST /inventory/{variant_id}/release

Architecture
------------
Routes → Service → Repository → Database
"""



from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_db
from app.api.deps_auth import get_current_user
from app.core.permissions import require_roles, require_verified_vendor
from app.core.logger import log_event

from app.domains.inventory.service import InventoryService

from app.api.v1.inventory.schemas import (
    InventoryCreate,
    InventoryResponse,
    InventoryListResponse,
    StockAdjustment
)

router = APIRouter(
    prefix="/inventory",
    tags=["Inventory"]
)

# =========================================================
# SERVICE DEPENDENCY
# =========================================================

def get_inventory_service(db: Session = Depends(get_db)) -> InventoryService:
    return InventoryService(db)

# =========================================================
# LOW STOCK ITEMS (ADMIN)
# =========================================================

@router.get(
    "/low-stock",
    response_model=List[InventoryResponse],
    summary="Get Low Stock Items",
    dependencies=[Depends(require_roles("vendor"))]
)
def get_low_stock_items(
    service: InventoryService = Depends(get_inventory_service)
):
    try:
        return service.get_low_stock_items()

    except HTTPException as e:
        if e.status_code == 403:
            log_event(
                "inventory_admin_access_denied",
                level="warning",
                error="Non-admin attempted admin API access"
            )
            raise HTTPException(
                status_code=403,
                detail="You are not able to use this service. Only admin can access it."
            )
        raise e

    except ValueError as e:
        log_event(
            "inventory_low_stock_validation_error",
            level="warning",
            error=str(e)
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        log_event(
            "inventory_low_stock_server_error",
            level="critical",
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail="Unable to fetch low stock items"
        )

# =========================================================
# VENDOR INVENTORY (IMPORTANT: MUST BE ABOVE DYNAMIC ROUTES)
# =========================================================
# NOTE:
# Static routes must be declared BEFORE dynamic routes like "/{variant_id}"
# Otherwise FastAPI will treat "vendor" as variant_id → causing 422 error
# =========================================================

@router.get(
    "/vendor",
    response_model=InventoryListResponse,
    summary="Vendor Inventory",
    dependencies=[Depends(require_verified_vendor())]
)
def list_vendor_inventory(
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=100),
    service: InventoryService = Depends(get_inventory_service),
    current_user=Depends(get_current_user)
):
    return service.list_vendor_inventory(
        user_id=current_user["user_id"],
        page=page,
        limit=limit
    )

# =========================================================
# GET INVENTORY BY VARIANT
# =========================================================
# NOTE:
# This dynamic route must come AFTER static routes
# =========================================================

@router.get(
    "/{variant_id}",
    response_model=InventoryResponse,
    summary="Get Inventory for Variant"
)
def get_inventory(
    variant_id: int,
    service: InventoryService = Depends(get_inventory_service)
):
    try:
        return service.get_inventory(variant_id)

    except ValueError as e:
        log_event(
            "inventory_fetch_error",
            level="warning",
            error=str(e)
        )
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        log_event(
            "inventory_fetch_server_error",
            level="critical",
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail="Unable to fetch inventory"
        )

# =========================================================
# CREATE INVENTORY (ADMIN)
# =========================================================

@router.post(
    "/",
    response_model=InventoryResponse,
    summary="Create Inventory (Admin Only)",
    dependencies=[Depends(require_roles("admin"))]
)
def create_inventory(
    payload: InventoryCreate,
    service: InventoryService = Depends(get_inventory_service)
):
    try:
        return service.create_inventory(
            variant_id=payload.variant_id,
            stock=payload.stock,
            low_stock_threshold=payload.low_stock_threshold
        )

    except HTTPException as e:
        if e.status_code == 403:
            log_event(
                "inventory_admin_access_denied",
                level="warning",
                error="Non-admin attempted admin API access"
            )
            raise HTTPException(
                status_code=403,
                detail="You are not able to use this service. Only admin can access it."
            )
        raise e

    except ValueError as e:
        log_event(
            "inventory_create_validation_error",
            level="warning",
            error=str(e)
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        log_event(
            "inventory_create_server_error",
            level="critical",
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail="Unable to create inventory"
        )

# =========================================================
# INCREASE STOCK (VENDOR)
# =========================================================

@router.post(
    "/{variant_id}/increase",
    response_model=InventoryResponse,
    summary="Increase Stock (Vendor Restock)",
    dependencies=[Depends(require_verified_vendor())]
)
def increase_stock(
    variant_id: int,
    payload: StockAdjustment,
    service: InventoryService = Depends(get_inventory_service),
    current_user=Depends(get_current_user)
):
    try:
        return service.increase_stock(
            variant_id=variant_id,
            quantity=payload.quantity,
            user_id=current_user["user_id"]
        )

    except ValueError as e:
        log_event(
            "inventory_increase_validation_error",
            level="warning",
            error=str(e)
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        log_event(
            "inventory_increase_server_error",
            level="critical",
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail="Unable to increase stock"
        )

# =========================================================
# DECREASE STOCK (ADMIN)
# =========================================================

@router.post(
    "/{variant_id}/decrease",
    response_model=InventoryResponse,
    summary="Decrease Stock (Admin Only)",
    dependencies=[Depends(require_roles("admin"))]
)
def decrease_stock(
    variant_id: int,
    payload: StockAdjustment,
    service: InventoryService = Depends(get_inventory_service)
):
    try:
        return service.decrease_stock(
            variant_id=variant_id,
            quantity=payload.quantity
        )

    except HTTPException as e:
        if e.status_code == 403:
            log_event(
                "inventory_admin_access_denied",
                level="warning",
                error="Non-admin attempted admin API access"
            )
            raise HTTPException(
                status_code=403,
                detail="You are not able to use this service. Only admin can access it."
            )
        raise e

    except ValueError as e:
        log_event(
            "inventory_decrease_validation_error",
            level="warning",
            error=str(e)
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        log_event(
            "inventory_decrease_server_error",
            level="critical",
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail="Unable to decrease stock"
        )

# =========================================================
# RESERVE STOCK (CHECKOUT SYSTEM)
# =========================================================

@router.post(
    "/{variant_id}/reserve",
    response_model=InventoryResponse,
    summary="Reserve Stock (Checkout Process)"
)
def reserve_stock(
    variant_id: int,
    payload: StockAdjustment,
    service: InventoryService = Depends(get_inventory_service)
):
    try:
        return service.reserve_stock(
            variant_id=variant_id,
            quantity=payload.quantity
        )

    except ValueError as e:
        log_event(
            "inventory_reserve_validation_error",
            level="warning",
            error=str(e)
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        log_event(
            "inventory_reserve_server_error",
            level="critical",
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail="Unable to reserve stock"
        )

# =========================================================
# RELEASE RESERVED STOCK
# =========================================================

@router.post(
    "/{variant_id}/release",
    response_model=InventoryResponse,
    summary="Release Reserved Stock"
)
def release_reserved_stock(
    variant_id: int,
    payload: StockAdjustment,
    service: InventoryService = Depends(get_inventory_service)
):
    try:
        return service.release_reserved_stock(
            variant_id=variant_id,
            quantity=payload.quantity
        )

    except ValueError as e:
        log_event(
            "inventory_release_validation_error",
            level="warning",
            error=str(e)
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        log_event(
            "inventory_release_server_error",
            level="critical",
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail="Unable to release reserved stock"
        )

# =========================================================
# LIST INVENTORY (ADMIN)
# =========================================================

@router.get(
    "/",
    response_model=InventoryListResponse,
    summary="List Inventory (Admin Only)",
    dependencies=[Depends(require_roles("admin"))]
)
def list_inventory(
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=100),
    service: InventoryService = Depends(get_inventory_service)
):
    try:
        return service.list_inventory(page, limit)

    except HTTPException as e:
        if e.status_code == 403:
            log_event(
                "inventory_admin_access_denied",
                level="warning",
                error="Non-admin attempted admin API access"
            )
            raise HTTPException(
                status_code=403,
                detail="You are not able to use this service. Only admin can access it."
            )
        raise e

    except Exception as e:
        log_event(
            "inventory_list_server_error",
            level="critical",
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail="Unable to fetch inventory list"
        )
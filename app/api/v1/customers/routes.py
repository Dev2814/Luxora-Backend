"""
Customer Routes
===============

API endpoints responsible for customer profile management.

Responsibilities
----------------
• Customer profile creation
• Retrieve customer profile
• Update customer information
• Admin customer listing

Role Access
-----------
Customer
    • POST /customers/profile
    • GET /customers/profile
    • PUT /customers/profile

Admin
    • GET /customers

Architecture
------------
Routes → Service → Repository → Database
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_db
from app.api.deps_auth import get_current_user
from app.core.permissions import require_roles
from app.core.logger import log_event

from app.domains.customers.service import CustomerService

from app.api.v1.customers.schemas import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    CustomerListResponse
)

# =========================================================
# ROUTER CONFIGURATION
# =========================================================

router = APIRouter(
    prefix="/customers",
    tags=["Customers"]
)


# =========================================================
# SERVICE DEPENDENCY
# =========================================================

def get_customer_service(db: Session = Depends(get_db)) -> CustomerService:
    """
    Dependency injection for CustomerService.
    """
    return CustomerService(db)


# =========================================================
# CREATE CUSTOMER PROFILE
# =========================================================

@router.post(
    "/profile",
    response_model=CustomerResponse,
    summary="Create Customer Profile"
)
def create_customer_profile(
    payload: CustomerCreate,
    service: CustomerService = Depends(get_customer_service),
    current_user=Depends(get_current_user)
):
    """
    Create a customer profile for the authenticated user.
    """

    try:

        return service.create_customer_profile(
            user_id=current_user["user_id"],
            payload=payload
        )

    except ValueError as e:

        log_event(
            "customer_create_validation_error",
            level="warning",
            user_id=current_user["user_id"],
            error=str(e)
        )

        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:

        log_event(
            "customer_create_server_error",
            level="critical",
            user_id=current_user["user_id"],
            error=str(e)
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to create customer profile"
        )


# =========================================================
# GET CUSTOMER PROFILE
# =========================================================

@router.get(
    "/profile",
    response_model=CustomerResponse,
    summary="Get Customer Profile"
)
def get_customer_profile(
    service: CustomerService = Depends(get_customer_service),
    current_user=Depends(get_current_user)
):
    """
    Retrieve the profile of the authenticated customer.
    """

    try:

        return service.get_customer_profile(
            user_id=current_user["user_id"]
        )

    except ValueError as e:

        log_event(
            "customer_fetch_error",
            level="warning",
            user_id=current_user["user_id"],
            error=str(e)
        )

        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:

        log_event(
            "customer_fetch_server_error",
            level="critical",
            user_id=current_user["user_id"],
            error=str(e)
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to fetch customer profile"
        )


# =========================================================
# UPDATE CUSTOMER PROFILE
# =========================================================

@router.put(
    "/profile",
    response_model=CustomerResponse,
    summary="Update Customer Profile"
)
def update_customer_profile(
    payload: CustomerUpdate,
    service: CustomerService = Depends(get_customer_service),
    current_user=Depends(get_current_user)
):
    """
    Update profile information for the authenticated customer.
    """

    try:

        return service.update_customer_profile(
            user_id=current_user["user_id"],
            payload=payload
        )

    except ValueError as e:

        log_event(
            "customer_update_validation_error",
            level="warning",
            user_id=current_user["user_id"],
            error=str(e)
        )

        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:

        log_event(
            "customer_update_server_error",
            level="critical",
            user_id=current_user["user_id"],
            error=str(e)
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to update customer profile"
        )


# =========================================================
# LIST CUSTOMERS (ADMIN)
# =========================================================

@router.get(
    "/",
    response_model=CustomerListResponse,
    summary="List Customers (Admin Only)",
    dependencies=[Depends(require_roles("admin"))]
)
def list_customers(
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=100),
    service: CustomerService = Depends(get_customer_service)
):
    """
    Retrieve paginated list of customers.

    Accessible only by administrators.
    """

    try:

        return service.list_customers(page, limit)

    except Exception as e:

        log_event(
            "customer_list_server_error",
            level="critical",
            error=str(e)
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to fetch customers"
        )
"""
Address Routes
==============

API endpoints responsible for user address management.

Responsibilities
----------------
• Create address
• Retrieve user addresses
• Retrieve single address
• Update address
• Delete address

Role Access
-----------
Authenticated User
    • POST   /addresses
    • GET    /addresses
    • GET    /addresses/{id}
    • PUT    /addresses/{id}
    • DELETE /addresses/{id}

Architecture
------------
Routes → Service → Repository → Database
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_db
from app.api.deps_auth import get_current_user
from app.core.logger import log_event

from app.domains.addresses.service import AddressService

from app.api.v1.addresses.schemas import (
    AddressCreate,
    AddressUpdate,
    AddressResponse
)

# =========================================================
# ROUTER CONFIGURATION
# =========================================================

router = APIRouter(
    prefix="/addresses",
    tags=["User Addresses"]
)

# =========================================================
# SERVICE DEPENDENCY
# =========================================================

def get_address_service(db: Session = Depends(get_db)) -> AddressService:
    return AddressService(db)

# =========================================================
# CREATE ADDRESS
# =========================================================

@router.post(
    "/",
    response_model=AddressResponse,
    summary="Create User Address"
)
def create_address(
    payload: AddressCreate,
    service: AddressService = Depends(get_address_service),
    current_user=Depends(get_current_user)
):

    try:

        return service.create_address(
            user_id=current_user["user_id"],
            payload=payload
        )

    except ValueError as e:

        log_event(
            "address_create_validation_error",
            level="warning",
            user_id=current_user["user_id"],
            error=str(e)
        )

        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:

        log_event(
            "address_create_server_error",
            level="critical",
            user_id=current_user["user_id"],
            error=str(e)
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to create address"
        )


# =========================================================
# LIST USER ADDRESSES
# =========================================================

@router.get(
    "/",
    response_model=List[AddressResponse],
    summary="Get User Addresses"
)
def list_addresses(
    service: AddressService = Depends(get_address_service),
    current_user=Depends(get_current_user)
):

    try:

        return service.get_user_addresses(
            user_id=current_user["user_id"]
        )

    except Exception as e:

        log_event(
            "address_list_server_error",
            level="critical",
            user_id=current_user["user_id"],
            error=str(e)
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to fetch addresses"
        )


# =========================================================
# GET SINGLE ADDRESS
# =========================================================

@router.get(
    "/{address_id}",
    response_model=AddressResponse,
    summary="Get Address"
)
def get_address(
    address_id: int,
    service: AddressService = Depends(get_address_service),
    current_user=Depends(get_current_user)
):

    try:

        return service.get_address(
            user_id=current_user["user_id"],
            address_id=address_id
        )

    except ValueError as e:

        log_event(
            "address_fetch_error",
            level="warning",
            user_id=current_user["user_id"],
            error=str(e)
        )

        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:

        log_event(
            "address_fetch_server_error",
            level="critical",
            user_id=current_user["user_id"],
            error=str(e)
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to fetch address"
        )


# =========================================================
# UPDATE ADDRESS
# =========================================================

@router.put(
    "/{address_id}",
    response_model=AddressResponse,
    summary="Update Address"
)
def update_address(
    address_id: int,
    payload: AddressUpdate,
    service: AddressService = Depends(get_address_service),
    current_user=Depends(get_current_user)
):

    try:

        return service.update_address(
            user_id=current_user["user_id"],
            address_id=address_id,
            payload=payload
        )

    except ValueError as e:

        log_event(
            "address_update_validation_error",
            level="warning",
            user_id=current_user["user_id"],
            error=str(e)
        )

        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:

        log_event(
            "address_update_server_error",
            level="critical",
            user_id=current_user["user_id"],
            error=str(e)
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to update address"
        )


# =========================================================
# DELETE ADDRESS
# =========================================================

@router.delete(
    "/{address_id}",
    summary="Delete Address"
)
def delete_address(
    address_id: int,
    service: AddressService = Depends(get_address_service),
    current_user=Depends(get_current_user)
):

    try:

        service.delete_address(
            user_id=current_user["user_id"],
            address_id=address_id
        )

        return {"message": "Address deleted successfully"}

    except ValueError as e:

        log_event(
            "address_delete_validation_error",
            level="warning",
            user_id=current_user["user_id"],
            error=str(e)
        )

        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:

        log_event(
            "address_delete_server_error",
            level="critical",
            user_id=current_user["user_id"],
            error=str(e)
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to delete address"
        )
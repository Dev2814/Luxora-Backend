"""
Attribute Routes

API endpoints for managing product attributes and variant attribute assignments.

Architecture:
Route → Service → Repository → Database
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_db
from app.core.permissions import require_role
from app.core.logger import log_event

from app.domains.attributes.service import (
    AttributeService,
    VariantAttributeService
)

from app.api.v1.attributes.schemas import (
    AttributeCreate,
    AttributeValueCreate,
    AttributeResponse,
    AttributeValueResponse,
    VariantAttributeAssign,
    AttributeTreeResponse
)


router = APIRouter(
    prefix="/attributes",
    tags=["Attributes"]
)


# ==================================================
# SERVICE DEPENDENCIES
# ==================================================

def get_attribute_service(db: Session = Depends(get_db)):
    return AttributeService(db)


def get_variant_attribute_service(db: Session = Depends(get_db)):
    return VariantAttributeService(db)


# ==================================================
# LIST ATTRIBUTES
# ==================================================

@router.get(
    "/",
    response_model=List[AttributeResponse],
    summary="List all attributes"
)
def list_attributes(
    service: AttributeService = Depends(get_attribute_service)
):

    return service.list_attributes()


# ==================================================
# CREATE ATTRIBUTE
# ==================================================

@router.post(
    "/",
    response_model=AttributeResponse,
    dependencies=[Depends(require_role("admin"))],
    summary="Create attribute"
)
def create_attribute(
    payload: AttributeCreate,
    service: AttributeService = Depends(get_attribute_service)
):

    try:

        attribute = service.create_attribute(payload.name)

        return attribute

    except ValueError as e:

        log_event(
            "attribute_create_error",
            level="warning",
            error=str(e)
        )

        raise HTTPException(status_code=400, detail=str(e))


# ==================================================
# ADD ATTRIBUTE VALUE
# ==================================================

@router.post(
    "/{attribute_id}/values",
    response_model=AttributeValueResponse,
    dependencies=[Depends(require_role("admin"))],
    summary="Create attribute value"
)
def add_attribute_value(
    attribute_id: int,
    payload: AttributeValueCreate,
    service: AttributeService = Depends(get_attribute_service)
):

    try:

        return service.add_attribute_value(
            attribute_id,
            payload.value
        )

    except ValueError as e:

        log_event(
            "attribute_value_create_error",
            level="warning",
            attribute_id=attribute_id,
            error=str(e)
        )

        raise HTTPException(status_code=400, detail=str(e))


# ==================================================
# LIST ATTRIBUTE VALUES
# ==================================================

@router.get(
    "/{attribute_id}/values",
    response_model=List[AttributeValueResponse],
    summary="List attribute values"
)
def list_attribute_values(
    attribute_id: int,
    service: AttributeService = Depends(get_attribute_service)
):

    try:

        return service.list_attribute_values(attribute_id)

    except ValueError as e:

        raise HTTPException(status_code=400, detail=str(e))


# ==================================================
# VARIANT ATTRIBUTE ROUTES
# ==================================================

@router.post(
    "/variants/{variant_id}",
    dependencies=[Depends(require_role("vendor"))],
    summary="Assign attributes to variant"
)
def assign_variant_attributes(
    variant_id: int,
    payload: VariantAttributeAssign,
    service: VariantAttributeService = Depends(get_variant_attribute_service)
):

    try:

        return service.assign_variant_attributes(
            variant_id,
            payload.attribute_value_ids
        )

    except ValueError as e:

        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/variants/{variant_id}",
    summary="Get variant attributes"
)
def get_variant_attributes(
    variant_id: int,
    service: VariantAttributeService = Depends(get_variant_attribute_service)
):

    return service.get_variant_attributes(variant_id)

# ==================================================
# ATTRIBUTE TREE
# ==================================================
@router.get(
    "/tree",
    response_model=List[AttributeTreeResponse],
    summary="List attributes with values (tree structure)"
)
def get_attribute_tree(
    service: AttributeService = Depends(get_attribute_service)
):
    """
    Retrieve attributes along with their values.

    Use Cases:
    - Product creation UI
    - Variant builder
    - Filters (frontend faceted search)

    Performance:
    - Uses optimized eager loading
    """

    return service.get_attribute_tree()
"""
Category Routes

API endpoints for category management.

Responsibilities:
- Public category browsing
- Category tree retrieval
- Admin category creation

Architecture:
Client → API Routes → Service → Repository → Database
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.permissions import require_role
from app.core.logger import log_event

from app.domains.categories.service import CategoryService

from app.api.v1.categories.schemas import (
    CategoryCreate,
    CategoryResponse,
    CategoryTreeResponse
)

router = APIRouter(
    prefix="/categories",
    tags=["Categories"]
)

# ==================================================
# SERVICE DEPENDENCY
# ==================================================

def get_category_service(
    db: Session = Depends(get_db)
) -> CategoryService:
    """
    Dependency injection for CategoryService.
    """
    return CategoryService(db)

# ==================================================
# LIST CATEGORIES (PUBLIC)
# ==================================================

@router.get(
    "/",
    response_model=list[CategoryResponse],
    summary="List All Categories"
)
def list_categories(
    service: CategoryService = Depends(get_category_service)
):

    try:
        categories = service.list_categories()

        log_event(
            "category_list_accessed",
            total=len(categories)
        )

        return categories

    except ValueError as e:

        log_event(
            "category_list_api_error",
            level="error",
            error=str(e)
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# # ==================================================
# # GET ROOT CATEGORIES (PARENTS ONLY)
# # ==================================================

# @router.get(
#     "/parents",
#     response_model=list[CategoryResponse],
#     summary="Get Parent Categories"
# )
# def get_parent_categories(
#     service: CategoryService = Depends(get_category_service)
# ):

#     try:
#         return service.get_root_categories()

#     except ValueError as e:
#         raise HTTPException(status_code=400, detail=str(e))

# ==================================================
# 🔥 NEW: GET CHILD CATEGORIES
# ==================================================

@router.get(
    "/{parent_id}/children",
    response_model=list[CategoryResponse],
    summary="Get Child Categories"
)
def get_child_categories(
    parent_id: int,
    service: CategoryService = Depends(get_category_service)
):
    """
    Fetch all direct children of a given parent category.

    Example:
    Electronics → Mobiles, Laptops
    """

    try:

        categories = [
            c for c in service.list_categories()
            if c.parent_id == parent_id
        ]

        return categories

    except Exception as e:

        log_event(
            "category_children_error",
            level="error",
            parent_id=parent_id,
            error=str(e)
        )

        raise HTTPException(status_code=400, detail="Unable to fetch children")

# ==================================================
# CATEGORY TREE (PUBLIC)
# ==================================================

@router.get(
    "/tree",
    response_model=list[CategoryTreeResponse],
    summary="Get Category Tree"
)
def get_category_tree(
    service: CategoryService = Depends(get_category_service)
):

    try:

        tree = service.get_category_tree()

        log_event(
            "category_tree_accessed",
            root_nodes=len(tree)
        )

        return tree

    except ValueError as e:

        log_event(
            "category_tree_api_error",
            level="error",
            error=str(e)
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# ==================================================
# CREATE CATEGORY (ADMIN ONLY)
# ==================================================

@router.post(
    "/",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Category (Admin Only)",
    dependencies=[Depends(require_role("admin"))]
)
def create_category(
    payload: CategoryCreate,
    service: CategoryService = Depends(get_category_service)
):

    try:

        category = service.create_category(payload)

        log_event(
            "category_created_api",
            category_id=category.id
        )

        return category

    except ValueError as e:

        log_event(
            "category_create_api_error",
            level="warning",
            error=str(e)
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# ==================================================
# CREATE SUBCATEGORY (CLEAN VERSION)
# ==================================================

@router.post(
    "/{parent_id}/sub",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Subcategory",
    dependencies=[Depends(require_role("admin"))]
)
def create_subcategory(
    parent_id: int,
    payload: CategoryCreate,
    service: CategoryService = Depends(get_category_service)
):

    try:

        return service.create_subcategory(parent_id, payload)

    except ValueError as e:

        log_event(
            "subcategory_create_error",
            level="warning",
            error=str(e)
        )

        raise HTTPException(status_code=400, detail=str(e))
    
    
# ==================================================
# GET PARENTS + CATEGORIES WITH CHILDREN + COUNT
# ==================================================

@router.get(
    "/with-children",
    response_model=list[CategoryResponse],
    summary="Get Root + Categories That Have Children"
)
def get_categories_with_children(
    service: CategoryService = Depends(get_category_service)
):
    """
    Returns:
    • Root categories (parent_id = NULL)
    • Categories that have children
    • Includes children_count

    Useful for:
    • Mega menus
    • Navigation systems
    """

    try:

        categories = service.list_categories()

        # ----------------------------------------
        # BUILD CHILD COUNT MAP
        # ----------------------------------------
        children_count_map = {}

        for c in categories:
            if c.parent_id:
                children_count_map[c.parent_id] = (
                    children_count_map.get(c.parent_id, 0) + 1
                )

        # ----------------------------------------
        # FILTER + ADD COUNT
        # ----------------------------------------
        result = []

        for c in categories:

            if (c.parent_id is None) or (c.id in children_count_map):

                # inject dynamic field
                c.children_count = children_count_map.get(c.id, 0)

                result.append(c)

        return result

    except Exception as e:

        log_event(
            "categories_with_children_error",
            level="error",
            error=str(e)
        )

        raise HTTPException(
            status_code=400,
            detail="Unable to fetch categories"
        )
    
@router.get(
    "/roots",
    response_model=list[CategoryResponse],
    summary="Get Root Categories"
)
def get_root_categories_strict(
    service: CategoryService = Depends(get_category_service)
):
    
    """
    Returns ONLY categories where:
    • parent_id is NULL

    This is a strict version for:
    • Top navigation
    • Homepage category display
    """

    try:

        result = service.get_root_categories()

        return result
    
    except Exception as e:


        log_event(
            "root_categories_strict_error",
            level="error",
            error=str(e)
        )
        raise HTTPException(
            status_code=400, 
            detail="Unable to fetch root categories"
        )
    
    
# ==================================================
# 🔥 GET SUBCATEGORIES (parent_id NOT NULL)
# ==================================================

@router.get(
    "/subcategories",
    response_model=list[CategoryResponse],
    summary="Get All Subcategories"
)
def get_subcategories(
    service: CategoryService = Depends(get_category_service)
):
    """
    Returns ONLY subcategories:
    • Categories where parent_id is NOT NULL

    This includes:
    • Child categories
    • Sub-child categories
    • All nested levels except root

    Useful for:
    • Product filtering
    • Admin panel
    • Category mapping
    """

    try:

        categories = service.list_categories()

        # Filter subcategories
        result = [c for c in categories if c.parent_id is not None]

        return result

    except Exception as e:

        log_event(
            "subcategories_fetch_error",
            level="error",
            error=str(e)
        )

        raise HTTPException(
            status_code=400,
            detail="Unable to fetch subcategories"
        )    
    
@router.get(
    "/level-one",
    response_model=list[CategoryResponse],
    summary="Get Level-1 Categories (Mobiles Type Only)"
)
def get_level_one_categories(
    service: CategoryService = Depends(get_category_service)
):
    """
    Returns ONLY:
    • Categories whose parent is root

    Example:
    Electronics → Mobiles
    """

    try:

        return service.get_level_one_categories()

    except Exception as e:

        log_event(
            "level_one_categories_api_error",
            level="error",
            error=str(e)
        )

        raise HTTPException(
            status_code=400,
            detail="Unable to fetch level-1 categories"
        )
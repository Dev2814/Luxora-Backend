"""
Category Service

Handles business logic related to product categories.

Responsibilities:
- Create categories
- Create subcategories (clean REST)
- List categories
- Build category tree
- Fetch category descendants

Architecture:
API → Service → Repository → Database
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.domains.categories.repository import CategoryRepository
from app.models.category import Category  # ✅ FIXED IMPORT
from app.core.logger import log_event


class CategoryService:

    def __init__(self, db: Session):
        self.db = db
        self.repo = CategoryRepository(db)

    # ==================================================
    # LIST CATEGORIES
    # ==================================================

    def list_categories(self):
        try:
            return self.repo.get_all_categories()

        except SQLAlchemyError as e:
            log_event(
                "category_list_error",
                level="critical",
                error=str(e)
            )
            raise ValueError("Unable to fetch categories")

    # ==================================================
    # CREATE CATEGORY (ROOT)
    # ==================================================

    def create_category(self, payload):
        try:

            # -------------------------
            # SLUG VALIDATION
            # -------------------------
            existing = self.repo.get_by_slug(payload.slug)
            if existing:
                raise ValueError("Category slug already exists")

            # -------------------------
            # NORMALIZE PARENT
            # -------------------------
            parent_id = payload.parent_id or None

            if parent_id:
                parent = self.repo.get_by_id(parent_id)
                if not parent:
                    raise ValueError("Parent category not found")

            # -------------------------
            # CREATE CATEGORY
            # -------------------------
            category = self.repo.create_category(
                name=payload.name,
                slug=payload.slug,
                parent_id=parent_id,
                description=payload.description,
                meta_title=payload.meta_title,
                meta_description=payload.meta_description
            )

            log_event(
                "category_created",
                category_id=category.id,
                parent_id=parent_id
            )

            return category

        except ValueError:
            raise

        except SQLAlchemyError as e:

            self.repo.rollback()

            log_event(
                "category_create_error",
                level="critical",
                error=str(e)
            )

            raise ValueError("Unable to create category")

    # ==================================================
    # CREATE SUBCATEGORY (PRODUCTION FIXED)
    # ==================================================

    def create_subcategory(self, parent_id: int, payload):
        """
        Create subcategory using parent_id from route.

        Best Practice:
        - parent_id from URL
        - payload contains only category data
        """

        try:

            # -------------------------
            # VALIDATE PARENT
            # -------------------------
            parent = self.repo.get_by_id(parent_id)
            if not parent:
                raise ValueError("Parent category not found")

            # -------------------------
            # SLUG VALIDATION
            # -------------------------
            existing = self.repo.get_by_slug(payload.slug)
            if existing:
                raise ValueError("Category slug already exists")

            # -------------------------
            # CREATE SUBCATEGORY
            # -------------------------
            category = self.repo.create_category(
                name=payload.name,
                slug=payload.slug,
                parent_id=parent_id,
                description=payload.description,
                meta_title=payload.meta_title,
                meta_description=payload.meta_description
            )

            log_event(
                "subcategory_created",
                category_id=category.id,
                parent_id=parent_id
            )

            return category

        except ValueError:
            raise

        except SQLAlchemyError as e:

            self.repo.rollback()

            log_event(
                "subcategory_create_error",
                level="critical",
                parent_id=parent_id,
                error=str(e)
            )

            raise ValueError("Unable to create subcategory")

    # ==================================================
    # GET ROOT CATEGORIES
    # ==================================================

    def get_root_categories(self):
        try:
            return self.repo.get_root_categories()

        except Exception as e:
            log_event(
                "root_categories_error",
                level="error",
                error=str(e)
            )
            raise ValueError("Unable to fetch parent categories")

    # ==================================================
    # GET CHILDREN (🔥 NEW)
    # ==================================================

    def get_children(self, category_id: int):
        """
        Fetch direct children of a category.
        """

        try:

            parent = self.repo.get_by_id(category_id)

            if not parent:
                raise ValueError("Category not found")

            return self.repo.get_children(category_id)

        except Exception as e:

            log_event(
                "category_children_error",
                level="error",
                category_id=category_id,
                error=str(e)
            )

            raise ValueError("Unable to fetch children")

    # ==================================================
    # CATEGORY TREE
    # ==================================================

    def get_category_tree(self):

        try:

            categories = self.repo.get_all_categories()

            category_map = {}
            root_nodes = []

            for category in categories:
                category_map[category.id] = {
                    "id": category.id,
                    "name": category.name,
                    "slug": category.slug,
                    "parent_id": category.parent_id,
                    "children": []
                }

            for category in category_map.values():
                parent_id = category["parent_id"]

                if parent_id and parent_id in category_map:
                    category_map[parent_id]["children"].append(category)
                else:
                    root_nodes.append(category)

            log_event(
                "category_tree_fetched",
                total=len(root_nodes)
            )

            return root_nodes

        except SQLAlchemyError as e:

            log_event(
                "category_tree_error",
                level="critical",
                error=str(e)
            )

            raise ValueError("Unable to build category tree")

    # ==================================================
    # GET DESCENDANT IDS
    # ==================================================

    def get_descendant_ids(self, category_id: int):

        try:

            categories = self.repo.get_all_categories()

            children_map = {}

            for category in categories:
                children_map.setdefault(category.parent_id, []).append(category.id)

            result = []

            def collect(cid):
                result.append(cid)
                for child in children_map.get(cid, []):
                    collect(child)

            collect(category_id)

            return result

        except Exception as e:

            log_event(
                "category_descendant_error",
                level="error",
                category_id=category_id,
                error=str(e)
            )

            return []
        

    def get_level_one_categories(self):
        """
        Returns only level-1 categories (e.g., Mobiles).
        No children, no roots.
        """

        try:
            return self.repo.get_level_one_categories()

        except Exception as e:
            log_event(
                "level_one_categories_error",
                level="error",
                error=str(e)
            )
            raise ValueError("Unable to fetch level-1 categories")
"""
Category Repository

Handles all database operations for categories.

Responsibilities:
- Fetch categories
- Create categories
- Retrieve category by ID / slug
- Maintain clean database access layer

Architecture:
Service → Repository → Database
"""

from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.category import Category
from sqlalchemy.orm import aliased


class CategoryRepository:

    def __init__(self, db: Session):
        self.db = db

    # ==================================================
    # GET ALL CATEGORIES
    # ==================================================

    def get_all_categories(self) -> List[Category]:

        return (
            self.db.query(Category)
            .filter(Category.is_deleted == False)
            .order_by(Category.sort_order.asc())
            .all()
        )

    # ==================================================
    # GET CATEGORY BY ID
    # ==================================================

    def get_by_id(self, category_id: int) -> Optional[Category]:

        return (
            self.db.query(Category)
            .filter(
                Category.id == category_id,
                Category.is_deleted == False
            )
            .first()
        )

    # ==================================================
    # GET CATEGORY BY SLUG
    # ==================================================

    def get_by_slug(self, slug: str) -> Optional[Category]:

        return (
            self.db.query(Category)
            .filter(
                Category.slug == slug,
                Category.is_deleted == False
            )
            .first()
        )

    # ==================================================
    # CREATE CATEGORY
    # ==================================================

    def create_category(
        self,
        name: str,
        slug: str,
        parent_id: int | None = None,
        description: str | None = None,
        meta_title: str | None = None,
        meta_description: str | None = None
    ) -> Category:

        category = Category(
            name=name,
            slug=slug,
            parent_id=parent_id,
            description=description,
            meta_title=meta_title,
            meta_description=meta_description
        )

        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)

        return category

    # ==================================================
    # UPDATE CATEGORY
    # ==================================================

    def update_category(self, category: Category, data: dict) -> Category:

        for field, value in data.items():
            setattr(category, field, value)

        self.db.commit()
        self.db.refresh(category)

        return category

    # ==================================================
    # GET ROOT CATEGORIES (PARENT ONLY)
    # ==================================================

    def get_root_categories(self):
        """
        Fetch only top-level categories (parent_id is NULL).
        """

        return (
            self.db.query(Category)
            .filter(
                Category.parent_id.is_(None),
                Category.is_deleted == False,
                Category.is_active == True
            )
            .order_by(Category.sort_order.asc())
            .all()
        )

    # ==================================================
    # GET CHILD CATEGORIES (🔥 NEW)
    # ==================================================

    def get_children(self, parent_id: int):
        """
        Fetch direct children of a category.
        """

        return (
            self.db.query(Category)
            .filter(
                Category.parent_id == parent_id,
                Category.is_deleted == False,
                Category.is_active == True
            )
            .order_by(Category.sort_order.asc())
            .all()
        )
    

    def get_level_one_categories(self):
        """
        Fetch ONLY level-1 categories:
        - Categories whose parent is root
        """

        Parent = aliased(Category)

        return (
            self.db.query(Category)
            .join(Parent, Category.parent_id == Parent.id)
            .filter(
                Parent.parent_id.is_(None),  # Parent is root
                Category.is_deleted == False,
                Category.is_active == True
            )
            .order_by(Category.sort_order.asc())
            .all()
        )

    # ==================================================
    # DELETE CATEGORY (SOFT DELETE)
    # ==================================================

    def soft_delete(self, category: Category):

        category.is_deleted = True

        self.db.commit()

    # ==================================================
    # TRANSACTION CONTROL
    # ==================================================

    def rollback(self):
        self.db.rollback()
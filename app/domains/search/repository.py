"""
Search Repository

Handles product search queries.

Responsibilities
----------------
• Keyword search
• Brand filtering
• Category filtering
• Price filtering
• Sorting
• Pagination

Architecture
------------
Service → Repository → Database
"""

from sqlalchemy.orm import Session
from sqlalchemy import or_, asc, desc

from app.models.product import Product
from sqlalchemy.orm import joinedload
from app.models.product_image import ProductImage
from app.models.category import Category


class SearchRepository:
    """
    Repository responsible for querying products
    for search and filtering operations.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_all_child_categories(self, category_id):
        ids = [category_id]

        children = self.db.query(Category).filter(
            Category.parent_id == category_id
        ).all()

        for child in children:
            ids.extend(self.get_all_child_categories(child.id))

        return ids

    # =========================================================
    # PRODUCT SEARCH
    # =========================================================

    def search_products(
        self,
        keyword: str | None = None,
        brand_id: int | None = None,
        category_id: int | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        sort_by: str | None = None,
        page: int = 1,
        limit: int = 20,
    ):

        query = self.db.query(Product).filter(
            Product.is_active == True,
            Product.is_deleted == False
        ).options(
            joinedload(Product.images)  # 🔥 LOAD IMAGES
        )

        # ---------------- KEYWORD ----------------
        if keyword:
            keyword_filter = f"%{keyword}%"
            query = query.filter(
                or_(
                    Product.name.ilike(keyword_filter),
                    Product.description.ilike(keyword_filter)
                )
            )

        # ---------------- FILTERS ----------------
        if brand_id:
            query = query.filter(Product.brand_id == brand_id)

        # if category_id:
        #     query = query.filter(Product.category_id == category_id)

        if category_id:
            category_ids = self.get_all_child_categories(category_id)

            query = query.filter(Product.category_id.in_(category_ids))

        if min_price:
            query = query.filter(Product.price >= min_price)

        if max_price:
            query = query.filter(Product.price <= max_price)

        # ---------------- SORT ----------------
        if sort_by == "price_asc":
            query = query.order_by(asc(Product.price))
        elif sort_by == "price_desc":
            query = query.order_by(desc(Product.price))
        else:
            query = query.order_by(desc(Product.created_at))

        # ---------------- TOTAL ----------------
        total = query.count()

        # ---------------- PAGINATION ----------------
        offset = (page - 1) * limit
        products = query.offset(offset).limit(limit).all()

        # 🔥 BUILD RESPONSE WITH PRIMARY IMAGE
        items = []

        for product in products:

            primary_image = None

            if product.images:
                for img in product.images:
                    if getattr(img, "is_primary", False):
                        primary_image = img.image_url
                        break

                if not primary_image:
                    primary_image = product.images[0].image_url

            items.append({
                "id": product.id,
                "name": product.name,
                "slug": product.slug,
                "price": product.price,
                "compare_price": product.compare_price,
                "brand_id": product.brand_id,
                "category_id": product.category_id,
                "is_active": product.is_active,
                "primary_image": primary_image
            })

        return total, items
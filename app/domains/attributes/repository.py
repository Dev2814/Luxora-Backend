"""
Attribute Repository

Responsible for database access for the Product Attribute system.

Architecture:
Service Layer → Repository → Database

Responsibilities:
- Manage product attributes
- Manage attribute values
- Manage variant attribute assignments

This repository strictly handles database operations.
Business validation should be handled in the service layer.
"""

from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import IntegrityError

from app.models.product_attribute import (
    ProductAttribute,
    ProductAttributeMap,
    ProductAttributeValue
)

# from app.models.product_attribute_value import (
#     ProductAttributeValue,
# )

# from app.models.product_attribute_map import (
#     ProductAttributeMap,
# )


# =========================================================
# ATTRIBUTE REPOSITORY
# =========================================================

class AttributeRepository:
    """
    Repository responsible for ProductAttribute
    and ProductAttributeValue operations.
    """

    def __init__(self, db: Session):
        self.db = db

    # -----------------------------------------------------
    # CREATE ATTRIBUTE
    # -----------------------------------------------------

    def create_attribute(self, name: str) -> ProductAttribute:
        """
        Create a new product attribute.

        Example:
            Color
            Size
            Storage

        Raises:
            ValueError: If attribute already exists
        """

        attribute = ProductAttribute(name=name.strip())

        try:
            self.db.add(attribute)
            self.db.commit()
            self.db.refresh(attribute)

        except IntegrityError:
            self.db.rollback()
            raise ValueError("Attribute already exists")

        return attribute

    # -----------------------------------------------------
    # LIST ATTRIBUTES
    # -----------------------------------------------------

    def list_attributes(self):
        """
        Retrieve all non-deleted attributes.
        """

        return (
            self.db.query(ProductAttribute)
            .filter(ProductAttribute.is_deleted == False)
            .order_by(ProductAttribute.name.asc())
            .all()
        )

    # -----------------------------------------------------
    # GET ATTRIBUTE BY ID
    # -----------------------------------------------------

    def get_attribute_by_id(self, attribute_id: int):
        """
        Fetch a single attribute by ID.
        """

        return (
            self.db.query(ProductAttribute)
            .filter(
                ProductAttribute.id == attribute_id,
                ProductAttribute.is_deleted == False
            )
            .first()
        )

    # -----------------------------------------------------
    # CREATE ATTRIBUTE VALUE
    # -----------------------------------------------------

    def create_attribute_value(
        self,
        attribute_id: int,
        value: str
    ) -> ProductAttributeValue:
        """
        Create a value for an attribute.

        Example:

        Attribute: Color
        Values:
            Red
            Blue
            Black
        """

        attribute_value = ProductAttributeValue(
            attribute_id=attribute_id,
            value=value.strip()
        )

        try:

            self.db.add(attribute_value)
            self.db.commit()
            self.db.refresh(attribute_value)

        except IntegrityError:

            self.db.rollback()
            raise ValueError("Attribute value already exists")

        return attribute_value

    # -----------------------------------------------------
    # LIST ATTRIBUTE VALUES
    # -----------------------------------------------------

    def list_attribute_values(self, attribute_id: int):
        """
        Retrieve values belonging to a specific attribute.
        """

        return (
            self.db.query(ProductAttributeValue)
            .filter(
                ProductAttributeValue.attribute_id == attribute_id,
                ProductAttributeValue.is_deleted == False
            )
            .order_by(ProductAttributeValue.value.asc())
            .all()
        )
    
     # -----------------------------------------------------
    # ATTRIBUTE TREE (ATTRIBUTE + VALUES)
    # -----------------------------------------------------
    def get_attribute_tree(self):
        """
        Fetch attributes along with their values.

        Optimized using eager loading to avoid N+1 queries.

        Returns:
            List[ProductAttribute]
        """
        return (
            self.db.query(ProductAttribute)
            .options(
                selectinload(ProductAttribute.values)
            )
            .filter(ProductAttribute.is_deleted == False)
            .order_by(ProductAttribute.name.asc())
            .all()
        )


# =========================================================
# VARIANT ATTRIBUTE REPOSITORY
# =========================================================

class VariantAttributeRepository:
    """
    Repository responsible for assigning attribute values
    to product variants.

    Example:

        Variant: iPhone Black 128GB

        Attribute mappings:
            Color   -> Black
            Storage -> 128GB
    """

    def __init__(self, db: Session):
        self.db = db

    # -----------------------------------------------------
    # ASSIGN ATTRIBUTES TO VARIANT
    # -----------------------------------------------------

    def assign_attributes(
        self,
        variant_id: int,
        attribute_value_ids: list[int]
    ):
        """
        Assign attribute values to a variant.

        Example:
            Variant: iPhone 15 Black 128GB

            attribute_value_ids:
                [black_id, storage_128_id]
        """

        records = [
            ProductAttributeMap(
                variant_id=variant_id,
                attribute_value_id=value_id
            )
            for value_id in attribute_value_ids
        ]

        try:

            self.db.add_all(records)
            self.db.commit()

            for record in records:
                self.db.refresh(record)

        except IntegrityError:

            self.db.rollback()
            raise ValueError("Duplicate attribute assignment")

        return records

    # -----------------------------------------------------
    # GET VARIANT ATTRIBUTES
    # -----------------------------------------------------

    def get_variant_attributes(self, variant_id: int):
        """
        Retrieve attribute mappings for a variant.
        """

        return (
            self.db.query(ProductAttributeMap)
            .filter(ProductAttributeMap.variant_id == variant_id)
            .all()
        )

    # -----------------------------------------------------
    # DELETE VARIANT ATTRIBUTES
    # -----------------------------------------------------

    def delete_variant_attributes(self, variant_id: int):
        """
        Remove all attribute assignments for a variant.

        Useful when updating variant attributes.
        """

        (
            self.db.query(ProductAttributeMap)
            .filter(ProductAttributeMap.variant_id == variant_id)
            .delete()
        )

        self.db.commit()

   
"""
Attribute Service

Handles business logic for product attributes and attribute values.

Architecture:
API → Service → Repository → Database

Responsibilities:
- Create attributes
- Manage attribute values
- Assign attributes to product variants
"""

from sqlalchemy.orm import Session

from app.domains.attributes.repository import (
    AttributeRepository,
    VariantAttributeRepository,
)

from app.core.logger import log_event


# ==================================================
# ATTRIBUTE SERVICE
# ==================================================

class AttributeService:
    """
    Handles business logic for attribute management.
    """

    def __init__(self, db: Session):

        self.repo = AttributeRepository(db)

    # --------------------------------------------------
    # CREATE ATTRIBUTE
    # --------------------------------------------------

    def create_attribute(self, name: str):

        """
        Create a new product attribute.

        Example:
            Color
            Size
            Storage
        """

        name = name.strip()

        if not name:
            raise ValueError("Attribute name is required")

        attribute = self.repo.create_attribute(name)

        log_event(
            "attribute_created",
            attribute_id=attribute.id,
            name=attribute.name
        )

        return attribute

    # --------------------------------------------------
    # LIST ATTRIBUTES
    # --------------------------------------------------

    def list_attributes(self):

        """
        Retrieve all attributes.
        """

        return self.repo.list_attributes()

    # --------------------------------------------------
    # CREATE ATTRIBUTE VALUE
    # --------------------------------------------------

    def add_attribute_value(self, attribute_id: int, value: str):

        """
        Add value to an attribute.

        Example:

            Attribute: Color
            Value: Red
        """

        value = value.strip()

        if not value:
            raise ValueError("Attribute value is required")

        attribute = self.repo.get_attribute_by_id(attribute_id)

        if not attribute:
            raise ValueError("Attribute not found")

        attribute_value = self.repo.create_attribute_value(
            attribute_id,
            value
        )

        log_event(
            "attribute_value_created",
            attribute_id=attribute_id,
            value_id=attribute_value.id
        )

        return attribute_value

    # --------------------------------------------------
    # LIST ATTRIBUTE VALUES
    # --------------------------------------------------

    def list_attribute_values(self, attribute_id: int):

        """
        Fetch all values for an attribute.
        """

        attribute = self.repo.get_attribute_by_id(attribute_id)

        if not attribute:
            raise ValueError("Attribute not found")

        return self.repo.list_attribute_values(attribute_id)
    
        
    # --------------------------------------------------
    # ATTRIBUTE TREE
    # --------------------------------------------------
    def get_attribute_tree(self):
        """
        Retrieve attribute tree including values.

        Enterprise Notes:
        - Uses repository optimized query
        - Filters soft-deleted values (defensive layer)
        """

        attributes = self.repo.get_attribute_tree()

        # Defensive filtering (important in production)
        for attr in attributes:
            attr.values = [
                v for v in attr.values if not v.is_deleted
            ]

        return attributes

        # Filter soft-deleted values at service level (safety layer)
        for attr in attributes:
            attr.values = [
                v for v in attr.values if not v.is_deleted
            ]

        return attributes


# ==================================================
# VARIANT ATTRIBUTE SERVICE
# ==================================================

class VariantAttributeService:
    """
    Handles assignment of attribute values to product variants.
    """

    def __init__(self, db: Session):

        self.repo = VariantAttributeRepository(db)

    # --------------------------------------------------
    # ASSIGN ATTRIBUTES TO VARIANT
    # --------------------------------------------------

    def assign_variant_attributes(
        self,
        variant_id: int,
        attribute_value_ids: list[int]
    ):

        """
        Assign attribute values to a variant.

        Example:

            Variant: iPhone Black 128GB

            Attributes:
                Color -> Black
                Storage -> 128GB
        """

        if not attribute_value_ids:
            raise ValueError("Attributes required")

        records = self.repo.assign_attributes(
            variant_id,
            attribute_value_ids
        )

        log_event(
            "variant_attributes_assigned",
            variant_id=variant_id,
            total=len(attribute_value_ids)
        )

        return records

    # --------------------------------------------------
    # GET VARIANT ATTRIBUTES
    # --------------------------------------------------

    def get_variant_attributes(self, variant_id: int):

        """
        Retrieve attributes assigned to a variant.
        """

        return self.repo.get_variant_attributes(variant_id)

    # --------------------------------------------------
    # UPDATE VARIANT ATTRIBUTES
    # --------------------------------------------------

    def update_variant_attributes(
        self,
        variant_id: int,
        attribute_value_ids: list[int]
    ):

        """
        Replace all attributes assigned to a variant.
        """

        if not attribute_value_ids:
            raise ValueError("Attributes required")

        self.repo.delete_variant_attributes(variant_id)

        records = self.repo.assign_attributes(
            variant_id,
            attribute_value_ids
        )

        log_event(
            "variant_attributes_updated",
            variant_id=variant_id,
            total=len(attribute_value_ids)
        )

        return records
    
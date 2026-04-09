"""
Invoice Model
=============

Stores invoice metadata for orders.

Purpose
-------
• Track generated invoice PDFs
• Store invoice number
• Provide download link

Architecture
------------
Order
   │
   └── Invoice
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    Index
)

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.models.base import Base


class Invoice(Base):

    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)

    order_id = Column(
        Integer,
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )

    invoice_number = Column(
        String(50),
        nullable=False,
        unique=True
    )

    pdf_path = Column(
        String(255),
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    order = relationship(
        "Order", 
        back_populates="invoice",
    )

    __table_args__ = (
        Index("idx_invoice_order", "order_id"),
    )
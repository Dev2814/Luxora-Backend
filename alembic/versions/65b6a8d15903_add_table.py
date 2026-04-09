"""add table 

Revision ID: 65b6a8d15903
Revises: 49777f3b2b73
Create Date: 2026-04-06 12:25:52.828431

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '65b6a8d15903'
down_revision: Union[str, Sequence[str], None] = '49777f3b2b73'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

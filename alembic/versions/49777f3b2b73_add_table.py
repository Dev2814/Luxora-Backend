"""add table 

Revision ID: 49777f3b2b73
Revises: 4eab6d062ea9
Create Date: 2026-04-06 12:23:01.767462

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '49777f3b2b73'
down_revision: Union[str, Sequence[str], None] = '4eab6d062ea9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

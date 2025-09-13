"""migration_manual

Revision ID: rev20250913T183706
Revises: rev20250913T183652
Create Date: 2025-09-13 21:37:06.843739

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'rev20250913T183706'
down_revision: Union[str, None] = 'rev20250913T183652'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

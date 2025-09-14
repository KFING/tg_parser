"""migration_manual

Revision ID: rev20250914T193527
Revises: rev20250913T183706
Create Date: 2025-09-14 22:35:27.984638

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'rev20250914T193527'
down_revision: Union[str, None] = 'rev20250913T183706'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

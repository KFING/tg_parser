"""migration_manual

Revision ID: rev20250903T202042
Revises: rev20250903T201912
Create Date: 2025-09-03 23:20:42.471913

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'rev20250903T202042'
down_revision: Union[str, None] = 'rev20250903T201912'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

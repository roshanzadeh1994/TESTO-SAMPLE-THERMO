"""Add data column to DeviceInspection

Revision ID: 9b7496ee3d0a
Revises: 41f066769364
Create Date: 2024-12-13 15:16:53.717467

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9b7496ee3d0a'
down_revision: Union[str, None] = '41f066769364'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

"""Add incremental crawl statistics

Revision ID: 8b4e0f5f2a1c
Revises: cd360119ffea
Create Date: 2026-08-31

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8b4e0f5f2a1c"
down_revision: Union[str, Sequence[str], None] = "cd360119ffea"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "crawl_jobs",
        sa.Column("pages_new", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "crawl_jobs",
        sa.Column("pages_changed", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "crawl_jobs",
        sa.Column("pages_unchanged", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "crawl_jobs",
        sa.Column("pages_deactivated", sa.Integer(), server_default="0", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("crawl_jobs", "pages_deactivated")
    op.drop_column("crawl_jobs", "pages_unchanged")
    op.drop_column("crawl_jobs", "pages_changed")
    op.drop_column("crawl_jobs", "pages_new")

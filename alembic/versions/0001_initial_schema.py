"""initial schema

Revision ID: 0001
Revises: 
Create Date: 2026-08-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "hero_profile",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("tagline", sa.Text(), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("email", sa.String(200), nullable=True),
        sa.Column("github_url", sa.String(500), nullable=True),
        sa.Column("linkedin_url", sa.String(500), nullable=True),
        sa.Column("resume_url", sa.String(500), nullable=True),
        sa.Column("profile_picture", sa.Text(), nullable=True),
        sa.Column("location", sa.String(200), nullable=True),
        sa.Column("years_experience", sa.String(50), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "experiences",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("company", sa.String(200), nullable=False),
        sa.Column("company_url", sa.String(500), nullable=True),
        sa.Column("role", sa.String(200), nullable=False),
        sa.Column("start_date", sa.String(50), nullable=False),
        sa.Column("end_date", sa.String(50), nullable=True),
        sa.Column("is_current", sa.Boolean(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("technologies", sa.JSON(), nullable=True),
        sa.Column("location", sa.String(200), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "projects",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("long_description", sa.Text(), nullable=True),
        sa.Column("technologies", sa.JSON(), nullable=True),
        sa.Column("live_url", sa.String(500), nullable=True),
        sa.Column("github_url", sa.String(500), nullable=True),
        sa.Column("images", sa.JSON(), nullable=True),
        sa.Column("is_featured", sa.Boolean(), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "skills",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("proficiency", sa.Integer(), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("skills")
    op.drop_table("projects")
    op.drop_table("experiences")
    op.drop_table("hero_profile")

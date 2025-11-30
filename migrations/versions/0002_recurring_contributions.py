"""add recurring contribution fields

Revision ID: 0002
Revises: 0001
Create Date: 2025-11-24 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def _column_exists(connection, table_name, column_name):
    inspector = sa.inspect(connection)
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade():
    bind = op.get_bind()

    if not _column_exists(bind, "user_asset", "monthly_contribution"):
        op.add_column(
            "user_asset",
            sa.Column(
                "monthly_contribution",
                sa.Float(),
                nullable=False,
                server_default="0",
            ),
        )

    if not _column_exists(bind, "user_asset", "yearly_contribution"):
        op.add_column(
            "user_asset",
            sa.Column(
                "yearly_contribution",
                sa.Float(),
                nullable=False,
                server_default="0",
            ),
        )

    op.execute("UPDATE user_asset SET monthly_contribution = 0 WHERE monthly_contribution IS NULL")
    op.execute("UPDATE user_asset SET yearly_contribution = 0 WHERE yearly_contribution IS NULL")


def downgrade():
    bind = op.get_bind()
    if _column_exists(bind, "user_asset", "yearly_contribution"):
        op.drop_column("user_asset", "yearly_contribution")
    if _column_exists(bind, "user_asset", "monthly_contribution"):
        op.drop_column("user_asset", "monthly_contribution")

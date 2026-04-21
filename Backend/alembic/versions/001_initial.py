"""Initial schema — users, assets, decisions (pgvector), signals

Revision ID: 001_initial
Revises:
Create Date: 2025-01-01 00:00:00.000000
"""
from __future__ import annotations
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable required PostgreSQL extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    # ── users ──────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_superuser", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ── assets ─────────────────────────────────────────────────────────────
    op.create_table(
        "assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ticker", sa.String(20), nullable=False),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("asset_class", sa.String(50), nullable=False, server_default="equity"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("ix_assets_user_id", "assets", ["user_id"])
    op.create_unique_constraint("uq_asset_user_ticker", "assets", ["user_id", "ticker"])

    # ── decisions ──────────────────────────────────────────────────────────
    op.create_table(
        "decisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ticker", sa.Text, nullable=False),
        sa.Column("bull_thesis", sa.Text, nullable=False, server_default=""),
        sa.Column("bear_thesis", sa.Text, nullable=False, server_default=""),
        sa.Column("arbiter_reasoning", sa.Text, nullable=False, server_default=""),
        sa.Column("bull_sources", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("bear_sources", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("market_context", postgresql.JSONB, nullable=False, server_default="{}"),
        # pgvector column — 1536 dims for text-embedding-3-small
        sa.Column("embedding", sa.Column("embedding",
            sa.Text).type if False else
            sa.column("embedding").type if False else
            # Raw DDL for pgvector — Alembic doesn't know the type natively
            sa.Text,  # placeholder; replaced by raw SQL below
            nullable=True),
        sa.Column("status", sa.Text, nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    # Replace TEXT placeholder with actual vector column
    op.execute("ALTER TABLE decisions DROP COLUMN IF EXISTS embedding")
    op.execute("ALTER TABLE decisions ADD COLUMN embedding vector(1536)")
    op.create_index("ix_decisions_user_id", "decisions", ["user_id"])
    op.create_index("ix_decisions_ticker_created", "decisions", ["ticker", "created_at"])
    # IVFFlat index for cosine similarity search
    op.execute(
        "CREATE INDEX ix_decisions_embedding_ivfflat ON decisions "
        "USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )

    # ── trading_signals ────────────────────────────────────────────────────
    op.create_table(
        "trading_signals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("assets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("decision_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("decisions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("signal", sa.String(10), nullable=False),
        sa.Column("bull_confidence", sa.Numeric(5, 4), nullable=False),
        sa.Column("bear_confidence", sa.Numeric(5, 4), nullable=False),
        sa.Column("net_confidence", sa.Numeric(5, 4), nullable=False),
        sa.Column("price_at_signal", sa.Numeric(18, 6), nullable=True),
        sa.Column("currency", sa.String(10), nullable=False, server_default="USD"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("ix_signals_asset_id", "trading_signals", ["asset_id"])
    op.create_index("ix_signals_created_at", "trading_signals", ["created_at"])


def downgrade() -> None:
    op.drop_table("trading_signals")
    op.execute("DROP INDEX IF EXISTS ix_decisions_embedding_ivfflat")
    op.drop_table("decisions")
    op.drop_table("assets")
    op.drop_table("users")

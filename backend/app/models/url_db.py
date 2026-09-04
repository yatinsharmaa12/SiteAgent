from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.core.time import now_utc_naive
from app.db.database import Base


class URL(Base):
    __tablename__ = "urls"

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "normalized_url",
            name="uq_company_normalized_url",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )

    url: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
    )

    normalized_url: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    depth: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    discovered_from: Mapped[Optional[str]] = mapped_column(
        String(2048),
        nullable=True,
    )

    first_discovered_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=now_utc_naive,
        nullable=False,
    )

    last_crawled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )

    crawl_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    http_status: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    last_error: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    # New fields for incremental crawl tracking
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
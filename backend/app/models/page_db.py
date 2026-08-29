from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Page(Base):
    __tablename__ = "pages"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )

    url_id: Mapped[int] = mapped_column(
        ForeignKey("urls.id", ondelete="CASCADE"),
        nullable=False,
    )

    url: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
    )

    title: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    http_status: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    content_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    crawled_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
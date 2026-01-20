from datetime import datetime, timezone

from sqlalchemy import (
    CHAR,
    TIMESTAMP,
    VARCHAR,
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    PrimaryKeyConstraint,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, mapped_column


def utcnow():
    """Return the current timestamp in UTC."""
    return datetime.now(timezone.utc)


class Base(MappedAsDataclass, DeclarativeBase):
    pass


class LinkedPlayer(Base):
    __tablename__ = "linked_players"

    discord_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    uuid: Mapped[str] = mapped_column(CHAR(36), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(16), unique=True, nullable=False)

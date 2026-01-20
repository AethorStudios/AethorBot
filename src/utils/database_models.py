from datetime import UTC, datetime

from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass


def utcnow():
    """Return the current timestamp in UTC."""
    return datetime.now(UTC)


class Base(MappedAsDataclass, DeclarativeBase):
    pass

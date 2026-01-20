# /modules/database_async.py

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import selectinload

from src.utils.config import ConfigModel, get_config

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

AsyncSQLSession: async_sessionmaker[AsyncSession]


def get_current_session() -> AsyncSession:
    """Get a new asynchronous SQLAlchemy session."""
    global AsyncSQLSession
    if not AsyncSQLSession:
        raise RuntimeError("AsyncSQLSession is not initialized.")
    return AsyncSQLSession()


def initialize_local_database() -> async_sessionmaker[AsyncSession]:
    """Initialize the local SQLite database connection."""
    global AsyncSQLSession
    config: ConfigModel = get_config()
    connection_string = f"sqlite+aiosqlite:///{config.bot.local_database_path}"

    _engine = create_async_engine(
        connection_string, pool_size=5, max_overflow=10, pool_pre_ping=True, pool_recycle=1800
    )

    AsyncSQLSession = async_sessionmaker(
        bind=_engine,
        expire_on_commit=False,
        autoflush=True,
        class_=AsyncSession,
    )

    return AsyncSQLSession

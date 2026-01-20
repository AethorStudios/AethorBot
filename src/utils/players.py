from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import select

from src.utils.database.database_models import LinkedPlayer
from src.utils.database.sql_database import get_current_session


async def set_player(discord_id: int, uuid: UUID, username: str) -> LinkedPlayer:
    async with get_current_session() as session:
        async with session.begin():
            new_player = LinkedPlayer(
                discord_id=discord_id,
                uuid=str(uuid),
                username=username,
            )
            session.add(new_player)
            return new_player


async def edit_player(discord_id: int, uuid: UUID, username: str) -> LinkedPlayer | None:
    async with get_current_session() as session:
        async with session.begin():
            result = await session.execute(select(LinkedPlayer).where(LinkedPlayer.discord_id == discord_id))
            player = result.scalars().first()
            if player:
                player.uuid = str(uuid)
                player.username = username
                session.add(player)
                return player
    return None


async def get_player(discord_id: int) -> LinkedPlayer | None:
    async with get_current_session() as session:
        result = await session.execute(select(LinkedPlayer).where(LinkedPlayer.discord_id == discord_id))
        player = result.scalars().first()
        return player


async def get_players() -> list[LinkedPlayer]:
    async with get_current_session() as session:
        result = await session.execute(select(LinkedPlayer))
        players = result.scalars().all()
        return players


async def unlink_player(discord_id: int) -> None:
    async with get_current_session() as session:
        async with session.begin():
            result = await session.execute(select(LinkedPlayer).where(LinkedPlayer.discord_id == discord_id))
            player = result.scalars().first()
            if player:
                await session.delete(player)

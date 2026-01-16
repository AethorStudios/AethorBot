import json
from base64 import b64decode
from uuid import UUID

import aiohttp
from yarl import URL

from src.utils.models import MinecraftUser

MINECRAFT_API_URL = URL("https://api.minecraftservices.com/")


# ============== REQUEST FUNCTIONS ==============


async def get_json(url: URL) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=10) as resp:
            resp.raise_for_status()
            return await resp.json()


async def post_json(url: URL, json_data: dict) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=json_data, timeout=10) as resp:
            resp.raise_for_status()
            return await resp.json()


# ============== MOJANG FUNCTIONS ==============


async def fetch_player_by_uuid(uuid: UUID) -> MinecraftUser:
    if not uuid:
        return None
    url = MINECRAFT_API_URL / "minecraft/profile/lookup" / str(uuid)

    data = await get_json(url)
    if data:
        if data.get("errorMessage"):
            return None
        username = data.get("name")
        return MinecraftUser(uuid=uuid, username=username)


async def fetch_player_by_username(name: str) -> MinecraftUser:
    if not name:
        return None, None
    name = name.strip()
    url = MINECRAFT_API_URL / "minecraft/profile/lookup/name/" / name

    data = await get_json(url)
    if data:
        if data.get("errorMessage"):
            return None
        uuid = UUID(data.get("id"))
        username = data.get("name")
        return MinecraftUser(uuid=uuid, username=username)


async def fetch_player_textures(uuid: UUID) -> dict:
    url = URL("https://sessionserver.mojang.com/session/minecraft/profile/") / str(uuid)
    data = await get_json(url)

    value_encoded = data.get("properties", [{}])[0].get("value")
    value = b64decode(value_encoded).decode("utf-8")
    textures = json.loads(value).get("textures", {})
    return textures

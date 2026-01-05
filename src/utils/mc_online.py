from mcstatus import JavaServer

from src.config import ConfigModel, get_config
from src.utils import rcon

CONFIG: ConfigModel = get_config()


def _parse_list_output(raw: str) -> list[str]:
    # Typical: "There are X of a max of Y players online: name1, name2"
    if ":" in raw:
        names = raw.split(":", 1)[1]
        return [n.strip() for n in names.split(",") if n.strip()]
    return []


async def online_players() -> list[str]:
    # Prefer RCON if available for reliability
    if rcon.is_enabled():
        try:
            raw = rcon.send_command("list")
            names = _parse_list_output(raw)
            return names
        except Exception:
            pass

    # Fallback to mcstatus
    if not CONFIG.minecraft.address:
        return []
    try:
        server = JavaServer.lookup(CONFIG.minecraft.address)
        # Try full query first (requires enable-query=true on server)
        try:
            q = await server.async_query()
            if getattr(q.players, "names", None):
                return [str(n) for n in q.players.names if str(n).strip()]
        except Exception:
            # If query fails, try status sample (may be incomplete)
            status = await server.async_status()
            sample = getattr(status.players, "sample", None)
            if sample:
                return [p.name for p in sample if getattr(p, "name", None)]
    except Exception:
        pass
    return []


async def is_player_online(name: str) -> bool:
    name = name.strip()
    if not name:
        return False
    names = await online_players()
    name_lower = name.lower()
    return any(n.lower() == name_lower for n in names)

from mcrcon import MCRcon

from src.utils.config import ConfigModel, get_config

CONFIG: ConfigModel = get_config()


def is_enabled() -> bool:
    return CONFIG.minecraft.rcon.enabled and CONFIG.minecraft.rcon.password.get_secret_value() != ""


def send_command(cmd: str) -> str:
    if not is_enabled():
        raise RuntimeError("RCON is not enabled or missing password.")
    with MCRcon(
        CONFIG.minecraft.rcon.host, CONFIG.minecraft.rcon.password.get_secret_value, port=CONFIG.minecraft.rcon.port
    ) as mcr:
        resp = mcr.command(cmd)
        return resp or ""


def whitelist_add(name: str) -> str:
    name = name.strip()
    if not name:
        raise ValueError("Empty name")
    return send_command(f"whitelist add {name}")


def whitelist_remove(name: str) -> str:
    name = name.strip()
    if not name:
        raise ValueError("Empty name")
    return send_command(f"whitelist remove {name}")


def whitelist_list() -> list[str]:
    raw = send_command("whitelist list")
    # Typical response: "There are N whitelisted players: name1, name2"
    parts = raw.split(":", 1)
    if len(parts) == 2:
        names = [n.strip() for n in parts[1].split(",") if n.strip()]
        return names
    # Some servers may return just comma-separated names
    if "," in raw:
        return [n.strip() for n in raw.split(",") if n.strip()]
    return [raw.strip()] if raw.strip() else []

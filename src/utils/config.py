from __future__ import annotations

from os import getenv
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, SecretStr, ValidationError
from pydantic.types import NonNegativeInt, PositiveInt  # noqa

if TYPE_CHECKING:
    import discord

    from src.bot import AethorBot

load_dotenv()
CONFIG: ConfigModel | None = None
BOT: AethorBot | None = None


# ============== CONFIG MODELS ==============


class RolesConfig(BaseModel):
    verified_role_id: NonNegativeInt = 0
    mute_role_id: NonNegativeInt = 0
    admin_role_ids: list[NonNegativeInt] = Field(default_factory=list)

    @property
    def verified_role(self) -> discord.Role | None:
        if BOT and self.verified_role_id != 0 and BOT.config.bot.guild:
            return BOT.config.bot.guild.get_role(int(self.verified_role_id))
        return None

    @property
    def mute_role(self) -> discord.Role | None:
        if BOT and self.mute_role_id != 0 and BOT.config.bot.guild:
            return BOT.config.bot.guild.get_role(int(self.mute_role_id))
        return None

    @property
    def admin_roles(self) -> list[discord.Role]:
        roles: list[discord.Role] = []
        if BOT and BOT.config.bot.guild:
            guild = BOT.config.bot.guild
            for role_id in self.admin_role_ids:
                role = guild.get_role(int(role_id))
                if role:
                    roles.append(role)
        return roles


class ChannelsConfig(BaseModel):
    log_channel_id: NonNegativeInt = 0
    mod_log_channel_id: NonNegativeInt = 0
    verify_log_channel_id: NonNegativeInt = 0

    @property
    def log_channel(self) -> discord.TextChannel | None:
        if BOT and self.log_channel_id != 0:
            return BOT.get_channel(int(self.log_channel_id))
        return None

    @property
    def mod_log_channel(self) -> discord.TextChannel | None:
        if BOT and self.mod_log_channel_id != 0:
            return BOT.get_channel(int(self.mod_log_channel_id))
        return None

    @property
    def verify_log_channel(self) -> discord.TextChannel | None:
        if BOT and self.verify_log_channel_id != 0:
            return BOT.get_channel(int(self.verify_log_channel_id))
        return None


class AutoSyncConfig(BaseModel):
    enabled: bool = False
    hour: NonNegativeInt = 3
    minute: NonNegativeInt = 0
    remove_extras: bool = False
    cooldown_seconds: NonNegativeInt = 30


class FileLogsConfig(BaseModel):
    enabled: bool = True
    path: Path = Path("logs/aethor.log")
    max_bytes: NonNegativeInt = 1_048_576
    backup_count: NonNegativeInt = 5


class BotConfig(BaseModel):
    token: SecretStr = Field(default=SecretStr(""))
    guild_id: NonNegativeInt = 0
    application_id: NonNegativeInt = 0

    roles: RolesConfig = Field(default_factory=RolesConfig)
    channels: ChannelsConfig = Field(default_factory=ChannelsConfig)
    auto_sync: AutoSyncConfig = Field(default_factory=AutoSyncConfig)
    logs: FileLogsConfig = Field(default_factory=FileLogsConfig)

    @property
    def guild(self) -> discord.Guild | None:
        if BOT:
            return BOT.get_guild(int(self.guild_id))
        return None


class RconConfig(BaseModel):
    enabled: bool = False
    host: str = "127.0.0.1"
    port: PositiveInt = 25575
    password: SecretStr | None = None


class BackupConfig(BaseModel):
    enabled: bool = True
    max_keep: NonNegativeInt = 10


class HealthcheckConfig(BaseModel):
    enabled: bool = True
    port: PositiveInt = int(getenv("PORT", "8080"))


class MinecraftConfig(BaseModel):
    host: str = "play.example.com"
    port: PositiveInt = 25565

    rcon: RconConfig = Field(default_factory=RconConfig)
    whitelist_backup: BackupConfig = Field(default_factory=BackupConfig)
    healthcheck: HealthcheckConfig = Field(default_factory=HealthcheckConfig)

    @property
    def address(self) -> str:
        return f"{self.host}:{self.port}"


class ConfigModel(BaseModel):
    """
    Root config.
    - Defaults come from Pydantic
    - Unknown keys dropped on validate
    """

    model_config = ConfigDict(extra="ignore")

    bot: BotConfig = Field(default_factory=BotConfig)
    minecraft: MinecraftConfig = Field(default_factory=MinecraftConfig)

    def validate_required_runtime(self) -> None:
        """
        Enforce that placeholders were replaced.
        Call this after load, before actually running the bot.
        """
        token = self.bot.token.get_secret_value().strip()
        if not token or token == "":
            raise RuntimeError("bot.token is not set.")

        required_ids = {
            "bot.guild_id": self.bot.guild_id,
            "bot.application_id": self.bot.application_id,
            "bot.roles.verified_role_id": self.bot.roles.verified_role_id,
            "bot.roles.mute_role_id": self.bot.roles.mute_role_id,
            "bot.channels.log_channel_id": self.bot.channels.log_channel_id,
            "bot.channels.mod_log_channel_id": self.bot.channels.mod_log_channel_id,
            "bot.channels.verify_log_channel_id": self.bot.channels.verify_log_channel_id,
        }
        missing = [k for k, v in required_ids.items() if int(v) == 0]
        if missing:
            raise RuntimeError(f"Missing required config IDs (still 0): {', '.join(missing)}")


# ============== CONFIG FUNCTIONS ==============


class InvalidYamlError(RuntimeError):
    pass


def _is_in_file(search_value: str, file: Path) -> bool:
    if not search_value:
        return False
    try:
        return search_value.casefold() in file.read_text(encoding="utf-8").casefold()
    except FileNotFoundError:
        return False
    except Exception as e:
        raise InvalidYamlError(f"Failed reading {file}: {e}") from e


def _load_yaml_mapping(file: Path) -> dict[str, Any]:
    try:
        raw = yaml.safe_load(file.read_text(encoding="utf-8")) if file.exists() else None
    except Exception as e:
        raise InvalidYamlError(f"Failed parsing YAML {file}: {e}") from e

    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise InvalidYamlError(f"{file} must contain a YAML mapping/object at the top level.")
    return raw


def _keys_shape(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _keys_shape(v) for k, v in obj.items()}
    return None


def _yaml_safe(obj: Any) -> Any:
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, SecretStr):
        return obj.get_secret_value()
    if isinstance(obj, dict):
        return {k: _yaml_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_yaml_safe(v) for v in obj]
    return obj


def save_config(path: Path, config: ConfigModel) -> None:
    data = _yaml_safe(config.model_dump(exclude_unset=False, mode="python"))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, indent=4)


def set_global_config(config: ConfigModel) -> None:
    global CONFIG
    CONFIG = config


def load_config(path: str | Path, *, update_if_has_string: str = "") -> ConfigModel:
    """
    - Create if missing (using ConfigModel defaults)
    - Load + validate
    - Rewrite if schema changed (missing keys) or legacy marker found
    - Unknown keys dropped on rewrite
    """
    path = Path(path)
    default = ConfigModel()  # <--- pure defaults, no template dict

    if not path.is_file():
        global CONFIG
        save_config(path, default)
        CONFIG = default
        default.validate_required_runtime()
        return default

    raw = _load_yaml_mapping(path)

    try:
        config = ConfigModel.model_validate(raw)
    except ValidationError as e:
        raise InvalidYamlError(f"Invalid config file {path}:\n{e}") from e

    expected_shape = _keys_shape(default.model_dump(exclude_unset=False, mode="python"))
    actual_shape = _keys_shape(raw)
    needs_update = (expected_shape != actual_shape) or _is_in_file(update_if_has_string, path)

    if needs_update:
        save_config(path, config)

    config.validate_required_runtime()
    set_global_config(config)
    return config


def resolve_config_values(bot: AethorBot) -> None:
    global BOT
    BOT = bot


def get_config() -> ConfigModel:
    if CONFIG is None:
        raise RuntimeError("Config not loaded yet. Call load_config() first.")
    return CONFIG

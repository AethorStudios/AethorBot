from __future__ import annotations

from pathlib import Path
from typing import Any, Optional
from os import getenv

from dotenv import load_dotenv

import yaml
from pydantic import BaseModel, ConfigDict, Field, SecretStr, ValidationError, computed_field
from pydantic.types import NonNegativeInt, PositiveInt  # noqa

load_dotenv()
CONFIG: ConfigModel | None = None

# Models


class DiscordConfig(BaseModel):
    token: SecretStr = Field(default=SecretStr(""))
    guild_id: NonNegativeInt = 0
    application_id: NonNegativeInt = 0


class RolesConfig(BaseModel):
    verified_role_id: NonNegativeInt = 0
    mute_role_id: NonNegativeInt = 0
    admin_role_ids: list[NonNegativeInt] = Field(default_factory=list)


class ChannelsConfig(BaseModel):
    log_channel_id: NonNegativeInt = 0
    mod_log_channel_id: NonNegativeInt = 0
    verify_log_channel_id: NonNegativeInt = 0


class AutoSyncConfig(BaseModel):
    enabled: bool = False
    hour: NonNegativeInt = 3
    minute: NonNegativeInt = 0
    remove_extras: bool = False
    cooldown_seconds: NonNegativeInt = 30


class MinecraftConfig(BaseModel):
    host: str = "play.example.com"
    port: PositiveInt = 25565

    @property
    def address(self) -> str:
        return f"{self.host}:{self.port}"


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


class FileLogsConfig(BaseModel):
    enabled: bool = True
    path: Path = Path("logs/aethor.log")
    max_bytes: NonNegativeInt = 1_048_576
    backup_count: NonNegativeInt = 5


class ConfigModel(BaseModel):
    """
    Root config.
    - Defaults come from Pydantic
    - Unknown keys dropped on validate
    """

    model_config = ConfigDict(extra="ignore")

    discord: DiscordConfig = Field(default_factory=DiscordConfig)
    roles: RolesConfig = Field(default_factory=RolesConfig)
    channels: ChannelsConfig = Field(default_factory=ChannelsConfig)

    minecraft: MinecraftConfig = Field(default_factory=MinecraftConfig)
    rcon: RconConfig = Field(default_factory=RconConfig)
    auto_sync: AutoSyncConfig = Field(default_factory=AutoSyncConfig)
    backup: BackupConfig = Field(default_factory=BackupConfig)
    healthcheck: HealthcheckConfig = Field(default_factory=HealthcheckConfig)
    file_logs: FileLogsConfig = Field(default_factory=FileLogsConfig)

    def validate_required_runtime(self) -> None:
        """
        Enforce that placeholders were replaced.
        Call this after load, before actually running the bot.
        """
        token = self.discord.token.get_secret_value().strip()
        if not token or token == "":
            raise RuntimeError("discord.token is not set.")

        # Discord IDs should be real snowflakes, not 0.
        # If you ever *want* to allow 0 for some env, loosen these.
        required_ids = {
            "discord.guild_id": self.discord.guild_id,
            "discord.application_id": self.discord.application_id,
            "roles.verified_role_id": self.roles.verified_role_id,
            "roles.mute_role_id": self.roles.mute_role_id,
            "channels.log_channel_id": self.channels.log_channel_id,
            "channels.mod_log_channel_id": self.channels.mod_log_channel_id,
            "channels.verify_log_channel_id": self.channels.verify_log_channel_id,
        }
        missing = [k for k, v in required_ids.items() if int(v) == 0]
        if missing:
            raise RuntimeError(f"Missing required config IDs (still 0): {', '.join(missing)}")


# -----------------------------
# Loader / saver (CDL-style)
# -----------------------------


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
        yaml.safe_dump(data, f, sort_keys=False)


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


def get_config() -> ConfigModel:
    if CONFIG is None:
        raise RuntimeError("Config not loaded yet. Call load_config() first.")
    return CONFIG

from __future__ import annotations

import argparse
from argparse import ArgumentParser, BooleanOptionalAction
from pathlib import Path

from pydantic import BaseModel, Field


class RuntimeArgs(BaseModel):
    check: bool = Field(
        False, description="Validate setup and cogs, then exit.", json_schema_extra={"action": "store_true"}
    )
    sync: bool = Field(False, description="Sync slash commands on ready.", json_schema_extra={"action": "store_true"})
    config_path: Path = Field(Path("config.yaml"), description="Path to configuration file.")


def _add_args_from_model(parser: ArgumentParser, model: type[BaseModel]) -> None:
    for name, field in model.model_fields.items():
        cli_name = name.replace("_", "-")
        arg_type = type(field.default)
        if arg_type not in (list, set, bool):
            arg_type = str
        help_text = field.description or ""
        default = field.default
        default_options = {"default": default, "dest": name, "help": help_text}

        name_or_flags = [f"--{cli_name}"]
        alias: str = field.alias or field.validation_alias or field.serialization_alias
        if alias and len(alias) == 1:
            name_or_flags.insert(0, f"-{alias}")
        if arg_type is bool:
            action = (
                field.json_schema_extra.get("action")
                if field.json_schema_extra and field.json_schema_extra.get("action")
                else BooleanOptionalAction
            )
            default_options.pop("default")
            parser.add_argument(*name_or_flags, action=action, **default_options)
            continue
        if arg_type in (list, set):
            parser.add_argument(*name_or_flags, nargs="*", action="extend", **default_options)
            continue
        parser.add_argument(*name_or_flags, type=arg_type, **default_options)


def get_runtime_args() -> RuntimeArgs:
    parser = argparse.ArgumentParser(description="Aethor Discord Bot", usage="poetry run python -m src.bot [OPTIONS]")
    _add_args_from_model(parser, RuntimeArgs)
    namespace = parser.parse_args()
    return RuntimeArgs.model_validate(vars(namespace))


if __name__ == "__main__":
    print(get_runtime_args())

from __future__ import annotations

import argparse

from pydantic import BaseModel


class RuntimeArgs(BaseModel):
    check: bool = False
    sync: bool = False


def get_runtime_args() -> RuntimeArgs:
    parser = argparse.ArgumentParser(description="Aethor Discord Bot")
    parser.add_argument("--check", action="store_true", help="Validate setup and cogs, then exit.")
    parser.add_argument("--sync", action="store_true", help="Sync slash commands on ready.")
    args = parser.parse_args()

    return RuntimeArgs.model_validate(vars(args))

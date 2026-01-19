import datetime
import glob
import json
import os

from src.utils.config import ConfigModel, get_config
from src.utils.store import read_whitelist

BASE_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
BACKUP_DIR = os.path.join(BASE_DIR, "backups")

CONFIG: ConfigModel = get_config()


def ensure_dir() -> None:
    os.makedirs(BACKUP_DIR, exist_ok=True)


def list_backups() -> list[str]:
    ensure_dir()
    pattern = os.path.join(BACKUP_DIR, "whitelist-*.json")
    return sorted(glob.glob(pattern))


def prune_old_backups() -> None:
    files = list_backups()
    if CONFIG.minecraft.whitelist_backup.max_keep <= 0:
        return
    if len(files) <= CONFIG.minecraft.whitelist_backup.max_keep:
        return
    to_delete = files[0 : len(files) - CONFIG.minecraft.whitelist_backup.max_keep]
    for f in to_delete:
        try:
            os.remove(f)
        except Exception:
            pass


def backup_whitelist() -> str | None:
    if not CONFIG.minecraft.whitelist_backup.enabled:
        return None
    ensure_dir()
    now = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    path = os.path.join(BACKUP_DIR, f"whitelist-{now}.json")
    try:
        data = read_whitelist()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        prune_old_backups()
        return path
    except Exception:
        return None

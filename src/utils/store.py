import json
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "data")
WHITELIST_PATH = os.path.normpath(os.path.join(DATA_DIR, "whitelist.json"))
PLAYERS_PATH = os.path.normpath(os.path.join(DATA_DIR, "players.json"))


def ensure_files() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(WHITELIST_PATH):
        with open(WHITELIST_PATH, "w", encoding="utf-8") as f:
            json.dump([], f, indent=4)
    if not os.path.exists(PLAYERS_PATH):
        with open(PLAYERS_PATH, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=4)


def read_whitelist() -> list[str]:
    ensure_files()
    with open(WHITELIST_PATH, encoding="utf-8") as f:
        data = json.load(f)
        if not isinstance(data, list):
            return []
        return [str(x) for x in data]


def write_whitelist(entries: list[str]) -> None:
    ensure_files()
    entries = sorted({e.strip() for e in entries if e.strip()})
    with open(WHITELIST_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=4)


def add_to_whitelist(name: str) -> bool:
    name = name.strip()
    if not name:
        return False
    wl = read_whitelist()
    if name in wl:
        return False
    wl.append(name)
    write_whitelist(wl)
    return True


def remove_from_whitelist(name: str) -> bool:
    name = name.strip()
    wl = read_whitelist()
    if name not in wl:
        return False
    wl = [x for x in wl if x != name]
    write_whitelist(wl)
    return True

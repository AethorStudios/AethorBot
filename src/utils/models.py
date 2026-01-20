from dataclasses import dataclass
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from yarl import URL


@dataclass
class MinecraftUser:
    uuid: UUID
    username: str

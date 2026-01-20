from dataclasses import dataclass
from uuid import UUID


@dataclass
class MinecraftUser:
    uuid: UUID
    username: str

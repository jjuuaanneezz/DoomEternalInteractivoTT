from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
import time


class ActionType(Enum):
    SPAWN = "SPAWN"
    COMMAND = "COMMAND"
    PANIC = "PANIC"


@dataclass
class GiftData:
    donor: str
    gift_name: str
    repeat_count: int
    diamond_count: int
    total_coins: int = 0

    def __post_init__(self):
        if self.total_coins == 0:
            self.total_coins = self.diamond_count * self.repeat_count


@dataclass
class SpawnTask:
    action_type: ActionType
    command: str
    donor: str
    description: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class DemonTier:
    min_coins: int
    max_coins: int
    category: str
    demons: List[str]

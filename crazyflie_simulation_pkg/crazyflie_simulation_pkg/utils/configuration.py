from dataclasses import dataclass, field
from typing import List

from omegaconf import MISSING


@dataclass
class Position:
    x: float
    y: float
    z: float


@dataclass
class CrazyflieConfig:
    active: bool = False
    name: str = MISSING
    incoming_twist_topic: str = MISSING


@dataclass
class SwarmConfig:
    state_publisher_rate: float = field(default=10.0)
    velocity_publisher_rate: float = field(default=1.0)
    max_ang_z_rate: float = field(default=0.4)
    height: float = field(default=0.5)
    crazyflies: List[CrazyflieConfig] = field(
        default_factory=list[CrazyflieConfig]
    )

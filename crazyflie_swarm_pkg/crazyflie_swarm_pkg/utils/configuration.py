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
    sim_uri: str = MISSING
    uri: str = MISSING
    takeoff_height: float = MISSING
    takeoff_duration: float = MISSING
    multiranger: bool = False
    initial_position: Position = MISSING


@dataclass
class SwarmConfig:
    dt: float = field(default=0.01)
    state_publisher_rate: float = field(default=10.0)
    led_publisher_rate: float = field(default=1.0)
    velocity_publisher_rate: float = field(default=1.0)
    simulation: bool = field(default=True)
    crazyflies: List[CrazyflieConfig] = field(default_factory=list[CrazyflieConfig])

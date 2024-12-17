from dataclasses import dataclass, field

from omegaconf import MISSING


@dataclass
class DimensionsConfig:
    d_eq: float = MISSING
    radius: float = MISSING
    max_vis_objs: float = MISSING  # Max distance of visibility [m]


@dataclass
class GainsConfig:
    k_r: float = MISSING
    k_o: float = MISSING
    k_m: float = MISSING
    k_al: float = MISSING
    k_l: float = MISSING
    k_a: float = MISSING


@dataclass
class BoundsConfig:
    v_min: float = MISSING
    v_max: float = MISSING
    omega_min: float = MISSING
    omega_max: float = MISSING
    a_max: float = MISSING
    force_max: float = MISSING
    angle_offset_max: float = MISSING


@dataclass
class AgentConfig:
    num_options: int = MISSING
    k: float = MISSING
    h: float = MISSING


@dataclass
class FlockingConfig:
    dimensions: DimensionsConfig = field(default_factory=DimensionsConfig)
    gains: GainsConfig = field(default_factory=GainsConfig)
    bounds: BoundsConfig = field(default_factory=BoundsConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)

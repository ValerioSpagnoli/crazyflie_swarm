from enum import Enum

import numpy as np


class Direction(Enum):
    none = -1
    front = 0
    left = 1
    back = 2
    right = 3
    up = 4


class ObstacleType(Enum):
    none = -1
    obstacle = 0
    drone = 1
    floor = 2


class Obstacle:
    def __init__(
        self,
        abs_pos: np.ndarray = np.zeros((3, 1)),
        rel_pos: np.ndarray = np.zeros((3, 1)),
        direction: Direction = Direction.none,
        type: ObstacleType = ObstacleType.none,
    ) -> None:
        self.abs_pos = abs_pos
        self.rel_pos = rel_pos
        self.direction = direction
        self.type = type

    def __str__(self):
        return (
            f"Direction: {self.direction}\n"
            + f"Type: {self.type}\n"
            + f"Absolute Position: {self.abs_pos.transpose()}\n"
            + f"Relative Position: {self.rel_pos.transpose()}\n"
        )

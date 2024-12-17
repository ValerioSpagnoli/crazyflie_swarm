from enum import Enum

class RangeDirection(Enum):
    """
    Enum for the direction of the range measurement.
    """
    FRONT = 0
    LEFT = 1
    BACK = 2
    RIGHT = 3
    UP = 4
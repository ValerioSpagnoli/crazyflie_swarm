from dataclasses import dataclass

import numpy as np


@dataclass
class CrazyState:
    # Position
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    # Euler orientation
    roll: float = 0.0  # In Degrees by default
    pitch: float = 0.0  # In Degrees by default
    yaw: float = 0.0  # In Degrees by default

    # Linear Velocity
    vx: float = 0.0
    vy: float = 0.0
    vz: float = 0.0

    # Angular Velocity
    roll_rate: float = 0.0
    pitch_rate: float = 0.0
    yaw_rate: float = 0.0

    # Multiranger data
    mr_front: float = 0.0
    mr_right: float = 0.0
    mr_back: float = 0.0
    mr_left: float = 0.0
    mr_up: float = 0.0

    # Initial Position
    init_x: float = 0.0
    init_y: float = 0.0
    init_z: float = 0.0

    def __str__(self):
        return (
            f"Position: ({self.x:.2f}, {self.y:.2f}, {self.z:.2f})\n"
            + f"Inital Position: ({self.init_x:.2f}, {self.init_y:.2f}, {self.init_z:.2f})\n"
            + f"Euler Orientation: ({self.roll:.2f}, {self.pitch:.2f}, {self.yaw:.2f})\n"
            + f"Multiranger Data: ({self.mr_front:.2f}, {self.mr_right:.2f}, {self.mr_back:.2f}, {self.mr_left:.2f}, {self.mr_up:.2f})"
        )

    def get_position(self) -> np.ndarray:
        return np.array([self.x, self.y, self.z])

    def get_initial_position(self) -> np.ndarray:
        return np.array([self.init_x, self.init_y, self.init_z])

    def get_rotation_matrix(self) -> np.ndarray:
        roll = np.deg2rad(self.roll)
        pitch = np.deg2rad(self.pitch)
        yaw = np.deg2rad(self.yaw)

        R_roll = np.array(
            [
                [1, 0, 0],
                [0, np.cos(roll), -np.sin(roll)],
                [0, np.sin(roll), np.cos(roll)],
            ]
        )

        R_pitch = np.array(
            [
                [np.cos(pitch), 0, np.sin(pitch)],
                [0, 1, 0],
                [-np.sin(pitch), 0, np.cos(pitch)],
            ]
        )

        # Matrice di rotazione per yaw
        R_yaw = np.array(
            [
                [np.cos(yaw), -np.sin(yaw), 0],
                [np.sin(yaw), np.cos(yaw), 0],
                [0, 0, 1],
            ]
        )

        # Matrice di rotazione composta
        R = R_yaw @ R_pitch @ R_roll

        return R

    def rel2glob(self, rel_pos: np.ndarray) -> np.ndarray:
        """
        Calculate the absolute position of an obstacle given the orientation and position of the robot.

        Parameters:
            rel_pos (np.ndarray): A 3x1 vector representing the distance of the object relative to the robot [dx, dy, dz].

        Returns:
            np.ndarray: A 3x1 vector representing the absolute position of the object.
        """
        rel_pos.reshape(3, 1)
        R = self.get_rotation_matrix()
        abs_pos = self.get_position() + R @ rel_pos
        return abs_pos.reshape(3, 1)

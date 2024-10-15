from dataclasses import dataclass

import numpy as np


@dataclass
class CrazyState:
    # Position
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    # Euler orientation
    roll: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0

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

    def __str__(self):
        return (
            f"Position: ({self.x:.2f}, {self.y:.2f}, {self.z:.2f})\n"
            + f"Euler Orientation: ({self.roll:.2f}, {self.pitch:.2f}, {self.yaw:.2f})\n"
            + f"Linear Velocity: ({self.vx:.2f}, {self.vy:.2f}, {self.vz:.2f})\n"
            + f"Angular Velocity: ({self.roll_rate:.2f}, {self.pitch_rate:.2f}, {self.yaw_rate:.2f})\n"
            + f"Multiranger Data: ({self.mr_front:.2f}, {self.mr_right:.2f}, {self.mr_back:.2f}, {self.mr_left:.2f}, {self.mr_up:.2f})"
        )

    def get_position(self) -> np.ndarray:
        return np.array([self.x, self.y, self.z])

    def get_rotation_matrix(self) -> np.ndarray:
        R_roll = np.array(
            [
                [1, 0, 0],
                [0, np.cos(self.roll), -np.sin(self.roll)],
                [0, np.sin(self.roll), np.cos(self.roll)],
            ]
        )

        R_pitch = np.array(
            [
                [np.cos(self.pitch), 0, np.sin(self.pitch)],
                [0, 1, 0],
                [-np.sin(self.pitch), 0, np.cos(self.pitch)],
            ]
        )

        # Matrice di rotazione per yaw
        R_yaw = np.array(
            [
                [np.cos(self.yaw), -np.sin(self.yaw), 0],
                [np.sin(self.yaw), np.cos(self.yaw), 0],
                [0, 0, 1],
            ]
        )

        # Matrice di rotazione composta
        R = R_yaw @ R_pitch @ R_roll

        return R

    def rel2glob(self, rel_pos) -> np.ndarray:
        """
        Calculate the absolute position of an obstacle given the orientation and position of the robot.

        Parameters:
            rel_pos (np.ndarray): A 3x1 vector representing the distance of the object relative to the robot [dx, dy, dz].

        Returns:
            np.ndarray: A 3x1 vector representing the absolute position of the object.
        """
        R = self.get_rotation_matrix()
        abs_pos = self.get_position() + R @ rel_pos
        return abs_pos

from dataclasses import dataclass

import numpy as np
import crazyflie_simulation_pkg.utils.stringer as stringer

colors = ['b', 'g', 'r', 'c', 'm', 'y', 'olive', 'orange', 'deeppink','turquoise']

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

    # Initial Position
    init_x: float = 0.0
    init_y: float = 0.0
    init_z: float = 0.0

    def __str__(self):
        return (
            f"Position: ({self.x:.2f}, {self.y:.2f}, {self.z:.2f})\n"
            + f"Inital Position: ({self.init_x:.2f}, {self.init_y:.2f}, {self.init_z:.2f})\n"
            + f"Euler Orientation: ({self.roll:.2f}, {self.pitch:.2f}, {self.yaw:.2f})\n"
            + f"Linear Velocity: ({self.vx:.2f}, {self.vy:.2f}, {self.vz:.2f})\n"
            + f"Angular Velocity: ({self.roll_rate:.2f}, {self.pitch_rate:.2f}, {self.yaw_rate:.2f})\n"
            + f"Multiranger Data: ({self.mr_front:.2f}, {self.mr_right:.2f}, {self.mr_back:.2f}, {self.mr_left:.2f}, {self.mr_up:.2f})"
        )
    
    def fromMsg(self, msg):
        self.x = msg.position[0]
        self.y = msg.position[1]
        self.z = msg.position[2]
        self.roll = msg.euler_orientation[0]
        self.pitch = msg.euler_orientation[1]
        self.yaw = msg.euler_orientation[2]
        self.vx = msg.linear_velocity[0]
        self.vy = msg.linear_velocity[1]
        self.vz = msg.linear_velocity[2]
        self.roll_rate = msg.angular_velocity[0]
        self.pitch_rate = msg.angular_velocity[1]
        self.yaw_rate = msg.angular_velocity[2]
        self.mr_front = msg.multiranger[0]
        self.mr_right = msg.multiranger[1]
        self.mr_back = msg.multiranger[2]
        self.mr_left = msg.multiranger[3]
        self.mr_up = msg.multiranger[4]

        return self
    def toDrone(self, name, config):
        dr = {
                config.name : name,
                config.color : colors[int(name[-1])],
                config.scope_pose: [0] *6,
                config.scope_dists: [0] *4,
                config.forces: '',
                config.scope_velocity: [0] *2,
                config.obj_detected: '',
                config.des_v: ''
            }
        
        dr[config.scope_pose] = [self.x, self.y, self.z, self.roll, self.pitch, self.yaw]
        dr[config.scope_dists] = [self.mr_front, self.mr_right, self.mr_back, self.mr_left]
        dr[config.forces] = '0,0,0,0,0,0,0,0,0' 
        dr[config.scope_velocity] = [self.vx, self.vy]
        #dr[config.obj_detected] = self.get_objects()
        dr[config.des_v] = stringer.string_velocity_noname(self.vx, self.vy)
        
        return dr


    def get_position(self) -> np.ndarray:
        return np.array([self.x, self.y, self.z])

    def get_initial_position(self) -> np.ndarray:
        return np.array([self.init_x, self.init_y, self.init_z])

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

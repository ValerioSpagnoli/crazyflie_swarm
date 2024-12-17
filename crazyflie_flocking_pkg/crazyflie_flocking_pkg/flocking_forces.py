from typing import Dict, List

import numpy as np

from crazyflie_flocking_pkg.utils import get_clipper, get_versor
from crazyflie_flocking_pkg.utils.configuration import FlockingConfig
from crazyflie_flocking_pkg.utils.definitions import Direction, Obstacle
from crazyflie_swarm_pkg.crazyflie import CrazyState
from rclpy.impl.rcutils_logger import RcutilsLogger



class ForcesGenerator:
    def __init__(self, config: FlockingConfig, ros2_logger: RcutilsLogger):
        self.config = config
        self.ros2_logger = ros2_logger

    def get_forces(
        self,
        state: CrazyState,
        neighbors: Dict[str, CrazyState],
        obstacles: List[Obstacle],
        v_mig: np.ndarray,
    ):
        
        self.ros2_logger.info(f"{neighbors}") 
               
        # Initialization
        f_inter_robot = np.zeros((3, 1))
        f_obstacle = np.zeros((3, 1))
        f_migration = np.zeros((3, 1))

        self_pos = state.get_position()

        # Inter-robot forces, formula (2)
        # The force to each neighbor is summed together into a total force
        for name, neighbor in neighbors.items():
            n_pos = neighbor.get_position()

            neighbor_distance = (
                np.linalg.norm(n_pos - self_pos)
                - 2 * self.config.dimensions.radius
            )

            #  It's not sure that this is right, it's done to avoid the case of the over-pulling of the drones if they're a lot
            #  namely, if you have a lot of robot, thay can't be at d_eq to each other, but just a subset of them
            #  this means that all the other will pull the drone towards other drones, making the configuration "squeeze"
            
            # TODO: serve con piú di 3 robot
            # if neighbor_distance > 2 * self.config.dimensions.d_eq:
            #     continue

            # Direction of vector between me and nth neighbor
            u_ij = get_versor(n_pos - self_pos).reshape((3, 1))
            self.ros2_logger.info(f"\n ************** {u_ij.transpose()} *****************\n")

            f_inter_robot += (
                self.config.gains.k_r
                * (neighbor_distance - self.config.dimensions.d_eq)
                * u_ij
            )
        f_inter_robot[2] = 0

        # Obstacle avoidance forces, formula (3)
        for o in obstacles:
            obstacle_distance = np.linalg.norm(o.rel_pos) - self.config.dimensions.radius

            # Versor to obstacle computation 
            self_yaw = np.deg2rad(state.yaw)
            R = np.array(
                [
                    [np.cos(self_yaw), -np.sin(self_yaw), 0],
                    [np.sin(self_yaw), np.cos(self_yaw), 0],
                    [0, 0, 1],
                ]
            )

            if o.direction == Direction.front:
                u_ik = R @ np.array([1, 0, 0])
            elif o.direction == Direction.back:
                u_ik = R @ np.array([-1, 0, 0])
            elif o.direction == Direction.left:
                u_ik = R @ np.array([0, 1, 0])
            elif o.direction == Direction.right:
                u_ik = R @ np.array([0, -1, 0])
                
            u_ik = np.reshape(u_ik, (3, 1))
            
            # BE SURE THAT THE GAIN K_O IS NOT USED TWICE
            # We could test other kind of obstacle force just to see which one is the best
            contr = (
                - (1 / (obstacle_distance) ** 2) * u_ik
            )  # f_obs originale
            
            # d_0 = self.config.dimensions.max_vis_objs - self.config.dimensions.radius
            # contr = - (1/(obstacle_distance)**2 - 1/(d_0)**2)* u_ik  # f_obs continua
            # contr = - (1/(obstacle_distance) - 1/(d_0))**2 * u_ik    # f_obs APF

            f_obstacle += self.config.gains.k_o * contr

        f_obstacle[2] = 0

        # Migration force, formula (4)
        v_mig = np.reshape(v_mig, (3, 1))
        f_migration = self.config.gains.k_m * v_mig

        # Clip forces
        forces = np.hstack((f_inter_robot, f_obstacle, f_migration))
        overall_force = np.sum(forces, axis=1)
        clipper = get_clipper(overall_force, self.config.bounds.force_max)
        forces = forces / clipper

        return forces

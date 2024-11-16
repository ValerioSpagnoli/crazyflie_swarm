from typing import Dict, List

import numpy as np
from rclpy.impl.rcutils_logger import RcutilsLogger

from crazyflie_flocking_pkg.flocking_forces import ForcesGenerator
from crazyflie_flocking_pkg.utils.configuration import FlockingConfig
from crazyflie_flocking_pkg.utils.definitions import (
    Direction,
    Obstacle,
    ObstacleType,
)
from crazyflie_swarm_pkg.crazyflie import CrazyState


class Agent:
    def __init__(
        self,
        name: str,
        config: FlockingConfig,
        ros2_logger: RcutilsLogger = None,
    ):
        self.forces_gen = ForcesGenerator(config, ros2_logger)
        self.ros2_logger = ros2_logger
        self.config = config
        self.name = name
        self.counter = 0
        self.n_cycles_decision = 10
        self.v_mig = np.array([0, 0, 0])

    def compute_velocities(self, swarm_state: Dict[str, CrazyState], target):
        """
        Computes the velocities of the drone based on the forces generated by the flocking algorithm.
        """
        # Get the state of the drone
        state = swarm_state[self.name]

        # Get the state of the neighbors
        neighbors = swarm_state.copy()
        neighbors.pop(self.name)  # remove myself from neighbors

        # TODO: per ora si mettono solo in formazione
        v_mig = np.array([4.0, 0, 0])
        
        # Obstacles
        detected_obstacles = self.detect_obstacles(state)
        obstacles = self.classify_obstacles(neighbors, detected_obstacles)
        
        # Compute the forces
        forces = self.forces_gen.get_forces(
            state, neighbors, obstacles, v_mig
        )

        overall_force = np.clip(
            np.sum(forces, axis=1),
            -self.config.bounds.force_max,
            self.config.bounds.force_max,
        )
        
        # Compute the yaw mean
        target_yaw = (
            np.arctan2(target[1] - state.y, target[0] - state.x) - state.yaw
        )
        yaw_mean = state.yaw
        for _, neighbor in neighbors.items():
            yaw_mean += neighbor.yaw
        yaw_mean += target_yaw
        yaw_mean /= len(neighbors) + 2

        # Compute velocities
        v = self.config.gains.k_l * overall_force
        v = np.clip(v, -self.config.bounds.v_max, self.config.bounds.v_max)
        omega = self.config.gains.k_a * (yaw_mean - state.yaw)
        omega = np.clip(
            omega, -self.config.bounds.omega_max, self.config.bounds.omega_max
        )
        
        self.ros2_logger.info("")
        self.ros2_logger.info("----------------------")
        self.ros2_logger.info(f"Agent {self.name}")
        self.ros2_logger.info(f"State\n{state}")
        self.ros2_logger.info(f"Number of obstacles: {len(obstacles)}")
        self.ros2_logger.info(f"{np.round(forces[:, 0],2)}")
        self.ros2_logger.info(f"{np.round(forces[:, 1],2)}")
        self.ros2_logger.info(f"{np.round(forces[:, 2],2)}")
        self.ros2_logger.info(f"{np.round(v,2)}")
        self.ros2_logger.info("----------------------")
        self.ros2_logger.info("")

        return v, 0.0, forces, obstacles

    def detect_obstacles(
        self,
        state: CrazyState,
    ) -> List[Obstacle]:
        """
        Detects obstacles around the agent based on its state and the states of its neighbors.
        Args:
            state (CrazyState): The current state of the agent, which includes sensor readings.
            neighbors (Dict[str, CrazyState]): A dictionary of neighboring agents' states, keyed by their identifiers.
        Returns:
            List[Obstacle]: A list of detected obstacles, each with its absolute position, relative position, direction, and type.
        The function performs the following steps:
        1. Initializes an empty list to store detected obstacles.
        2. Checks the agent's sensor readings in the front, left, back, right, and up directions.
        If an obstacle is detected within a threshold distance (2 units), it calculates the obstacle's relative position,
        converts it to an absolute position, and appends it to the list of detected obstacles.
        """
        detected_obstacles: List[Obstacle] = []
        obstacle_threshold = 2

        if state.mr_front < obstacle_threshold:
            obstacle_rel_pos = state.mr_front * np.array([1, 0, 0])
            obstacle_abs_pos = state.rel2glob(obstacle_rel_pos)
            detected_obstacles.append(
                Obstacle(
                    abs_pos=obstacle_abs_pos,
                    direction=Direction.front,
                    rel_pos=obstacle_rel_pos,
                )
            )

        if state.mr_left < obstacle_threshold:
            obstacle_rel_pos = state.mr_left * np.array([0, 1, 0])
            obstacle_abs_pos = state.rel2glob(obstacle_rel_pos)
            detected_obstacles.append(
                Obstacle(
                    abs_pos=obstacle_abs_pos,
                    direction=Direction.left,
                    rel_pos=obstacle_rel_pos,
                )
            )

        if state.mr_back < obstacle_threshold:
            obstacle_rel_pos = state.mr_back * np.array([-1, 0, 0])
            obstacle_abs_pos = state.rel2glob(obstacle_rel_pos)
            detected_obstacles.append(
                Obstacle(
                    abs_pos=obstacle_abs_pos,
                    direction=Direction.back,
                    rel_pos=obstacle_rel_pos,
                )
            )

        if state.mr_right < obstacle_threshold:
            obstacle_rel_pos = state.mr_right * np.array([0, -1, 0])
            obstacle_abs_pos = state.rel2glob(obstacle_rel_pos)
            detected_obstacles.append(
                Obstacle(
                    abs_pos=obstacle_abs_pos,
                    direction=Direction.right,
                    rel_pos=obstacle_rel_pos,
                )
            )

        if state.mr_up < obstacle_threshold:
            obstacle_rel_pos = state.mr_up * np.array([0, 0, 1])
            obstacle_abs_pos = state.rel2glob(obstacle_rel_pos)
            detected_obstacles.append(
                Obstacle(
                    abs_pos=obstacle_abs_pos,
                    direction=Direction.up,
                    rel_pos=obstacle_rel_pos,
                )
            )

        return detected_obstacles

    def classify_obstacles(
        self,
        neighbors: Dict[str, CrazyState],
        detected_obstacles: List[Obstacle],
    ) -> List[Obstacle]:
        """

        Args:
            state (CrazyState): The current state of the agent, which includes sensor readings.
            neighbors (Dict[str, CrazyState]): A dictionary of neighboring agents' states, keyed by their identifiers.
        Returns:
            List[Obstacle]: A list of classified obstacles, each with its absolute position, relative position, direction, and type.

        1. Iterates over the detected obstacles to determine their type:
        - If the obstacle is below a certain height (0.1 units), it is classified as a floor.
        - If the obstacle is within a close distance (0.1 units) to any neighbor, it is classified as a drone.
        - Otherwise, it is classified as a generic obstacle.
        2. Returns the list of detected obstacles by setting the type
        """

        drone_treshold = 0.4

        for o in detected_obstacles:
            isObstacle = True

            if o.abs_pos[2] < 0.05:
                isObstacle = False
                o.type = ObstacleType.floor
                continue

            for key, neighbor in neighbors.items():

                dist = np.linalg.norm(
                    o.abs_pos
                    + neighbor.get_initial_position()
                    - neighbor.get_position()
                )
                
                if (
                    dist < drone_treshold
                ):  # TODO: make this a parameter, like "DRONE_CLASS_THRESHOLD"
                    isObstacle = False
                    o.type = ObstacleType.drone
                    break

            # Obstacles that aren't floors or drones are classified as generic obstacles
            if isObstacle:
                o.type = ObstacleType.obstacle

        return detected_obstacles

import random
from typing import Dict, List

import numpy as np
from crazyflie_flocking_pkg.crazyflie_flocking_pkg.utils.geometry import point_line_distance
from rclpy.impl.rcutils_logger import RcutilsLogger

from crazyflie_flocking_pkg.flocking_forces import ForcesGenerator
from crazyflie_flocking_pkg.utils.configuration import FlockingConfig
from crazyflie_flocking_pkg.utils.definitions import Direction, Obstacle, ObstacleType, Option
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
        self.decision_counter = 0
        self.decision_cycle = 10 # TODO: make this a parameter
        self.v_mig = np.array([0, 0, 0])
        self.option = Option.uncommitted

    def compute_velocities(
        self,
        state: CrazyState,
        neighbors: Dict[str, CrazyState],
        neighbor_agents: Dict[str, "Agent"],
    ) -> np.ndarray:
        """
        Computes the velocities of the drone based on the forces generated by the flocking algorithm.
        """
        # Obstacles
        detected_obstacles = self.detect_obstacles(state)
        obstacles = self.classify_obstacles(neighbors, detected_obstacles)
        
        # TODO: CONFIG
        v_mig = np.array([0.0, 0.0, 0.0])
        target = np.array([1.0, 0.0, state.z])
        
        if self.config.agent.is_influenced:
            self.decision_counter += 1
            if self.decision_counter == self.decision_cycle:
                self.option = self.search_for_commit(state, neighbor_agents, obstacles, target)
                mig_angle = self.option.value * 2 * np.pi / self.config.agent.num_options
                v_mig = np.array([0.0 ,0.0 ,0.0]) if self.option == Option.uncommitted else np.array([np.cos(mig_angle), np.sin(mig_angle), 0])
            
        # Compute the forces
        forces = self.forces_gen.get_forces(state, neighbors, obstacles, v_mig)

        overall_force = np.clip(
            np.sum(forces, axis=1),
            -self.config.bounds.force_max,
            self.config.bounds.force_max,
        )

        # Compute linear velocity
        v = self.config.gains.k_l * overall_force
        v = np.clip(v, -self.config.bounds.v_max, self.config.bounds.v_max)

        # Compute angular velocity
        omega = 0.0
        if not self.config.agent.is_omnidirectional:
            # Align overall_force to u_i
            cosyaw = np.cos(np.deg2rad(state.yaw))
            sinyaw = np.sin(np.deg2rad(state.yaw))
            u_i = np.reshape(np.array([cosyaw, sinyaw, 0]), (3, 1))

            # Linear speed, formulas (5), (7) TODO: aggiusta
            v_scalar = self.config.gains.k_l * (np.dot(np.reshape(overall_force, (1, 3)), u_i))
            v_scalar = np.clip(v_scalar, self.config.bounds.v_min, self.config.bounds.v_max)
            v = v_scalar[0] * u_i
            v = np.reshape(v, (3,))

            # Angular speed, formula (8)
            # u_i_orthogonal computed as vector orthogonal to u_i and vector_orthogonal_to_plane (z axis)
            zdir = np.array([[0], [0], [1]])
            u_i_orthogonal = np.cross(zdir[:, 0], u_i[:, 0])
            omega_scalar = self.config.gains.k_a * (np.dot(overall_force, u_i_orthogonal))
            self.ros2_logger.info(f"omega_scalar: {np.round(omega_scalar,2)}")
            omega_scalar = np.clip(
                omega_scalar,
                self.config.bounds.omega_min,
                self.config.bounds.omega_max,
            )
            omega = -omega_scalar

        self.ros2_logger.info("")
        self.ros2_logger.info("-------------------------")
        self.ros2_logger.info(f"Agent {self.name}")
        self.ros2_logger.info(f"State\n{state}")
        self.ros2_logger.info(f"Number of obstacles: {len(obstacles)}")
        self.ros2_logger.info(f"Inter Robot Force: {np.round(forces[:, 0],2)}")
        self.ros2_logger.info(f"Obstacle Force: {np.round(forces[:, 1],2)}")
        self.ros2_logger.info(f"Migration Force: {np.round(forces[:, 2],2)}")
        self.ros2_logger.info(f"Overall Force: {np.round(overall_force,2)}")
        if not self.config.agent.is_omnidirectional:
            self.ros2_logger.info(f"u_i: {np.round(u_i.transpose(),2)}")
            self.ros2_logger.info(f"u_i_orthogonal: {np.round(u_i_orthogonal,2)}")
            self.ros2_logger.info(f"v_scalar: {np.round(v_scalar,2)}")
        self.ros2_logger.info(f"v: {np.round(v,2)}")
        self.ros2_logger.info(f"omega: {np.round(omega,2)}")
        self.ros2_logger.info("-------------------------")
        self.ros2_logger.info("")

        return v, omega

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
                    o.abs_pos + neighbor.get_initial_position() - neighbor.get_position()
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
    
    
    def search_for_commit(self, state: CrazyState, neighbor_agents: Dict[str, "Agent"], obstacles: List[Obstacle], target: np.ndarray) -> Option:
        """
        Search for commit based on neighbors
        """
        p = random.uniform(0, 1)
        
        if self.option == Option.uncommitted:
            option = random.randint(1, self.config.agent.num_options)
            v_gamma = self.get_option_value(option, state, obstacles, target)
            P_gamma = v_gamma * self.config.agent.k
            
            if p < P_gamma:
                # I have a new commitment, decided by myself
                return option
            
            for n in neighbor_agents.values():
                if not n.option == Option.uncommitted:
                    v_rho = self.get_option_value(n.option, state, obstacles, target)
                    P_rho = v_rho * self.config.agent.h
                    
                    if p < P_gamma + P_rho:
                        # I have a new commitment, decided by a neighbor
                        return n.option
                    
        else:
            v_alpha = self.get_option_value(self.option, state, obstacles, target)
            P_alpha = self.config.agent.k / v_alpha
            
            if p < P_alpha:
                # I abandon my commitment
                return Option.uncommitted
            
            for n in neighbor_agents.values():
                if not n.option == Option.uncommitted and not n.option == self.option:
                    v_sigma = self.get_option_value(n.option, state, obstacles, target)
                    P_sigma = self.config.agent.h * v_sigma
                    
                    if p < P_alpha + P_sigma:
                        # I've been convinced by someone else to abandon my commitment
                        return Option.uncommitted
                    
        return self.option
            
            
    def get_option_value(self, option: Option, state: CrazyState, obstacles: List[Obstacle], target: np.ndarray) -> float:
        """
        Get the value of the option
        """
        angle = option.value * 2 * np.pi / self.config.agent.num_options
        direction_vector = np.array([np.cos(angle), np.sin(angle), 0])
        min_distance = 100
        
        for o in obstacles:
            if not o.type == ObstacleType.obstacle:
                continue
            
            o_pos = o.abs_pos
            drone_pos = state.get_position
            drone_o_vec = o_pos - drone_pos
            
            if drone_o_vec @ direction_vector >= 0: # Obstacle is not behind
                distance = point_line_distance(o_pos, drone_pos, direction_vector) 
                if distance < min_distance:
                    min_distance = distance
        
        drone_target = target - state.get_position()
        target_distance = 50
        
        if drone_target @ direction_vector >= 0: # Target is not behind
            distance = point_line_distance(target, state.get_position(), direction_vector)
            if distance < target_distance:
                target_distance = distance
                
        value = min_distance / 100 * (1 - target_distance / 50)
        
        return value if value > 0 else 1e-5
              
            
            
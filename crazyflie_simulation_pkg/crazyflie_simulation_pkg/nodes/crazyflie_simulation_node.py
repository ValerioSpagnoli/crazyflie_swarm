from typing import Any, Dict

import rclpy
from geometry_msgs.msg import PoseStamped, Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node, Publisher, Subscription
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Float32
from std_srvs.srv import Empty

from crazyflie_simulation_pkg.utils import SwarmConfig, load_config
from crazyflie_swarm_interfaces.msg import CrazyflieState
from crazyflie_swarm_pkg.crazyflie.crazyflie_state import CrazyState


class CrazyflieSimulation(Node):
    def __init__(self):
        super().__init__("crazyflie_simulation_node")
        self.get_logger().set_level(rclpy.logging.LoggingSeverity.DEBUG)

        # * Load Config
        self.declare_parameter("swarm_config_path", "")
        swarm_config_path = (
            self.get_parameter("swarm_config_path")
            .get_parameter_value()
            .string_value
        )
        config = load_config(swarm_config_path, SwarmConfig)
        self.config = config

        self.get_logger().info("CrazyflieSimulationNode started")
        for cf_config in self.config.crazyflies:
            self.get_logger().info(f"  - {cf_config.name}")

        self.max_ang_z_rate = self.config.max_ang_z_rate
        self.takeoff_height = self.config.height

        # * CrazyflieSwarm
        self.swarm = []
        for crazyflie_config in self.config.crazyflies:
            if crazyflie_config.active is False:
                continue
            name = crazyflie_config.name
            self.swarm.append(name)

        self.get_logger().info(f"Swarm: {self.swarm}")

        # * Publishers
        velocity_publisher_rate = self.config.velocity_publisher_rate
        for name in self.swarm:
            publisher = self.create_publisher(Twist, f"/gz/{name}/cmd_vel", 10)
            self.create_timer(
                1 / velocity_publisher_rate,
                lambda name=name, publisher=publisher: self.publisher_velocity_callback(
                    name, publisher
                ),
            )

        state_publisher_rate = self.config.state_publisher_rate
        for name in self.swarm:
            publisher = self.create_publisher(
                CrazyflieState, f"/{name}/state", 10
            )
            self.create_timer(
                1 / state_publisher_rate,
                lambda name=name, publisher=publisher: self.state_callback(
                    name, publisher
                ),
            )

        # * Subscriptions
        self.velocity_subscribers: Dict[str, Subscription] = {}
        for crazyflie_config in self.config.crazyflies:
            if crazyflie_config.active is False:
                continue
            name = crazyflie_config.name
            incoming_twist_topic = crazyflie_config.incoming_twist_topic
            subscriber = self.create_subscription(
                Twist,
                incoming_twist_topic,
                lambda msg, name=name: self.subscriber_velocity_callback(
                    msg, name
                ),
                10,
            )
            self.velocity_subscribers[name] = subscriber

        self.odom_subscribers: Dict[str, Subscription] = {}
        for name in self.swarm:
            self.odom_subscribers[name] = self.create_subscription(
                Odometry,
                f"/{name}/odom",
                lambda msg, name=name: self.odom_callback(msg, name),
                10,
            )

        self.multiranger_subscribers: Dict[str, Subscription] = {}
        for name in self.swarm:
            self.multiranger_subscribers[name] = self.create_subscription(
                LaserScan,
                f"/{name}/multiranger",
                lambda msg, name=name: self.multiranger_callback(msg, name),
                10,
            )

        self.current_twist_commands: Dict[str, Twist] = {}
        self.current_odoms: Dict[str, Odometry] = {}
        self.current_multirangers: Dict[str, LaserScan] = {}
        self.current_states: Dict[str, CrazyState] = {}
        self.takeoff_commands: Dict[str, bool] = {}
        self.is_flying: Dict[str, bool] = {}
        self.keep_height: Dict[str, bool] = {}
        for name in self.swarm:
            self.current_twist_commands[name] = Twist()
            self.current_odoms[name] = Odometry()
            self.current_multirangers[name] = LaserScan()
            self.current_states[name] = CrazyState()
            self.takeoff_commands[name] = False
            self.is_flying[name] = False
            self.keep_height[name] = False

    def odom_callback(self, msg: Odometry, name: str) -> None:
        self.current_odoms[name] = msg
        state = CrazyState()

        state.x = self.current_odoms[name].pose.pose.position.x
        state.y = self.current_odoms[name].pose.pose.position.y
        state.z = self.current_odoms[name].pose.pose.position.z
        state.roll = self.current_odoms[name].pose.pose.orientation.x
        state.pitch = self.current_odoms[name].pose.pose.orientation.y
        state.yaw = self.current_odoms[name].pose.pose.orientation.z
        state.vx = self.current_odoms[name].twist.twist.linear.x
        state.vy = self.current_odoms[name].twist.twist.linear.y
        state.vz = self.current_odoms[name].twist.twist.linear.z
        state.roll_rate = self.current_odoms[name].twist.twist.angular.x
        state.pitch_rate = self.current_odoms[name].twist.twist.angular.y
        state.yaw_rate = self.current_odoms[name].twist.twist.angular.z
        state.mr_front = self.current_multirangers[name].ranges[2]
        state.mr_right = self.current_multirangers[name].ranges[1]
        state.mr_back = self.current_multirangers[name].ranges[0]
        state.mr_left = self.current_multirangers[name].ranges[3]
        state.mr_up = 1000.0

        self.current_states[name] = state

    def multiranger_callback(self, msg: LaserScan, name: str) -> None:
        self.current_multirangers[name] = msg

    def state_callback(self, name: str, publisher: Publisher) -> None:
        state_msg = CrazyflieState()
        state = self.current_states[name]
        state_msg.position[0] = state.x
        state_msg.position[1] = state.y
        state_msg.position[2] = state.z
        state_msg.euler_orientation[0] = state.roll
        state_msg.euler_orientation[1] = state.pitch
        state_msg.euler_orientation[2] = state.yaw
        state_msg.linear_velocity[0] = state.vx
        state_msg.linear_velocity[1] = state.vy
        state_msg.linear_velocity[2] = state.vz
        state_msg.angular_velocity[0] = state.roll_rate
        state_msg.angular_velocity[1] = state.pitch_rate
        state_msg.angular_velocity[2] = state.yaw_rate
        state_msg.multiranger[0] = state.mr_front
        state_msg.multiranger[1] = state.mr_right
        state_msg.multiranger[2] = state.mr_back
        state_msg.multiranger[3] = state.mr_left
        state_msg.multiranger[4] = state.mr_up

        publisher.publish(state_msg)

    def subscriber_velocity_callback(self, msg: Twist, name: str) -> None:
        self.current_twist_commands[name] = msg

    def publisher_velocity_callback(
        self, name: str, publisher: Publisher
    ) -> None:
        height_command = self.current_twist_commands[name].linear.z
        new_twist_msg = Twist()
        if self.is_flying[name]:
            new_twist_msg.linear.x = self.current_twist_commands[name].linear.x
            new_twist_msg.linear.y = self.current_twist_commands[name].linear.y
            new_twist_msg.linear.z = self.current_twist_commands[name].linear.z
            new_twist_msg.angular.x = self.current_twist_commands[
                name
            ].angular.x
            new_twist_msg.angular.y = self.current_twist_commands[
                name
            ].angular.y
            new_twist_msg.angular.z = self.current_twist_commands[
                name
            ].angular.z

        if height_command > 0 and not self.is_flying[name]:
            new_twist_msg.linear.z = 0.5
            if self.current_states[name].z > self.takeoff_height:
                new_twist_msg.linear.z = 0.0
                self.current_twist_commands[name].linear.z = 0.0
                self.is_flying[name] = True
                self.get_logger().info("Takeoff completed")

        if height_command < 0 and self.is_flying[name]:
            if self.current_states[name].z < 0.1:
                new_twist_msg.linear.z = 0.0
                self.is_flying[name] = False
                self.keep_height[name] = False
                self.get_logger().info("Landing completed")

        if (
            abs(self.current_twist_commands[name].angular.z)
            > self.max_ang_z_rate
        ):
            new_twist_msg.angular.z = (
                self.max_ang_z_rate
                * abs(self.current_twist_commands[name].angular.z)
                / self.current_twist_commands[name].angular.z
            )

        tolerance = 1e-7
        if abs(height_command) < tolerance and self.is_flying[name]:
            if not self.keep_height[name]:
                self.desired_height = self.current_states[name].z
                self.keep_height[name] = True
            else:
                error = self.desired_height - self.current_states[name].z
                new_twist_msg.linear.z = error

        if abs(height_command) > tolerance and self.is_flying[name]:
            if self.keep_height[name]:
                self.keep_height[name] = False

        publisher.publish(new_twist_msg)


def main(args: Any = None) -> None:
    rclpy.init(args=args)
    crazyflie_node = CrazyflieSimulation()
    rclpy.spin(crazyflie_node)
    crazyflie_node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()

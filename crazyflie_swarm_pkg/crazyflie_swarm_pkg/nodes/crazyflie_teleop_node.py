from typing import Any, Dict

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node, Publisher

from crazyflie_swarm_interfaces.msg import CrazyflieState
from crazyflie_swarm_pkg.utils import SwarmConfig, load_config


class CrazyflieTeleopNode(Node):
    def __init__(self):
        super().__init__("crazyflie_teleop_node")
        self.get_logger().set_level(rclpy.logging.LoggingSeverity.DEBUG)

        # * Load Config
        self.declare_parameter("swarm_config_path", "")
        swarm_config_path = (
            self.get_parameter("swarm_config_path").get_parameter_value().string_value
        )
        config = load_config(swarm_config_path, SwarmConfig)
        self.config = config

        self.get_logger().info("CrazyflieTeleopNode started")
        for cf_config in self.config.crazyflies:
            self.get_logger().info(
                f" - {cf_config.name}:\n  - uri: {cf_config.uri}\n  - active: {cf_config.active}"
            )

        # * CrazyflieSwarm
        self.swarm: Dict[str] = {}
        for crazyflie_config in self.config.crazyflies:
            if crazyflie_config.active is False:
                continue
            uri = crazyflie_config.uri
            name = crazyflie_config.name
            self.swarm[name] = uri

        # * Publishers
        self.velocity_publishers: Dict[str, Publisher] = {}
        velocity_publisher_rate = self.config.velocity_publisher_rate
        for name, _ in self.swarm.items():
            publisher = self.create_publisher(Twist, f"/{name}/cmd_vel", 10)
            self.velocity_publishers[name] = publisher
            self.create_timer(
                1 / velocity_publisher_rate,
                lambda name=name, publisher=publisher: self.velocity_callback(name, publisher),
            )

        # * Hardcoded publisher for one "simulated" cf
        # self.cf_publisher : Publisher = self.create_publisher(CrazyflieState, f"/cf3/state", 10)
        # self.create_timer(0.1, self.cf_callback)

        # * Subscriptions
        self.cmd_vel_subscriber = self.create_subscription(
            Twist, "/cmd_vel", self.cmd_vel_callback, 10
        )
        self.current_cmd_vel = Twist()

    def cmd_vel_callback(self, msg: Twist) -> None:
        self.current_cmd_vel = msg

    def velocity_callback(self, name: str, publisher: Publisher) -> None:
        velocity_msg = Twist()
        velocity_msg.linear.x = self.current_cmd_vel.linear.x
        velocity_msg.linear.y = self.current_cmd_vel.linear.y
        velocity_msg.linear.z = 0.0
        velocity_msg.angular.x = 0.0
        velocity_msg.angular.y = 0.0
        velocity_msg.angular.z = self.current_cmd_vel.angular.z
        publisher.publish(velocity_msg)

    def cf_callback(self) -> None:
        msg: CrazyflieState = CrazyflieState()
        msg.position[0] = 0.2
        msg.position[1] = 0.25
        msg.position[2] = 0.13
        self.cf_publisher.publish(msg)


def main(args: Any = None) -> None:
    rclpy.init(args=args)
    crazyflie_node = CrazyflieTeleopNode()
    rclpy.spin(crazyflie_node)
    crazyflie_node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()

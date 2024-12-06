import time
from typing import Dict

import cflib.crtp as crtp
import numpy as np
import rclpy
import tf_transformations as tft
from geometry_msgs.msg import PoseStamped, TransformStamped, Twist
from rclpy.node import Node, Publisher, Subscription
from std_msgs.msg import Float32
from tf2_ros import TransformBroadcaster

from crazyflie_swarm_interfaces.msg import CrazyflieState
from crazyflie_swarm_interfaces.srv import Land, TakeOff
from crazyflie_swarm_pkg.crazyflie import CrazyflieRobot
from crazyflie_swarm_pkg.utils import SwarmConfig, load_config


class CrazyflieSwarmNode(Node):
    def __init__(self):
        super().__init__("crazyflie_swarm_node")
        self.get_logger().set_level(rclpy.logging.LoggingSeverity.DEBUG)

        self.config = self._get_config()

        # * CrazyflieSwarm
        crtp.init_drivers()
        self.fully_connected_crazyflie_cnt = 0
        self.swarm: Dict[str, CrazyflieRobot] = {}
        is_simulated = self.config.simulation

        for crazyflie_config in self.config.crazyflies:
            if crazyflie_config.active is False:
                continue
            if is_simulated:
                uri = crazyflie_config.sim_uri
            else:
                uri = crazyflie_config.uri

            name = crazyflie_config.name
            multiranger = crazyflie_config.multiranger
            initial_position = crazyflie_config.initial_position
            height = crazyflie_config.takeoff_height
            duration = crazyflie_config.takeoff_duration
            crazyflie_robot = CrazyflieRobot(
                uri=uri,
                name=name,
                ro_cache="./ro_cache",
                rw_cache="./rw_cache",
                logger=self.get_logger(),
                multiranger=multiranger,
                initial_position=initial_position,
                default_take_off_height=height,
                default_take_off_duration=duration,
                is_simulated=self.config.simulation,
            )
            self.swarm[name] = crazyflie_robot
            while not crazyflie_robot.initialize():
                time.sleep(0.5)

        # * Subscriptions
        self.led_subscribers: Dict[str, Subscription] = {}
        for name, _ in self.swarm.items():
            self.led_subscribers[name] = self.create_subscription(
                Float32,
                f"/{name}/led",
                lambda msg, name=name: self.led_callback(msg, name),
                10,
            )

        self.velocity_subscribers: Dict[str, Subscription] = {}
        for name, _ in self.swarm.items():
            self.velocity_subscribers[name] = self.create_subscription(
                Twist,
                f"/{name}/cmd_vel",
                lambda msg, name=name: self.velocity_callback(msg, name),
                10,
            )

        self.attitude_subscribers: Dict[str, Subscription] = {}
        for name, _ in self.swarm.items():
            self.attitude_subscribers[name] = self.create_subscription(
                Twist,
                f"/{name}/cmd_attitude_setpoint",
                lambda msg, name=name: self.attitude_callback(msg, name),
                10,
            )

        # * Publishers

        # * TF Broadcaster
        self.tf_broadcaster = TransformBroadcaster(self)

        # * State Publisher
        self.state_publishers: Dict[str, Publisher] = {}
        self.pose_publishers: Dict[str, Publisher] = {}
        state_publisher_rate = self.config.state_publisher_rate
        for name, _ in self.swarm.items():
            publisher = self.create_publisher(CrazyflieState, f"/{name}/state", 10)
            self.pose_publishers[name] = self.create_publisher(PoseStamped, f"/{name}/pose", 10)
            self.state_publishers[name] = publisher
            self.create_timer(
                1 / state_publisher_rate,
                lambda name=name, publisher=publisher: self.state_callback(name, publisher),
            )

        # * Services
        self.take_off_service = self.create_service(
            TakeOff, "/take_off", self.take_off_service_callback
        )
        self.land_service = self.create_service(Land, "/land", self.land_service_callback)

        # * Timers
        for name, _ in self.swarm.items():
            self.create_timer(0.1, lambda name=name: self.update_robot(name))

    def _get_config(self) -> SwarmConfig:
        self.declare_parameter("swarm_config_path", "")
        swarm_config_path = (
            self.get_parameter("swarm_config_path").get_parameter_value().string_value
        )
        config = load_config(swarm_config_path, SwarmConfig)

        self.get_logger().info("CrazyflieSwarmNode started with parameters:")
        for cf_config in config.crazyflies:
            self.get_logger().info(f"  - {cf_config.name}: {cf_config.uri}")
        return config

    # *Timers Callbacks
    def update_robot(self, name) -> None:
        self.swarm[name].update()

    # * Subscribers Callbacks
    def led_callback(self, msg, name: str) -> None:
        try:
            self.swarm[name].set_led(int(msg.data))

        except Exception as e:
            self.get_logger().error(f"Error in led_callback: {e}")

    def velocity_callback(self, msg: Twist, name: str) -> None:
        velocity_x = msg.linear.x
        velocity_y = msg.linear.y
        yaw_rate = msg.angular.z

        self.get_logger().info(
            f"Velocity command for {name}: {velocity_x}, {velocity_y}, {yaw_rate}"
        )

        try:
            self.swarm[name].set_velocity(velocity_x, velocity_y, yaw_rate)
            pass
        except Exception as e:
            self.get_logger().error(f"Error in velocity_callback: {e}")

    def attitude_callback(self, msg: Twist, name: str) -> None:
        roll = msg.angular.x
        pitch = msg.angular.y
        yaw_rate = msg.angular.z
        thrust = int(msg.linear.z)

        self.get_logger().info(
            f"Attitude command for {name}: {roll}, {pitch}, {yaw_rate}, {thrust}"
        )

        try:
            self.swarm[name].set_attitude(roll, pitch, yaw_rate, thrust)
            pass
        except Exception as e:
            self.get_logger().error(f"Error in attitude_callback: {e}")

    # * Publishers Callbacks
    def state_callback(self, name: str, publisher: Publisher) -> None:
        try:
            state = self.swarm[name].get_state()

            state_msg = CrazyflieState()

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

            state_msg.initial_position[0] = state.init_x
            state_msg.initial_position[1] = state.init_y
            state_msg.initial_position[2] = state.init_z

            publisher.publish(state_msg)

            pose = PoseStamped()
            pose.header.stamp = self.get_clock().now().to_msg()
            pose.header.frame_id = "world"
            pose.pose.position.x = state.x
            pose.pose.position.y = state.y
            pose.pose.position.z = state.z
            q = tft.quaternion_from_euler(
                np.radians(state.roll), np.radians(state.pitch), np.radians(state.yaw)
            )
            pose.pose.orientation.x = q[0]
            pose.pose.orientation.y = q[1]
            pose.pose.orientation.z = q[2]
            pose.pose.orientation.w = q[3]
            self.pose_publishers[name].publish(pose)

            transform = TransformStamped()
            transform.header.stamp = self.get_clock().now().to_msg()
            transform.header.frame_id = "world"
            transform.child_frame_id = name
            transform.transform.translation.x = state.x
            transform.transform.translation.y = state.y
            transform.transform.translation.z = state.z
            q = tft.quaternion_from_euler(
                np.radians(state.roll), np.radians(state.pitch), np.radians(state.yaw)
            )
            transform.transform.rotation.x = q[0]
            transform.transform.rotation.y = q[1]
            transform.transform.rotation.z = q[2]
            transform.transform.rotation.w = q[3]
            self.tf_broadcaster.sendTransform(transform)

        except Exception as e:
            self.get_logger().error(f"Error in state_callback: {e}")

    # * Services Callbacks
    def take_off_service_callback(self, request: TakeOff.Request, response: TakeOff.Response):
        try:
            height = request.height
            duration = request.duration
            self.get_logger().info(f"Take off at {height}m for {duration}s")
            for name, cf in self.swarm.items():
                cf.take_off(height, duration)
            response.success = True

        except Exception as e:
            self.get_logger().error(f"Error in take_off_callback: {e}")
            response.success = False

        return response

    def land_service_callback(self, request: Land.Request, response: Land.Response):
        try:
            self.get_logger().info(f"Land at 0m for {request.duration}s")
            duration = request.duration
            for name, cf in self.swarm.items():
                cf.land(duration)
            response.success = True

        except Exception as e:
            self.get_logger().error(f"Error in land_callback: {e}")
            response.success = False

        return response

    # * Destroy Node Handler
    def destroy_node(self):
        for name, cf in self.swarm.items():
            cf.destroy()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    crazyflie_swarm_node = CrazyflieSwarmNode()
    try:
        rclpy.spin(crazyflie_swarm_node)

    except KeyboardInterrupt:
        crazyflie_swarm_node.land_service_callback()
        pass

    except Exception as e:
        crazyflie_swarm_node.get_logger().error(f"Error in main loop: {e}")

    finally:
        crazyflie_swarm_node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()

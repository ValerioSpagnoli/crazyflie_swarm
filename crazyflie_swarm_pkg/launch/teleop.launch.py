import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    ld = LaunchDescription()

    root = get_package_share_directory("crazyflie_swarm_pkg")

    dock = Node(
        package="crazyflie_swarm_pkg",
        name="crazyflie_teleop_node",
        executable="crazyflie_teleop_exec",
        parameters=[{"swarm_config_path": os.path.join(root, "config/config.yaml")}],
    )

    ld.add_action(dock)

    return ld

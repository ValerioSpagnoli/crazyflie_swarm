import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    ld = LaunchDescription()

    root = get_package_share_directory("crazyflie_swarm_pkg")

    swarm = Node(
        package="crazyflie_swarm_pkg",
        name="crazyflie_swarm_node",
        executable="crazyflie_swarm_exec",
        parameters=[{"config_path": os.path.join(root, "config/config.yaml")}],
    )

    ld.add_action(swarm)

    return ld

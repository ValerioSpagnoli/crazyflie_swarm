import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    ld = LaunchDescription()

    flocking_root = get_package_share_directory("crazyflie_flocking_pkg")
    swarm_root = get_package_share_directory("crazyflie_swarm_pkg")

    flocking = Node(
        package="crazyflie_flocking_pkg",
        name="crazyflie_flocking_node",
        executable="crazyflie_flocking_exec",
        parameters=[
            {
                "flocking_config_path": os.path.join(flocking_root, "config/config.yaml"),
                "swarm_config_path": os.path.join(swarm_root, "config/config.yaml"),
            }
        ],
    )

    ld.add_action(flocking)

    return ld

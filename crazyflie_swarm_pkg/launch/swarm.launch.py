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
        parameters=[{"swarm_config_path": os.path.join(root, "config/config.yaml")}],
    )

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        arguments=[
            "-d"
            + os.path.join(
                get_package_share_directory("crazyflie_swarm_pkg"),
                "config",
                "config.rviz",
            )
        ],
        output="screen",
        parameters=[
            {
                "use_sim_time": True,
            }
        ],
    )

    ld.add_action(swarm)
    ld.add_action(rviz)

    return ld

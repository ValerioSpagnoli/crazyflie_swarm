# Copyright 2022 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node


def generate_launch_description():
    # Configure ROS nodes for launch

    # Setup project paths
    root = get_package_share_directory("crazyflie_simulation_pkg")
    pkg_ros_gz_sim = get_package_share_directory("ros_gz_sim")
    gz_model_path = os.getenv("GZ_SIM_RESOURCE_PATH")

    # Load the SDF file from "description" package
    sdf_file = os.path.join(gz_model_path, "crazyflie_1", "model.sdf")
    with open(sdf_file, "r") as infp:
        robot_desc = infp.read()

    sdf_file = os.path.join(gz_model_path, "crazyflie_2", "model.sdf")
    with open(sdf_file, "r") as infp:
        robot_desc = infp.read()

    sdf_file = os.path.join(gz_model_path, "crazyflie_3", "model.sdf")
    with open(sdf_file, "r") as infp:
        robot_desc = infp.read()

    sdf_file = os.path.join(gz_model_path, "crazyflie_4", "model.sdf")
    with open(sdf_file, "r") as infp:
        robot_desc = infp.read()

    # Setup to launch the simulator and Gazebo world
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, "launch", "gz_sim.launch.py")
        ),
        launch_arguments={
            "gz_args": PathJoinSubstitution(
                [gz_model_path, "worlds", "crazyflie_world.sdf -r"]
            )
        }.items(),
    )

    bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        parameters=[
            {
                "config_file": os.path.join(
                    root, "config", "ros_gz_crazyflie_bridge.yaml"
                ),
            }
        ],
        output="screen",
    )

    cf_sim = Node(
        package="crazyflie_simulation_pkg",
        executable="crazyflie_simulation_exec",
        output="screen",
        parameters=[
            {"swarm_config_path": os.path.join(root, "config/config.yaml")},
        ],
    )

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        arguments=["-d", ""],
        output="screen",
    )

    return LaunchDescription([gz_sim, bridge, cf_sim, rviz])

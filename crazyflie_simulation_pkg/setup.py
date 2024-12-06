import os
from glob import glob

from setuptools import find_packages, setup

package_name = "crazyflie_simulation_pkg"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        (
            "share/ament_index/resource_index/packages",
            ["resource/" + package_name],
        ),
        ("share/" + package_name, ["package.xml"]),
        (os.path.join("share", package_name), glob("launch/*.launch.py")),
        (os.path.join("share", package_name, "config"), glob("config/*.yaml")),
        (
            os.path.join("share", package_name, "gazebo", "meshes"),
            glob("gazebo/meshes/*.dae"),
        ),
        (
            os.path.join(
                "share", package_name, "gazebo", "models", "crazyflie_1"
            ),
            glob("gazebo/models/crazyflie_1/*.sdf"),
        ),
        (
            os.path.join(
                "share", package_name, "gazebo", "models", "crazyflie_2"
            ),
            glob("gazebo/models/crazyflie_2/*.sdf"),
        ),
        (
            os.path.join(
                "share", package_name, "gazebo", "models", "crazyflie_3"
            ),
            glob("gazebo/models/crazyflie_3/*.sdf"),
        ),
        (
            os.path.join(
                "share", package_name, "gazebo", "models", "crazyflie_4"
            ),
            glob("gazebo/models/crazyflie_4/*.sdf"),
        ),
        (
            os.path.join("share", package_name, "gazebo", "models", "worlds"),
            glob("gazebo/models/worlds/*.sdf"),
        ),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="valeriospagnoli",
    maintainer_email="spagnoli.valerio.00@gmail.com",
    description="TODO: Package description",
    license="TODO: License declaration",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "crazyflie_simulation_exec = crazyflie_simulation_pkg.nodes.crazyflie_simulation_node:main",
        ],
    },
)

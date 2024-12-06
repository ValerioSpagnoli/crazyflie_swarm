import os
from glob import glob

from setuptools import find_packages, setup

package_name = "crazyflie_swarm_pkg"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(".", exclude=["test"]),
    package_dir={"": "."},  # Tell setuptools that packages are under current dir
    data_files=[
        (
            "share/ament_index/resource_index/packages",
            ["resource/" + package_name],
        ),
        ("share/" + package_name, ["package.xml"]),
        (
            os.path.join("share", package_name),
            glob("launch/*launch.[pxy][yma]*"),
        ),
        (os.path.join("share", package_name, "config"), glob("config/*.yaml")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Valerio Spagnoli",
    maintainer_email="spagnoli.valerio.00@gmail.com",
    description="TODO: Package description",
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "crazyflie_swarm_exec = crazyflie_swarm_pkg.nodes.crazyflie_swarm_node:main",
            "crazyflie_teleop_exec = crazyflie_swarm_pkg.nodes.crazyflie_teleop_node:main",
            "data_recorder_exec = crazyflie_swarm_pkg.nodes.data_recorder_node:main",
        ],
    },
)

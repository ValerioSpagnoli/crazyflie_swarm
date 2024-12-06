import os
from glob import glob

from setuptools import find_packages, setup

package_name = "crazyflie_flocking_pkg"

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
    maintainer="neverorfrog",
    maintainer_email="97flavio.maiorana@gmail.com",
    description="TODO: Package description",
    license="TODO: License declaration",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            f"crazyflie_flocking_exec = {package_name}.nodes.crazyflie_flocking_node:main",
        ],
    },
)

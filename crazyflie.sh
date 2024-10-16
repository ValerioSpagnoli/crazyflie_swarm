alias swarm='ros2 launch crazyflie_swarm_pkg swarm.launch.py'
alias dock='ros2 launch crazyflie_swarm_pkg dock.launch.py'
alias takeoff='ros2 service call /take_off crazyflie_swarm_interfaces/srv/TakeOff "{height: 0.25, duration: 1}"'
alias land='ros2 service call /land crazyflie_swarm_interfaces/srv/Land "{duration: 3}"'
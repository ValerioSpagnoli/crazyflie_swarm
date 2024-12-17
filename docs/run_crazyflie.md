# Run Crazyflie

## Take Off and Land
- Take Off:
  ```
  ros2 service call /take_off crazyflie_swarm_interfaces/srv/TakeOff "{height: 0.25, duration: 1}"
  ```
- Land
  ```
  ros2 service call /land crazyflie_swarm_interfaces/srv/Land "{duration: 3}"
  ```
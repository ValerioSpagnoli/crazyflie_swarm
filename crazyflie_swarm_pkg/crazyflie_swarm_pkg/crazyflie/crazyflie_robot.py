import time
from threading import Event
from typing import Dict

from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.crazyflie.syncLogger import SyncLogger
from cflib.utils.multiranger import Multiranger

from crazyflie_swarm_pkg.crazyflie.crazyflie_state import CrazyState
from crazyflie_swarm_pkg.utils import RangeDirection, RingBuffer, log


class CrazyflieRobot:
    def __init__(
        self,
        uri,
        name=None,
        ro_cache=None,
        rw_cache=None,
        logger=None,
        multiranger=False,
        initial_position=None,
        default_take_off_height=0.2,
        default_take_off_duration=3
    ):
        self.uri = uri
        self.name = name
        self.cf = Crazyflie(ro_cache=ro_cache, rw_cache=rw_cache)
        self.scf = SyncCrazyflie(self.uri, cf=self.cf)
        self.logger = logger

        self.default_take_off_height = default_take_off_height
        self.default_take_off_duration = default_take_off_duration
        self.default_land_duration = 3
        self.default_height = 0.2
        self.default_velocity = 0.1
        self.emergency_stop_distance = 0.3 # TODO: put in config

        # State
        self.initial_position = initial_position
        self.state = CrazyState()
        self.state.init_x = initial_position.x
        self.state.init_y = initial_position.y
        self.state.init_z = initial_position.z
        
        log(f"{self.state}", self.logger)
        
        self.estimators: Dict[str, LogConfig] = {}

        # Connection
        self.__connection_timeout = 10  # seconds
        self.__connection_opened = False

        # Flow deck
        self.__flow_deck_attached = False
        self.flow_deck_attached_event = Event()
        self.flow_deck_attached_event.clear()

        # Multiranger
        multiranger_buffer_size = 10
        self.multiranger = multiranger
        self.__multiranger_attached = False
        self.multiranger_attached_event = Event()
        self.multiranger_attached_event.clear()
        self.multiranger_sensor = Multiranger(self.scf)
        self.__buffer: Dict[RangeDirection, RingBuffer] = {}
        self.__buffer[RangeDirection.FRONT] = RingBuffer(
            multiranger_buffer_size, (1,)
        )
        self.__buffer[RangeDirection.RIGHT] = RingBuffer(
            multiranger_buffer_size, (1,)
        )
        self.__buffer[RangeDirection.BACK] = RingBuffer(
            multiranger_buffer_size, (1,)
        )
        self.__buffer[RangeDirection.LEFT] = RingBuffer(
            multiranger_buffer_size, (1,)
        )
        self.__buffer[RangeDirection.UP] = RingBuffer(
            multiranger_buffer_size, (1,)
        )
        self.__mean_buffer: Dict[RangeDirection, float] = {}
        self.__mean_buffer[RangeDirection.FRONT] = 0.0
        self.__mean_buffer[RangeDirection.RIGHT] = 0.0
        self.__mean_buffer[RangeDirection.BACK] = 0.0
        self.__mean_buffer[RangeDirection.LEFT] = 0.0
        self.__mean_buffer[RangeDirection.UP] = 0.0

        self.take_off_done = False
        self.is_flying = False

    # * Initialization
    def initialize(self):
        log(f"Connecting to Crazyflie {self.name} ...", self.logger)
        start_initialization = time.time()
        self.open_connection()

        # * Led sanity check
        self.set_led(255.0)

        self.scf.cf.param.add_update_callback(
            group="deck", name="bcFlow2", cb=self.flow_deck_attached_callback
        )
        if self.multiranger:
            self.scf.cf.param.add_update_callback(
                group="deck",
                name="bcMultiranger",
                cb=self.multiranger_deck_attached_callback,
            )

        while (
            not self.__connection_opened
            or not self.__flow_deck_attached
            or (not self.__multiranger_attached and self.multiranger)
        ):
            if time.time() - start_initialization > self.__connection_timeout:
                log(f"Initialization timeout for {self.name}", self.logger)
                self.close_connection()
                return False
            time.sleep(0.1)

        log(f"Crazyflie {self.name} connected.", self.logger)

        log(
            f"Resetting estimators of Crazyflie {self.name} ...",
            self.logger,
        )
        self.reset_estimator()
        log(f"Estimators of Crazyflie {self.name} reset.", self.logger)

        log(
            f"Starting estimators of Crazyflie {self.name} ...",
            self.logger,
        )
        self.setup_estimators()
        log(f"Estimators of Crazyflie {self.name} started.", self.logger)

        log(f"Crazyflie {self.name} initialized", self.logger)

        # * Led sanity check
        self.set_led(0.0)

        return True

    def destroy(self):
        # Destroy estimators
        for estimator in self.estimators.values():
            estimator.stop()

        # Destroy multiranger
        self.multiranger_sensor.stop()
        self.multiranger_attached_event.clear()
        self.__multiranger_attached = False

        # Destroy flow deck
        self.flow_deck_attached_event.clear()
        self.__flow_deck_attached = False

        # Close connection
        self.close_connection()
        log(f"Crazyflie {self.name} destroyed", self.logger)

    # Flow deck management
    def flow_deck_attached_callback(self, _, value_str):
        if int(value_str):
            self.flow_deck_attached_event.set()
            self.__flow_deck_attached = True
            log(f"Flow deck attached to {self.name}", self.logger)
        else:
            log(f"Flow deck is not attached to {self.name}", self.logger)

    def multiranger_deck_attached_callback(self, _, value_str) -> None:
        if int(value_str):
            self.multiranger_attached_event.set()
            self.__multiranger_attached = True
            self.multiranger_sensor.start()
            log(f"Multiranger is attached to {self.name}", self.logger)
        else:
            log(f"Multiranger is not attached to {self.name}", self.logger)

    # Connection management
    def open_connection(self):
        if self.__connection_opened:
            raise Exception("Connection already opened")
        try:
            self.scf.open_link()
            self.__connection_opened = True
        except Exception as e:
            log(f"Error opening connection: {e}", self.logger)
            self.close_connection()
            raise e

    def close_connection(self):
        self.__connection_opened = False
        self.scf.close_link()

    # * Update
    def update(self):

        # * Multirange values (filled only if above a certain height)
        if self.state.z > 0.1:
            self.__buffer[RangeDirection.FRONT].append(
                self.multiranger_sensor.front
            )
            self.__buffer[RangeDirection.RIGHT].append(
                self.multiranger_sensor.right
            )
            self.__buffer[RangeDirection.BACK].append(
                self.multiranger_sensor.back
            )
            self.__buffer[RangeDirection.LEFT].append(
                self.multiranger_sensor.left
            )
            self.__buffer[RangeDirection.UP].append(self.multiranger_sensor.up)
            self.__mean_buffer[RangeDirection.FRONT] = self.__buffer[
                RangeDirection.FRONT
            ].compute_mean()
            self.__mean_buffer[RangeDirection.RIGHT] = self.__buffer[
                RangeDirection.RIGHT
            ].compute_mean()
            self.__mean_buffer[RangeDirection.BACK] = self.__buffer[
                RangeDirection.BACK
            ].compute_mean()
            self.__mean_buffer[RangeDirection.LEFT] = self.__buffer[
                RangeDirection.LEFT
            ].compute_mean()
            self.__mean_buffer[RangeDirection.UP] = self.__buffer[
                RangeDirection.UP
            ].compute_mean()

        # * Handle take off and land
        z = self.state.z
        if not self.take_off_done and z >= self.default_take_off_height - 0.05:
            log(f"Take off done for Crazyflie {self.name}", self.logger)
            self.take_off_done = True
            self.is_flying = True

        if self.take_off_done and z <= 0.05:
            log(f"Land done for Crazyflie {self.name}", self.logger)
            self.cf.commander.send_stop_setpoint()
            self.is_flying = False
            self.take_off_done = False

        # * Handle multirange
        if self.multiranger and self.take_off_done:
            if (
                self.__mean_buffer[RangeDirection.FRONT]
                < self.emergency_stop_distance
                or self.__mean_buffer[RangeDirection.RIGHT]
                < self.emergency_stop_distance
                or self.__mean_buffer[RangeDirection.BACK]
                < self.emergency_stop_distance
                or self.__mean_buffer[RangeDirection.LEFT]
                < self.emergency_stop_distance
            ):
                log(f"Emergency stop for Crazyflie {self.name}", self.logger)
                self.emergency_stop()

    # * Commands
    def take_off(self, absolute_height=None, duration=None):
        if not self.__connection_opened:
            raise Exception("Connection not opened")
        if not self.__flow_deck_attached:
            raise Exception("Flow deck not attached")
        if self.multiranger and not self.__multiranger_attached:
            raise Exception("Multiranger not attached")

        if absolute_height is None:
            absolute_height = self.default_take_off_height
        if duration is None:
            duration = self.default_take_off_duration
        self.cf.commander.send_hover_setpoint(0, 0, 0, absolute_height)

    def land(self, duration=None):
        self.is_flying = False
        if duration is None:
            duration = self.default_land_duration
        self.cf.commander.send_velocity_world_setpoint(0, 0, -0.05, 0)

    def emergency_stop(self):
        self.cf.commander.send_stop_setpoint()

    def set_velocity(self, vx, vy, yaw_rate):
        if not self.__connection_opened:
            raise Exception("Connection not opened")
        if not self.__flow_deck_attached:
            raise Exception("Flow deck not attached")
        if self.multiranger and not self.__multiranger_attached:
            raise Exception("Multiranger not attached")
        if not self.is_flying:
            log(f"Not flying {self.name}", self.logger)
            return
        self.cf.commander.send_hover_setpoint(
            vx, vy, yaw_rate, self.default_take_off_height
        )

    # * Setters
    def set_led(self, intensity):
        try:
            self.cf.param.set_value("led.bitmask", intensity)
        except Exception as e:
            log(f"Error setting led intensity: {e}", self.logger)

    # * Getters
    def get_state(self) -> CrazyState:
        self.get_multiranger_data()
        return self.state

    def get_multiranger_data(self):
        self.state.mr_front = self.__mean_buffer[RangeDirection.FRONT]
        self.state.mr_right = self.__mean_buffer[RangeDirection.RIGHT]
        self.state.mr_back = self.__mean_buffer[RangeDirection.BACK]
        self.state.mr_left = self.__mean_buffer[RangeDirection.LEFT]
        self.state.mr_up = self.__mean_buffer[RangeDirection.UP]

    def pose_estimator_callback(self, timestamp, data, logconf):
        self.state.x = data["stateEstimate.x"] + self.initial_position.x
        self.state.y = data["stateEstimate.y"] + self.initial_position.y
        self.state.z = data["stateEstimate.z"] + self.initial_position.z
        self.state.roll = data["stabilizer.roll"]
        self.state.pitch = data["stabilizer.pitch"]
        self.state.yaw = data["stabilizer.yaw"]

    def setup_estimators(self):
        pose_estimator = LogConfig(name="Pose", period_in_ms=10)
        pose_estimator.add_variable("stateEstimate.x", "float")
        pose_estimator.add_variable("stateEstimate.y", "float")
        pose_estimator.add_variable("stateEstimate.z", "float")
        pose_estimator.add_variable("stabilizer.roll", "float")
        pose_estimator.add_variable("stabilizer.pitch", "float")
        pose_estimator.add_variable("stabilizer.yaw", "float")
        self.cf.log.add_config(pose_estimator)
        pose_estimator.data_received_cb.add_callback(
            self.pose_estimator_callback
        )
        pose_estimator.start()
        self.estimators["pose"] = pose_estimator

    # * Estimator Reset
    def reset_estimator(self):
        self.cf.param.set_value("kalman.resetEstimation", "1")
        time.sleep(0.1)
        self.cf.param.set_value("kalman.resetEstimation", "0")

        log_config = LogConfig(name="Kalman Variance", period_in_ms=500)
        log_config.add_variable("kalman.varPX", "float")
        log_config.add_variable("kalman.varPY", "float")
        log_config.add_variable("kalman.varPZ", "float")

        var_y_history = [1000] * 10
        var_x_history = [1000] * 10
        var_z_history = [1000] * 10

        threshold = 0.001

        with SyncLogger(self.scf, log_config) as logger:
            for log_entry in logger:
                data = log_entry[1]

                var_x_history.append(data["kalman.varPX"])
                var_x_history.pop(0)
                var_y_history.append(data["kalman.varPY"])
                var_y_history.pop(0)
                var_z_history.append(data["kalman.varPZ"])
                var_z_history.pop(0)

                min_x = min(var_x_history)
                max_x = max(var_x_history)
                min_y = min(var_y_history)
                max_y = max(var_y_history)
                min_z = min(var_z_history)
                max_z = max(var_z_history)

                if (
                    (max_x - min_x) < threshold
                    and (max_y - min_y) < threshold
                    and (max_z - min_z) < threshold
                ):
                    break

from typing import Type, TypeVar

import yaml
from omegaconf import OmegaConf
from rclpy.impl.rcutils_logger import RcutilsLogger


def log(
    message="", ros2_logger: RcutilsLogger = None, ros2_logger_level="info"
) -> None:
    if ros2_logger is None:
        print(message)
        return

    if ros2_logger_level == "info":
        ros2_logger.info(message)
    elif ros2_logger_level == "warn":
        ros2_logger.warn(message)
    elif ros2_logger_level == "error":
        ros2_logger.error(message)
    elif ros2_logger_level == "debug":
        ros2_logger.debug(message)
    else:
        ros2_logger.info(message)

    return


T = TypeVar("T")


def load_config(file_path: str, config_class: Type[T]) -> T:
    """
    Load configuration from a YAML file and merge it into a configuration object of the specified class.

    Args:
      file_path (str): The path to the YAML configuration file.
      config_class (Type[T]): The class of the configuration object.

    Returns:
      T: The merged configuration object.
    """
    with open(file_path, "r") as file:
        try:
            config: T = OmegaConf.structured(config_class)
            data = OmegaConf.create(yaml.safe_load(file))
            OmegaConf.unsafe_merge(config, data)
            return config
        except yaml.YAMLError as e:
            print(f"Error decoding YAML: {e}")
            return config_class()

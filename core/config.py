import os

import yaml

from core.exceptions import ConfigParseError


def load_config(file_path="core/config/config.yaml"):
    """ Parse config YAML and return as dict """
    try:
        with open(file_path, "r", encoding="utf-8") as config_file:
            return yaml.safe_load(config_file)
    except FileNotFoundError:
        exc_msg = (
            "Config file does not exist, please create 'core/config/config.yaml' "
            "from 'core/config/config.example.yaml'"
        )
        raise FileNotFoundError(exc_msg)  # pylint: disable=raise-missing-from
    except yaml.YAMLError as exc:
        raise ConfigParseError(f"Error parsing YAML file: {exc}")  # pylint: disable=raise-missing-from


def is_prod():
    """Returns True if the environment is prod, otherwise return False."""
    return os.getenv("ENVIRONMENT") == "prod"


config = load_config()

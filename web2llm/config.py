import collections.abc
import logging
from pathlib import Path

import yaml

try:
    # Python 3.9+
    import importlib.resources as pkg_resources
except ImportError:
    # Python < 3.9
    import importlib_resources as pkg_resources

logger = logging.getLogger(__name__)


def _deep_merge_dict(base: dict, new: dict) -> dict:
    """
    Recursively merges dict `new` into `base`.
    If a key exists in both and the value is a dict, it merges the sub-dicts.
    Otherwise, the value from `new` overwrites the value in `base`.
    """
    for key, value in new.items():
        if isinstance(value, collections.abc.Mapping) and key in base and isinstance(base[key], collections.abc.Mapping):
            base[key] = _deep_merge_dict(base[key], value)
        else:
            base[key] = value
    return base


def load_and_merge_configs() -> dict:
    """Loads configuration with a clear priority: Defaults < Project Config."""
    with pkg_resources.open_text(__package__, "default_config.yaml") as f:
        config = yaml.safe_load(f)

    project_config_path = Path.cwd() / ".web2llm.yaml"
    if project_config_path.is_file():
        logger.info(f"Found project configuration at: {project_config_path}")
        with open(project_config_path, "r", encoding="utf-8") as f:
            project_config = yaml.safe_load(f)
        if project_config:
            config = _deep_merge_dict(config, project_config)
    return config

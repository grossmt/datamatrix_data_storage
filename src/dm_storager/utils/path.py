from pathlib import Path


SCRIPT_PATH = Path.cwd()


def application_path() -> Path:
    """Return app root path."""
    return SCRIPT_PATH


def default_settings_dir_path() -> Path:
    """Return default abs path to settings dir."""
    return SCRIPT_PATH / "settings"


def default_settings_path() -> Path:
    """Return default config file path."""
    return SCRIPT_PATH / "settings" / "settings.toml"


def default_log_dir() -> Path:
    """Return default abs path to log dir."""
    return SCRIPT_PATH / "logs"


def default_log_file() -> Path:
    """Return default abs path to log dir."""
    return default_log_dir() / "server_log"


def default_data_folder() -> Path:
    """Return default data folder."""
    return SCRIPT_PATH / "saved_data"

from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parent.parent


def application_path() -> Path:
    """Return app root path."""
    return SCRIPT_PATH


def assets_path() -> Path:
    """Return abs path to assets inside app."""
    return SCRIPT_PATH / "assets"


def config_template_path() -> Path:
    """Return default config file path."""
    return assets_path() / "settings_template.toml"

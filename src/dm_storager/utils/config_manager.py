import toml, rtoml
import os
import click
import socket
from pathlib import Path
from typing import Optional, List

from dm_storager import Config
from dm_storager.assets import TEMPLATE_CONFIG
from dm_storager.utils.path import default_settings_dir_path, default_settings_path

MIN_PORT_NUMBER = 1024
MAX_PORT_NUMBER = 65536


def get_config(config_file_path: Path) -> Optional[Config]:
    """Get formatted config from given file or create default one,
    if config file does not exist.

    Arguments:
        config_file_path (Path): path to config file

    Returns:
        Config: dict of server configuration.
    """

    if config_file_path.exists():
        try:
            parsed_config = _load_config(config_file_path)
        except Exception as ex:
            click.echo("Settings file was corrupted!")
            click.echo(f"Reason: {str(ex)}")
            click.echo("Fix it or delete and configure new one from template.")
            return None
        return parsed_config

    if config_file_path == default_settings_path():
        # create new from default asset
        click.echo("No settings were found on default path.")
        click.echo("Creating new settings file from default.")
        template_config = _fill_template_config()

        save_result: bool = _save_config(config_file_path, template_config)
        if save_result:
            click.echo(f"New default settings were created at {str(config_file_path)}")
            click.echo("Please fill it with valid scanner info and restart programm.")
    else:
        click.echo("File not found. Please verify the settings path.")

    return None


def _load_config(path_to_config_file: Path) -> Config:
    config_dict = toml.load(path_to_config_file)
    return Config(**config_dict)


def _save_config(settings_path: Path, config: Config) -> bool:
    try:
        os.makedirs(default_settings_dir_path(), exist_ok=True)
    except OSError:
        click.echo("Failed to create directory with settings.")
        click.echo("Please be sure you have permissions on this directory.")
        return False

    try:
        with open(settings_path, "w") as settings_file:
            toml.dump(
                config.dict(),
                settings_file,
                encoder=toml.TomlPreserveInlineDictEncoder(),
            )
            # rtoml.dump(config.dict(), settings_file, pretty=True)

    except Exception:
        click.echo("Failed to create settings file.")
        click.echo("Please be sure you have permissions on this directory.")
        return False

    return True


def _resolve_local_addresses() -> List[str]:

    hostname = socket.gethostname()
    local_ips = socket.gethostbyname_ex(hostname)
    result = []
    for ip in local_ips[2]:
        result.append(ip)
    return result


def _fill_template_config():
    click.echo("Configuring server...")

    ips = _resolve_local_addresses()
    i = 0

    if len(ips) > 1:
        click.echo(f"Found {len(ips)} avaliable interfaces.")

        click.echo(
            "Please select the number of the interface, where server will be run:"
        )
        for ip in ips:
            click.echo(f"\t[{ips.index(ip)}]: {ip}")

        is_correct_input = False
        while not is_correct_input:
            _i = input()

            try:
                i = int(_i)
                if i not in range(len(ips)):
                    raise
            except Exception:
                is_correct_input = False
                click.echo(
                    f"Please select the number of interface in [0; {len(ips) - 1}]"
                )
                continue

            is_correct_input = True

        click.echo(f"You have selected {ips[i]}")
    else:
        click.echo(f"Found single avaliable interface: {ips[0]}")

    server_address = ips[i]

    click.echo(
        f"Enter the port between {MIN_PORT_NUMBER} and {MAX_PORT_NUMBER}, where server will be run:"
    )
    is_correct_input = False
    while not is_correct_input:
        _i = input()
        try:
            port = int(_i)
            if port not in range(MIN_PORT_NUMBER, MAX_PORT_NUMBER):
                raise
        except Exception:
            is_correct_input = False
            click.echo(
                f"Please enter the port number: [{MIN_PORT_NUMBER}; {MAX_PORT_NUMBER}]"
            )
            continue

        is_correct_input = True

    click.echo(f"Configured server address: {server_address}:{port}")

    click.echo("Creating configured settings file from template...")

    _config = TEMPLATE_CONFIG
    _config.server.host = server_address
    _config.server.port = port

    _config.clients["scanner_0"]["settings"].server_ip = server_address
    _config.clients["scanner_0"]["settings"].server_port = port

    return _config

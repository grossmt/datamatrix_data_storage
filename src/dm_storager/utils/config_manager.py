import toml
import os
import click
from pathlib import Path
from typing import Optional
from socket import inet_aton as ip_str_to_bytes

from dm_storager import Config
from dm_storager.assets import TEMPLATE_CONFIG
from dm_storager.structs import Scanner, ScannerSettings
from dm_storager.utils.path import default_settings_path
from dm_storager.utils.logger import configure_logger
from dm_storager.utils.network import (
    MIN_PORT_NUMBER,
    MAX_PORT_NUMBER,
    resolve_local_addresses,
)
from dm_storager.utils.string_formatter import hexify_id

CONFIG_ENABLE_LIST = ("y", "yes", "Y", "enable", "Enable", "ENABLE", "true", "True")


class ConfigManager:
    """Config manager for DataMatrix Storager."""

    def __init__(self, config_file_path: Path) -> None:
        self._config_path = config_file_path
        self._logger = configure_logger("CONFIG_MNGR", False)

        self._config: Optional[Config] = self.get_config(config_file_path)

    @property
    def config(self) -> Optional[Config]:
        return self._config

    @property
    def config_path(self) -> Path:
        return self._config_path

    def save_config(self, config: Config, config_path: Path) -> bool:
        """Save given config to specified path.

        Args:
            config (Config): dict of server configuration.
            config_path (Path): desired path to save.

        Returns:
            bool: status of saving config.
        """
        try:
            os.makedirs(config_path.parent, exist_ok=True)
        except OSError:
            self._logger.error("Failed to create directory with settings.")
            self._logger.error("Please be sure you have permissions on this directory.")
            return False

        try:
            with open(config_path, "w") as settings_file:
                toml.dump(
                    config.dict(),
                    settings_file,
                )

        except Exception:
            self._logger.error("Failed to save settings to file.")
            self._logger.error("Please be sure you have permissions on this directory.")
            return False

        self._logger.info(f"Config was successfully saved to {str(config_path)}")
        return True

    def get_config(self, config_path: Path) -> Optional[Config]:
        """Get formatted config from the file or create default one,
        if config file does not exist.

        Returns:
            Config: dict of server configuration.
        """

        self._logger.info(f"Retrieving config from {str(config_path)}")
        if config_path.exists():
            try:
                parsed_config = self._load_config(config_path)
            except Exception as ex:
                self._logger.error("Settings file was corrupted!")
                self._logger.error(f"Reason: {str(ex)}")
                self._logger.error(
                    "Fix it or delete and configure new one from template."
                )
                return None

            self._logger.info("Validation of settings...")
            if self.validate_config(parsed_config):
                self._logger.info("Settings OK")
                self._config = parsed_config
                return parsed_config

            self._logger.error("Fix given issues and restart the program.")
            return None

        if config_path == default_settings_path():
            # create new from default asset
            self._logger.warning("No settings were found on default path.")
            self._logger.warning("Creating new settings file from default.")
            template_config = self._fill_template_config()

            save_result: bool = self.save_config(template_config, config_path)
            if save_result:
                self._logger.info(
                    f"New default settings were created at {str(config_path)}"
                )
                self._logger.info(
                    "Please fill it with valid scanner info and restart programm."
                )
            else:
                return None
        else:
            self._logger.error("File not found. Please verify the settings path.")

        return None

    def validate_config(self, config: Config) -> bool:
        """Validates given config.

        Specially validates:
            - Unique ID of scanners. All scanners ID's are converted to HEX value.
            - IP Address of scanner. Must be valid IPv4 address.

        Args:
            config (Config): given dict of server config

        Returns
            bool: is config valid
        """
        is_valid = True

        for client_id in config.scanners.copy():
            hex_id = None

            hex_id = hexify_id(client_id)

            if not hex_id:
                self._logger.error("Given settings are invalid:")
                self._logger.error(f"\tFound wrong scanner ID: {client_id}")
                continue

            # Replace current record with formatted ID
            try:
                config.scanners[hex_id]
            except KeyError:
                config.scanners[hex_id] = config.scanners.pop(client_id)
            else:
                is_valid = False
                click.echo("Given settings are invalid:")
                click.echo(f"\tFound dublicate scanner ID: {hex_id}")
                continue

            # validate scanner address
            try:
                ip_str_to_bytes(config.scanners[str(hex_id)]["info"].address)
            except OSError:
                click.echo("Given settings are invalid:")
                ip = config.scanners[str(hex_id)]["info"].address
                click.echo(f"\tFound wrong IP address: scanner ID: {hex_id}, IP: {ip}")
                is_valid = False

        return is_valid

    def add_new_scanner(self, scanner: Scanner) -> bool:
        """Add new scanner to active config and saves it to current path.

        If scanner settings are valid and file is accessible, returns positive.

        Args:
            scanner (Scanner): new scanner to save.

        Returns:
            bool: status of saving
        """

        is_valid = self.validate_new_scanner(scanner)
        if not is_valid:
            return False

        if self._config is None:
            self._logger.error("Config is not initialized!")
            return False

        # TODO: Implement scanner saving
        correct_id = hexify_id(scanner.scanner_id)

        # new_record: ScannerSettings = {}
        # new_record[correct_id]

        # self._config.scanners[correct_id] = scanner

        pass

    def validate_new_scanner(self, scanner: Scanner) -> bool:
        """Validates given scanner.

        Specially validates:
            - ID of scanner. It must be correct and unique.
            - Address of scanner. (Not implemented yet)

        Returns:
            bool: validation status
        """
        correct_id = hexify_id(scanner.scanner_id)
        if not correct_id:
            self._logger.error(
                f"Given scanner is not valid: Bad ID {scanner.scanner_id}"
            )
            return False

        if self._config is None:
            # config is not created yet
            return False

        try:
            self._config.scanners[correct_id]
        except KeyError:
            pass
        else:
            self._logger.error(
                f"Given scanner is not valid: Not Unique ID: {correct_id}"
            )
            return False

        # validate scanner ips
        pass

        return True

    def _load_config(self, config_path: Path) -> Config:
        config_dict = toml.load(config_path)
        return Config(**config_dict)

    def _fill_template_config(self):
        click.echo("Configuring server...")

        ips = resolve_local_addresses()
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
            f"Enter the port between {MIN_PORT_NUMBER} and {MAX_PORT_NUMBER}, where server will be run:"  # noqa: E501
        )
        is_correct_input = False
        port = 0
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

        TEMPLATE_CONFIG.server.host = server_address
        TEMPLATE_CONFIG.server.port = port

        TEMPLATE_CONFIG.scanners["1"]["settings"].server_ip = server_address
        TEMPLATE_CONFIG.scanners["1"]["settings"].server_port = port

        # TEMPLATE_CONFIG.scanners["0x0001"]["settings"].server_ip = server_address
        # TEMPLATE_CONFIG.scanners["0x0001"]["settings"].server_port = port

        gateway_ip = server_address.replace(server_address.split(".")[3], "1")
        # TEMPLATE_CONFIG.scanners["0x0001"]["settings"].gateway_ip = gateway_ip
        TEMPLATE_CONFIG.scanners["1"]["settings"].gateway_ip = gateway_ip

        return TEMPLATE_CONFIG

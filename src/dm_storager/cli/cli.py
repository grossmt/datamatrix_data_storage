from ssl import PROTOCOL_TLS_SERVER
import click
import multiprocessing
import shutil

from pathlib import Path

from dm_storager.cli import opts
from dm_storager.utils.logger import configure_logger
from dm_storager.utils.network_settings import resolve_local_addresses
from dm_storager.utils.path import config_template_path
from dm_storager.assets.settings_template import TEMPLATE_CONFIG


@click.command()
@opts.config_opt
@opts.debug_flag
@click.pass_context
def main(context: click.Context, config_file_path: Path, debug: bool):
    """Data Matrix Storager system."""
    click.echo("")  # separate program output form user input
    multiprocessing.freeze_support()

    is_config_ok = _check_config(config_file_path)

    if not is_config_ok:
        context.exit()

    main_logger = configure_logger("SCANNER DATAMATRIX STORAGER", debug)

    print("Aborting program.")


def _check_config(config_file_path: Path) -> bool:
    """Check if config exists and generate it in user current dir if it doesn't.

    Arguments:
        config_file_path (Path): path to config file

    Returns:
        bool: if config exists and different from default one
    """

    if config_file_path == config_template_path():  # entered default template file
        generated_config = Path.cwd() / "connection_settings.toml"

        if generated_config.exists():
            click.echo(
                f'"{config_file_path}" exists! Set `--config` '
                f'argument to "{config_file_path}" to use it.'
            )
        else:
            pass

            # shutil.copy(
            #     src=config_template_path(), dst=Path.cwd() / "connection_settings.toml"
            # )
            # click.echo(
            #     f'"{config_file_path}" was generated. Please, '
            #     "fill it and restart app with `--config` argument."
            # )

            # Now we should configure default template config
            _fill_template_config()

        return False

    return True


def _fill_template_config():

    click.echo("You have selected default settings file.")
    click.echo("Now we should configure it.")

    # Server network settings:
    click.echo("Configuring server...")

    ips = resolve_local_addresses()
    i = 0

    if len(ips) > 0:
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

        print(f"You have selected {ips[i]}")
    else:
        click.echo(f"Found single avaliable interface: {ips[0]}")

    server_address = ips[i]

    click.echo("Enter the port, where server will be run:")
    is_correct_input = False
    while not is_correct_input:
        _i = input()
        try:
            port = int(_i)
            if port not in range(1, 65536):
                raise
        except Exception:
            is_correct_input = False
            click.echo("Please enter the port number: [1; 65536]")
            continue

        is_correct_input = True

    click.echo(f"Configured server address: {server_address}:{port}")
    click.echo("Creating configured settings file from template...")

    _config = TEMPLATE_CONFIG
    _config.subtitle = ""
    _config.server.host = server_address
    _config.server.port = port

    _config.clients["clients.scanner_0"][
        "clients.scanner_0.settings"
    ].server_ip = server_address
    _config.clients["clients.scanner_0"][
        "clients.scanner_0.settings"
    ].server_port = port

    pass

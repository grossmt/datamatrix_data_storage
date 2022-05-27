import click
import multiprocessing
from pathlib import Path

from dm_storager import Server
from dm_storager.cli import opts
from dm_storager.utils import ConfigManager
from dm_storager.utils.logger import configure_logger

from dm_storager.exceptions import ServerStop


@click.command()
@opts.config_opt
@opts.debug_flag
@click.pass_context
def main(context: click.Context, config_file_path: Path, debug: bool):  # noqa: WPS213
    """Data Matrix Storager system."""
    click.echo("")  # separate program output form user input
    multiprocessing.freeze_support()

    config_manager = ConfigManager(config_file_path)

    if not config_manager.config:
        context.exit()

    main_logger = configure_logger("SCANNER DATAMATRIX STORAGER", debug)

    main_logger.info("Creating server with given config.")

    server = Server(config_manager, debug)

    if server.is_configured:
        try:
            server.run_server()
        except ServerStop:
            main_logger.error("Stop server outside.")
        except Exception:
            main_logger.exception("Server runtime error:")
        finally:
            server.stop_server()

    click.echo("")
    main_logger.warning("Aborting program.")

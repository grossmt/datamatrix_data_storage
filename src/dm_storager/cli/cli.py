import click
import multiprocessing
from pathlib import Path
from typing import Optional

from dm_storager import Server, Config
from dm_storager.cli import opts
from dm_storager.utils.logger import configure_logger
from dm_storager.utils.config_manager import get_config

from dm_storager.exceptions import ServerStop


@click.command()
@opts.config_opt
@opts.debug_flag
@click.pass_context
def main(context: click.Context, config_file_path: Path, debug: bool):
    """Data Matrix Storager system."""
    click.echo("")  # separate program output form user input
    multiprocessing.freeze_support()

    server_config: Optional[Config] = get_config(config_file_path)

    if not server_config:
        context.exit()

    main_logger = configure_logger("SCANNER DATAMATRIX STORAGER", debug)

    main_logger.info("Creating server with given config.")

    server = Server(server_config, debug)

    if server.is_configured:
        try:
            server.run_server()
        except ServerStop:
            main_logger.error("Stop server outside.")
            main_logger.error("Aborting program.")
        except Exception:
            main_logger.exception("Server runtime error:")
        finally:
            server.stop_server()

    click.echo("")
    main_logger.warning("Aborting program.")

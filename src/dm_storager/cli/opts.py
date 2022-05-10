import click

from pathlib import Path

from dm_storager.utils.path import config_template_path

config_opt = click.option(
    "-C",
    "--config",
    "config_file_path",
    type=Path,
    prompt=True,
    default=config_template_path(),
    help=(
        "Set a path to config or use default to "
        "generate a config in the current folder"
    ),
)

debug_flag = click.option(
    "--debug",
    default=False,
    is_flag=True,
    help="Enable debug mode.",
)

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import codecs
import logging
from cx_Freeze import setup, Executable


def read(rel_path: str):  # noqa: D103
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), "r", encoding="utf8") as fp:
        return fp.read()


def get_version(rel_path: str):  # noqa: D103
    for line in read(rel_path).splitlines():
        if line.startswith("__version__"):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    raise RuntimeError("Unable to find version string.")


def get_project_name(rel_path: str):  # noqa: D103
    for line in read(rel_path).splitlines():
        if line.startswith("__project_name__"):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    raise RuntimeError("Unable to find project name string.")


# Logger setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",  # noqa: WPS323
)
log = logging.getLogger("app_freezer")


class AppConsts(object):
    """Consts."""

    ICON_PATH: str = "resources/favicon.ico"
    # VERSION: str = get_version("src/digitalizer/__init__.py")
    VERSION: str = "0.2.0"
    # NAME: str = get_project_name("src/digitalizer/__init__.py")
    NAME: str = "DM_Data_Storager"

    # INSTALL_DIR: str = ""
    INSTALL_DIR: str = r"[AppDataFolder]\{0:s}\{1:s}".format("ThirdPin", NAME)

    UUID: str = "{00e671de-d5b1-41ed-b6fa-bc7044ff2e7e}"


log.info("Start freezing console application...")

paths = [*sys.path, "src"]  # paths to search packages into
build_options = {"build_exe": f"built_{AppConsts.NAME}"}
build_exe_options = dict(  # noqa: C408
    packages=[
        "encodings",
    ],
    excludes=[
        "tkinter",
        "flake8",
        "black",
        "mccabe",
        "pycodestyle",
        "pyflakes",
    ],
    build_exe=build_options["build_exe"],
    include_files=[
        "resources",
        # "shared/libusb-1.0.dll",
    ],
    optimize=1,
    path=paths,
)

build_msi_options = {
    "add_to_path": True,
    "all_users": False,
    "initial_target_dir": AppConsts.INSTALL_DIR,
    "upgrade_code": AppConsts.UUID,
    "install_icon": AppConsts.ICON_PATH,
}

executables = [
    Executable(
        "src/dm_storager/__main__.py",
        base="Console",
        icon=AppConsts.ICON_PATH,
        target_name=f"{AppConsts.NAME}.exe",
    )
]


log.info(f'Creating app "{AppConsts.NAME}" with version {AppConsts.VERSION}...')
log.info(f'MSI install path is going to be: "{AppConsts.INSTALL_DIR}"')

setup(
    name=AppConsts.NAME.capitalize(),
    version=AppConsts.VERSION,
    description="",
    options={
        "build": build_options,
        "build_exe": build_exe_options,
        "bdist_msi": build_msi_options,
    },
    executables=executables,
)

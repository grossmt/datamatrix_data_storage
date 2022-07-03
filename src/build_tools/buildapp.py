# -*- coding: utf-8 -*-

import os
import sys
import time
import subprocess
import argparse
import logging

from build_tools.consts import AppConsts
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",  # noqa: WPS323
)


class AppBuilder(object):
    def __init__(self, args):
        self.__is_msi_enabled = bool(args.is_msi_enabled)
        self.__is_debug_enabled = bool(args.is_debug_enabled)

        self._logger = logging.getLogger("APP_FREEZER")

    def execute(self):

        self._logger.info(
            f'Creating app "{AppConsts.NAME}" with version {AppConsts.VERSION}...'
        )
        self._logger.info(
            f'MSI install path is going to be: "{AppConsts.DEFAULT_INSTALL_DIR}"'
        )

        status, msg = self.build()
        if status is True:
            self._logger.info(f"\n\n{msg:s}\n")
        else:
            self._logger.error((f"\n\n{msg:s}\n"))

    def build(self):
        ENVBIN = sys.exec_prefix

        args = [
            f"{ENVBIN}\\python.exe",
            "src\\build_tools\\setup.py",
        ]

        if self.__is_msi_enabled:
            args.extend(("bdist_msi", "-d", "built_msi"))
        else:
            args.append("build")

        if self.__is_debug_enabled:
            args.append("--debug")

        return self.__build(args)

    def __build(self, args):
        env = os.environ.copy()
        task = subprocess.Popen(args, cwd=Path.cwd(), env=env, shell=True)

        timeout = 350

        while (task.poll() is None) and (timeout > 0):
            time.sleep(1)
            timeout -= 1

        if task.poll() == 0:
            return (True, "Build success!")

        return (False, "Build fail!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="AppBuilder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=AppConsts.DESCRIPTION,
    )

    parser.add_argument(
        "--msi",
        action="store_true",
        help="enable a generating an msi file",
        dest="is_msi_enabled",
        default=False,
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="enable debug build with a console",
        dest="is_debug_enabled",
        default=False,
    )

    args = parser.parse_args()

    app = AppBuilder(args)
    app.execute()

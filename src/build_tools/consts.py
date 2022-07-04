import sys
import codecs
from pathlib import Path
from cx_Freeze import Executable


def get_parameter(file_path: Path, param_name: str) -> str:
    with codecs.open(str(file_path), "r", encoding="utf8") as fp:
        _f = fp.readlines()

    for line in _f:
        if line.startswith(f"__{param_name}__"):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    raise RuntimeError(f"Unable to find {param_name} string.")


class AppConsts(object):
    """Consts."""

    AUTHOR = "RFLABC"

    APP_CFG_PATH = Path.cwd() / Path("src") / Path("dm_storager") / Path("__init__.py")

    VERSION = get_parameter(APP_CFG_PATH, "version")
    NAME = get_parameter(APP_CFG_PATH, "project_name")

    DESCRIPTION = f"Utility to build {NAME} application"
    ICON_PATH = str(
        Path.cwd()
        / Path("src")
        / Path("build_tools")
        / Path("resources")
        / Path("favicon.ico")
    )

    DEFAULT_INSTALL_DIR = str(Path(r"[AppDataFolder]") / Path(AUTHOR) / Path(NAME))
    UUID: str = "{00e671de-d5b1-41ed-b6fa-bc7044ff2e7e}"


PATHS = [*sys.path, "dm_storager"]  # paths to search packages into
BUILD_OPTIONS = {"build_exe": f"built_{AppConsts.NAME}"}
BUILD_EXE_OPTIONS = dict(  # noqa: C408
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
    build_exe=BUILD_OPTIONS["build_exe"],
    include_files=[
        "resources",
    ],
    optimize=1,
    path=PATHS,
)

BUILD_MSI_OPTIONS = {
    "add_to_path": True,
    "all_users": False,
    "initial_target_dir": AppConsts.DEFAULT_INSTALL_DIR,
    "upgrade_code": AppConsts.UUID,
    "install_icon": AppConsts.ICON_PATH,
}

EXECUTABLES = [
    Executable(
        "src/dm_storager/__main__.py",
        base="Console",
        icon=AppConsts.ICON_PATH,
        target_name=f"{AppConsts.NAME}.exe",
    )
]

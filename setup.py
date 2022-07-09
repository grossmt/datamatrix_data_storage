"""A setuptools based setup module.
See:
https://packaging.python.org/guides/distributing-packages-using-setuptools/
https://github.com/pypa/sampleproject
"""

import sys
import os
import codecs
from pathlib import Path

from setuptools import setup
from setuptools import find_namespace_packages as find_packages

# Add current current folder to pythonpath for PEP518 build
sys.path.insert(0, os.path.dirname(__file__))

APP_CFG_PATH = Path.cwd() / Path("src") / Path("dm_storager") / Path("__config__.py")


def get_parameter(file_path: Path, param_name: str) -> str:
    with codecs.open(str(file_path), "r", encoding="utf8") as fp:
        _f = fp.readlines()

    for line in _f:
        if line.startswith(f"__{param_name}__"):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    raise RuntimeError(f"Unable to find {param_name} string.")


setup(
    name=get_parameter(APP_CFG_PATH, "project_name"),
    version=get_parameter(APP_CFG_PATH, "version"),
    description="Datamatrix storager application",
    author="RFLABC",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    package_data={
        "dm_storager.assets": [
            "*.toml",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "cx-freeze==6.10",
        "pydantic",
        "toml",
        "click",
        "pypiwin32",
        "concurrent-log-handler",
        "flask",
        "loguru",
    ],
    extras_require={
        "dev": [
            # Linting
            "wemake-python-styleguide",
            "mypy",
            "black",
        ],
        "test": ["pytest", "pytest-dotenv"],
    },
    entry_points={
        "console_scripts": ["dm_storage_server = dm_storager.cli:entry_point"]
    },
)

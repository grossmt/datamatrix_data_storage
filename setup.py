"""A setuptools based setup module.
See:
https://packaging.python.org/guides/distributing-packages-using-setuptools/
https://github.com/pypa/sampleproject
"""

import sys
import os

# Add current current folder to pythonpath for PEP518 build
sys.path.insert(0, os.path.dirname(__file__))

from setuptools import setup
from setuptools import find_namespace_packages as find_packages

setup(
    name="dm_storage_server",
    version="0.2.0",
    description="Server of datamatrix codes storager",
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

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
    version="0.0.1",
    description="Server of datamatrix codes storager",
    author="RFLABC",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=["StrEnum"],
    package_data={
        "robster.rs_nge100.config": [
            "*.json",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    extras_require={
        "dev": [
            "cx-freeze==6.10",
            "pydantic",
            # Linting
            "wemake-python-styleguide",
            "mypy",
            "black==20.8b0",
        ],
        "test": ["pytest", "pytest-dotenv"],
    },
)

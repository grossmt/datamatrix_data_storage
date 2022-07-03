#!/usr/bin/env python
# -*- coding: utf-8 -*-

from cx_Freeze import setup

from build_tools.consts import (
    AppConsts,
    BUILD_OPTIONS,
    BUILD_MSI_OPTIONS,
    BUILD_EXE_OPTIONS,
    EXECUTABLES,
)

setup(
    name=AppConsts.NAME,
    version=AppConsts.VERSION,
    description=AppConsts.DESCRIPTION,
    options={
        "build": BUILD_OPTIONS,
        "build_exe": BUILD_EXE_OPTIONS,
        "bdist_msi": BUILD_MSI_OPTIONS,
    },
    executables=EXECUTABLES,
)

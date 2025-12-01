# Copyright (c) 2025, NVIDIA CORPORATION.
# SPDX-License-Identifier: BSD-3-Clause

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from typing import Iterator

project = "pyhwloc"
copyright = "2025, Jiaming Yuan"
author = "Jiaming Yuan"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx_gallery.gen_gallery",
    "breathe",
]

templates_path = ["_templates"]
exclude_patterns: list[str] = []
autodoc_typehints_format = "short"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "alabaster"
html_static_path = ["_static"]

intersphinx_mapping = {"python": ("https://docs.python.org/3.12", None)}

# -- Build environment

os.environ["PYHWLOC_SPHINX"] = "1"

# -- Gallery
sphinx_gallery_conf = {
    # path to your example scripts
    "examples_dirs": ["../../examples/"],
    # path to where to save gallery generated output
    "gallery_dirs": ["examples"],
}


def is_readthedocs_build() -> bool:
    if os.environ.get("READTHEDOCS", None) == "True":
        return True
    return False


def normpath(path: str) -> str:
    return os.path.normpath(os.path.abspath(path))


@contextmanager
def _chdir(dirname: str) -> Iterator[None]:
    pwd = normpath(os.path.curdir)
    try:
        os.chdir(dirname)
        yield
    finally:
        os.chdir(pwd)


def build_pyhwloc_xml() -> str:
    """Build and install pyhwloc, returns the path to the doxygen xml files."""
    if sys.platform == "win32":
        raise NotImplementedError("Read the docs environment should be Linux.")

    hwloc_version_path = os.path.join(
        PROJECT_ROOT,
        "dev",
        "hwloc_version",
    )
    with open(hwloc_version_path, "r") as fd:
        hwloc_version = fd.read().strip()

    with tempfile.TemporaryDirectory() as tmpdir:
        pwd = normpath(os.path.curdir)
        script = f"""#!/usr/bin/env bash
# Clone
git clone https://github.com/open-mpi/hwloc.git
cd hwloc
git checkout {hwloc_version}

# Config
./autogen.sh
./configure --disable-nvml --enable-doxygen

# Build doc
cd doc
HWLOC_DOXYGEN_GENERATE_XML=YES doxygen ./doxygen.cfg
# Result is in `hwloc/doc/doxygen-doc/xml`

# Copy and cleanup
cp -r doxygen-doc/xml {pwd}/
cd ..
git clean -xdf
"""
        script_path = os.path.join(tmpdir, "build_xml.sh")
        with open(script_path, "w") as fd:
            fd.write(script)

        with _chdir(tmpdir):
            subprocess.check_call(["bash", script_path])
            xml_path = os.path.join(pwd, "xml")

        # Install pyhwloc while we have the hwloc source
        hwloc_src_dir = os.path.join(tmpdir, "hwloc")
        subprocess.check_call(
            [
                "pip",
                "install",
                PROJECT_ROOT,
                "--config-settings=fetch-hwloc=True",
                f"--config-settings=hwloc-src-dir={hwloc_src_dir}",
                "--config-settings=with-cuda=False",
                "--no-deps",
                "--no-build-isolation",
            ]
        )

    return xml_path


# -- Breathe
breathe_default_project = "pyhwloc"
breathe_domain_by_extension = {"h": "c"}

CURR_PATH = os.path.dirname(os.path.abspath(os.path.expanduser(__file__)))  # source
PROJECT_ROOT = os.path.normpath(os.path.join(CURR_PATH, os.path.pardir, os.path.pardir))

if is_readthedocs_build():
    hwloc_xml_path: str | None = build_pyhwloc_xml()
else:
    hwloc_xml_path = os.environ.get("PYHWLOC_XML_PATH", None)
    if hwloc_xml_path is None:
        hwloc_xml_path = os.path.join(
            PROJECT_ROOT, os.path.pardir, "hwloc/doc/doxygen-doc/xml"
        )
breathe_projects = {"pyhwloc": hwloc_xml_path}
print("breathe projects", breathe_projects)

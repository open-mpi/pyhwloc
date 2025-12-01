# Copyright (c) 2025, NVIDIA CORPORATION.
# SPDX-License-Identifier: BSD-3-Clause
"""CMake build script and hatchling hook for pyhwloc."""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface
from packaging.tags import platform_tags

FETCH_KEY = "PYHWLOC_FETCH_HWLOC"
BUILD_KEY = "PYHWLOC_BUILD_DIR"
ROOT_KEY = "PYHWLOC_HWLOC_ROOT_DIR"
SRC_KEY = "PYHWLOC_HWLOC_SRC_DIR"


def get_vs_generator() -> str:
    """Find the latest visual studio version."""
    out = subprocess.run(
        ["cmake", "-G"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    cmake_help = "\n".join([out.stdout.decode(), out.stderr.decode()])
    # ninja doesn't work due to cmake dependency specification.
    # I don't want cmake to pick up mingw somehow.
    vs2026 = "* Visual Studio 18 2026"
    vs2022 = "* Visual Studio 17 2022"

    if vs2026 in cmake_help:
        gen = vs2026
    elif vs2022 in cmake_help:
        gen = vs2022
    else:
        raise NotImplementedError("Requires visual studio >= 17")

    gen = f"-G{gen[2:]}"  # remove the "* "
    return gen


def run_cmake_build(
    source_dir: str | Path,
    build_dir: str | Path,
    build_type: str = "Release",
    parallel_jobs: int | None = None,
    cmake_args: list[str] | None = None,
) -> None:
    """Run CMake build process.

    Parameters
    ----------
    source_dir :
        Source directory containing CMakeLists.txt
    build_dir :
        Build directory for CMake
    build_type :
        CMake build type (Release, Debug, etc.)
    parallel_jobs :
        Number of parallel jobs, defaults to cpu_count()
    cmake_args :
        Additional CMake arguments

    """
    source_path = Path(source_dir).resolve()
    build_path = Path(build_dir).resolve()

    if cmake_args is None:
        cmake_args = []

    if parallel_jobs is None:
        parallel_jobs = os.cpu_count() or 1

    # Create build directory
    build_path.mkdir(exist_ok=True)
    (build_path / "_deps" / "hwloc-build").mkdir(exist_ok=True, parents=True)

    # Configure CMake
    configure_cmd = [
        "cmake",
        "-S",
        str(source_path),
        "-B",
        str(build_path),
        *cmake_args,
    ]
    if platform.system() == "Windows":
        gen = get_vs_generator()
        configure_cmd.append(gen)
    else:
        configure_cmd.append(f"-DCMAKE_BUILD_TYPE={build_type}")

    print(f"CMake config: {' '.join(configure_cmd)}")
    result = subprocess.run(configure_cmd, check=False)
    if result.returncode != 0:
        error_msg = f"CMake configuration failed with code {result.returncode}"
        raise RuntimeError(error_msg)

    # Build with CMake
    build_cmd = [
        "cmake",
        "--build",
        str(build_path),
        "--config",
        build_type,
        "--parallel",
        str(parallel_jobs),
    ]
    print(f"CMake build: {' '.join(build_cmd)}")

    result = subprocess.run(build_cmd, check=False)
    if result.returncode != 0:
        error_msg = f"CMake build failed with code {result.returncode}"
        raise RuntimeError(error_msg)

    install_cmd = [
        "cmake",
        "--install",
        str(build_path),
        "--config",
        build_type,
        "--parallel",
        str(parallel_jobs),
    ]
    print(f"CMake install: {' '.join(install_cmd)}")
    result = subprocess.run(install_cmd, check=False)
    if result.returncode != 0:
        error_msg = f"CMake install failed with code {result.returncode}"
        raise RuntimeError(error_msg)


class CMakeBuildHook(BuildHookInterface):
    """Build hook to run CMake during package building."""

    PLUGIN_NAME = "cmake"

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        """Run CMake build before packaging."""
        # Set platform-specific tag for the wheel
        build_data["tag"] = f"py3-none-{next(platform_tags())}"
        build_data["pure_python"] = False

        print(FETCH_KEY, ":", os.environ.get(FETCH_KEY, None))
        fetch_hwloc = os.environ.get(FETCH_KEY, None)
        # Check if native library already exists
        lib_dir = Path(self.root) / "src" / "pyhwloc" / "_lib"
        if lib_dir.exists() and (
            list(lib_dir.glob("*pyhwloc.so")) or list(lib_dir.glob("*pyhwloc.dll"))
        ):
            print("Native libraries already exist, skipping CMake build")
            return

        # Fetch hwloc
        cmake_args = []
        assert fetch_hwloc in (None, "True", "False")
        if fetch_hwloc == "True":
            cmake_args.append(f"-D{FETCH_KEY}=ON")
            print("Building with fetched hwloc from GitHub")

        # Existing hwloc installation root
        if os.environ.get(ROOT_KEY, None) is not None:
            root_dir = os.environ[ROOT_KEY]
            if not os.path.exists(root_dir):
                raise FileNotFoundError(root_dir)
            cmake_args.append(f"-DHWLOC_ROOT={root_dir}")

        # No CUDA in RTD
        if os.environ.get("READTHEDOCS", None) == "True":
            cmake_args.append("-DPYHWLOC_WITH_CUDA=OFF")

        # Source path
        if os.environ.get(SRC_KEY, None) is not None:
            src_dir = os.environ[SRC_KEY]
            if not os.path.exists(src_dir):
                raise FileNotFoundError(src_dir)
            cmake_args.append(f"-DFETCHCONTENT_SOURCE_DIR_HWLOC={src_dir}")
            assert fetch_hwloc == "True"

        # Build path
        if os.environ.get(BUILD_KEY, None) is not None:
            build_dir = os.environ[BUILD_KEY]
            run_cmake_build(
                source_dir=self.root, build_dir=build_dir, cmake_args=cmake_args
            )
        else:
            with tempfile.TemporaryDirectory() as build_dir:
                print("build-dir:", build_dir)
                run_cmake_build(
                    source_dir=self.root, build_dir=build_dir, cmake_args=cmake_args
                )

        # Remove all the unneeded files. We don't use the embedded mode as it doesn't
        # generate shared objects.
        rmdirs = ["include", "sbin", "share"]
        if platform.system() != "Windows":
            rmdirs.append("bin")

        for dirname in rmdirs:
            path = os.path.join(lib_dir, dirname)
            if os.path.exists(path):
                shutil.rmtree(path)

        path = os.path.join(lib_dir, "lib", "pkgconfig")
        if os.path.exists(path):
            shutil.rmtree(path)

        # Handle symlinks
        libdir_name = "bin" if platform.system() == "Windows" else "lib"
        for dirpath, dirnames, filenames in os.walk(os.path.join(lib_dir, libdir_name)):
            for f in filenames:
                path = os.path.join(dirpath, f)
                if os.path.islink(path):
                    realpath = os.path.realpath(path)
                    os.remove(path)
                    shutil.copyfile(realpath, path, follow_symlinks=False)

        # Remove remaining files. Defined as a second scan to avoid deleting the real
        # library.
        for dirpath, dirnames, filenames in os.walk(os.path.join(lib_dir, libdir_name)):
            for f in filenames:
                path = os.path.join(dirpath, f)
                if not path.endswith(".so") and not path.endswith(".dll"):
                    os.remove(path)

####################
Building from Source
####################

At the moment, installing pyhwloc **requires** building from source as we haven't made any
release yet.

.. contents::
    :backlinks: none
    :local:

Requirements
============

We only support the latest (> 2.12) hwloc. In addition to the basic hwloc, we have
integration with CUDA-related hwloc features and hence, the CTK is required.

Building PyHwloc from Source
============================

There are two ways to create and distribute a binary wheel for pyhwloc. The first one uses
the system hwloc and the second one builds hwloc from source and bundles it into the
wheel. The following sections go through them.

Windows
-------

Following are some notes about building pyhwloc and hwloc from source on Windows using
CMake. We don't support the mingw environment for Windows. First, we need to build hwloc
from source:

.. code-block:: powershell

  cd hwloc\contrib\windows-cmake\
  cmake -GNinja -DHWLOC_ENABLE_PLUGINS=ON -DCMAKE_INSTALL_PREFIX="$Env:CONDA_PREFIX" -DCMAKE_BUILD_TYPE=RelWithDebInfo  -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DBUILD_SHARED_LIBS=ON ..
  ninja
  ninja install

Then we can proceed to build pyhwloc. It's necessary to specify the hwloc root for Windows
as CMake can't find its installation.

- Binary wheel

  .. code-block:: powershell

    pip wheel -v . --no-build-isolation --no-deps --wheel-dir dist --config-settings=hwloc-root-dir="$Env:CONDA_PREFIX"

- Editable installation:

  .. code-block:: powershell

    pip install -e . --no-deps --no-build-isolation --config-settings=hwloc-root-dir="$Env:CONDA_PREFIX"

Linux
-----

To use a pre-built hwloc in the system or a virtual environment (conda):

- Create a conda environment that's similar to the CI build.
- Build hwloc from source with its autotools-based build, install it into the conda
  environment (``CONDA_PREFIX``). We have example scripts used in the CI. Then we can
  proceed to create the pyhwloc wheel:

  + Binary wheel

    .. code-block:: sh

      pip wheel -v . -w dist/ --no-build-isolation

  + Use editable build:

    .. code-block:: sh

      pip install -e . --no-build-isolation

  + Source Wheel

    .. code-block:: sh

      python -m build --sdist


Fat Wheel
---------

In addition to reusing the system hwloc installation, pyhwloc can fetch and build hwloc
from source and bundle it into the wheel automatically:

.. code-block:: sh

  pip wheel -v . --config-settings=fetch-hwloc=True --wheel-dir dist/

The bundling approach is mainly for the PyPI package. We don't recommend the PyPI package
for complex use cases aside from exploratory usage, since bundling a custom hwloc might
create symbol conflicts between different versions of hwloc in the environment.

A complete list of options available for the ``--config-settings=``:

- ``build-dir=/path/to/build/dir`` for specifying a build dir.
- ``hwloc-src-dir=/path/to/hwloc-src`` for using a local checkout of hwloc. This assumes
  the src directory is the git repo, which is not the same as the release tarball.
- ``hwloc-root-dir=/path/to/hwloc`` to specify the path of an existing hwloc installation.
- ``fetch-hwloc=True`` to build the fat wheel.

The binary wheel uses plugins by default. Due to the plugins support, all symbols from
hwloc are loaded into the linker's public name space using
:py:data:`ctypes.RTLD_GLOBAL`. For the Windows build, please make sure the CUDA runtime
and driver libraries are in the ``PATH`` when you import pyhwloc.

Building the Document
=====================

We have a docker file in the project for creating the environment with the right doxygen
version. Following are notes for how to do it manually.

We use the ``breathe`` project to generate sphinx doc for low-level API from the C doxygen
document. This requires:

- Set the ``HWLOC_DOXYGEN_GENERATE_XML=YES`` environment variable when running doxygen
  with hwloc:

.. code-block:: sh

  cd hwloc/doc
  HWLOC_DOXYGEN_GENERATE_XML=YES doxygen ./doxygen.cfg

- One must run the hwloc `configure` script under the project root with the
  ``--enable-doxygen`` option since the ``doxygen-config.cfg`` file is generated under the
  build root.

- You can inform the pyhwloc sphinx build about the XML path via the ``PYHWLOC_XML_PATH``
  environment variable:

.. code-block:: sh

  cd pyhwloc/docs
  PYHWLOC_XML_PATH=/path/hwloc/doc/doxygen-doc/xml make html

Another issue with doxygen files is how to obtain a clang-assisted doxygen build. The
build-time dependencies (aside from the standard C++ toolchain) for doxygen on Ubuntu
24.04:

- flex
- bison
- xml2
- libclang-19-dev

I have also created an `issue
<https://github.com/conda-forge/doxygen-feedstock/issues/57>`__ for the doxygen feedstock
to ask for clang support. In the meanwhile, see the CI scripts for conda dependencies.

Running Tests
=============

We use ``pytest`` for testing the `pyhwloc` package. The following snippet uses
`pytest-cov` as well. We use the cov package to track the coverage of hwloc features
during early development.

.. code-block:: sh

  pytest ./pyhwloc/tests/ --cov=pyhwloc --cov-report=html

The container image used for GitHub action is built from the `dev/Dockerfile.cpu`:

.. code-block:: sh

  docker build --progress=plain -f ./Dockerfile.cpu . -t pyhwloc:latest

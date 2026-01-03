###############
Developer Notes
###############

Symbol Conflicts
================

The hwloc is loaded into the public linker name space to support hwloc plugins. This might
have unintended consequences.

Update hwloc
============

Update the commit hash in ``dev/hwloc_version``.

Design Decisions
================

Some design decisions were made in the initial development phase. For instance, whether
something should be a Python attribute or a Python method. My choice at the time was
simple, if it's part of a C struct, it's an attribute, otherwise, it's a function. If both
are possible, like the ``cpuset`` and the ``pci_id``, we use property. This way, we can
keep it simple and allow future extension for parameters. It's ok, Python stdlib does not
use property very often, let's move on.

Hwloc has lots of setters and getters, some Python users might frown upon this design
pattern, but we decided keep it instead. Most of these setters and getters have
parameters. We could have wrapped them into properties like:

.. code-block:: python

  topology.membind[proc_id] = Membind(policy, flags)

It might be more ergonomic this way, but also feels like an un-intuitive way to writing
code. In addition, the setter and getters don't have exact match. For instance, setting
the ``DEFAULT`` policy with the membind setter might get you a ``FIRST_TOUCH`` policy in
the getter.

For interpolation modules, hwloc supports getting the CPU affinity of GPUs with functions
like ``nvml_get_device_cpuset``. We rename the function in the high-level interface as
``get_affinity`` to avoid confusion.

GitHub CI
=========

PyHwloc's GitHub action tests use container images cached in ``ghcr.io``. Please refer to
the `GitHub document <https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry>`__ for an in-depth explanation of how it works.

To create the initial GitHub package for PyHwloc:

- Create a personal access token (classic) in the GitHub `developer settings <https://github.com/settings/tokens>`__, with write access (`write:packages`) to the GitHub package.
- Log in with docker.
- Build the container image as described in the building from source document, use the tag ``ghcr.io/open-mpi/pyhwloc:latest``.
- Push the image and find the package in https://github.com/orgs/open-mpi/packages

Currently, the image is private. To use the image for GitHub action:

- Create a read-only PAT (classic, `read:packages`).
- Store it as project secret in the project's settings tab: `Settings -> Secrets and Variables -> Actions`.
- Use the `secrets.GITHUB_TOKEN` to access it in a workflow.
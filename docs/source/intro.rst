#####################
Getting Started Guide
#####################

.. contents::
    :backlinks: none
    :local:

Overview
========

``PyHwloc`` exposes a Python interface to the Hardware Locality (hwloc) library, providing
an easier and more interactive way to discover and control your system's hardware
topology. For a comprehensive introduction to hardware topology concepts and background
information, please refer to the official `hwloc documentation
<https://www.open-mpi.org/projects/hwloc/>`__. This document primarily concerns the usage
of the Python interface.

**Two-Tier Architecture**

PyHwloc is designed with two layers:

1. **High-Level Interface** (Recommended): Provides Pythonic classes and methods that are
   easy to use and follow Python conventions, but has limited feature set at the moment.
2. **Low-Level Interface**: Direct mapping of the C API through :py:mod:`ctypes` for
   advanced use cases when high-level features are insufficient.

Most users should start with the high-level interface and only use the low-level API when
specific functionality is missing. Two interfaces can interpolate through the use of the
``native_handle`` property.

Quick Start Example
===================

Here's a simple example to get started with ``pyhwloc``:

.. code-block:: python

    from pyhwloc import from_this_system

    # Create and load system topology
    with from_this_system() as topo:
        # Get basic system information
        n_cores = topo.n_cores()
        n_numa = topo.n_numa_nodes()

        print(f"System has {n_cores} CPU cores")
        print(f"System has {n_numa} NUMA nodes")

        # Get the current CPU binding
        cpuset = topo.get_cpubind()
        print(f"Current CPU binding: {cpuset}")

We have some more examples in the :doc:`/examples/index`.


Tips and Tricks
===============

Documentation
-------------

We reuse the C document for most of the functions, which might look confusing if you are
not already familiar with hwloc. On the other hand, the package is fully typed. Please use
the type hints as part of the document.

The Topology Class and the Object Class
---------------------------------------

The hwloc API is built upon the :py:class:`~pyhwloc.topology.Topology`, through which one
can obtain devices represented by the :py:class:`~pyhwloc.hwobject.Object` and other
attributes. For interpolation with CUDA libraries, the :py:class:`~pyhwloc.nvml.Device`
can be converted into a :py:class:`~pyhwloc.hwobject.Object` through the
topology. Following is a snippet for walking the topology with object nodes:

.. code-block:: python

    import pyhwloc

    with pyhwloc.Topology() as topo:
        for node in topo.iter_numa_nodes():
            print(f"NUMA Node {node.logical_index}: {node}")
            print(f"  Memory: {node.total_memory // (1024 * 1024)} MB")

The :py:class:`~pyhwloc.hwobject.Object` represents a specific software or hardware device
in the device tree. You can get its attributes using specific getters like
:py:class:`~pyhwloc.hwobject.Object.arity`.

We have some special categories of objects, including
:py:class:`~pyhwloc.hwobject.NumaNode`, :py:class:`~pyhwloc.hwobject.OsDevice` and
friends. These object types have their own attributes, like the PCI bus ID of the
:py:class:`~pyhwloc.hwobject.PciDevice`. You can check whether an object is an `OsDevice`
by using the ``isinstance``, or the predicate
:py:meth:`~pyhwloc.hwobject.Object.is_os_device`. Iteration methods like the
`iter_numa_nodes` shown above can return object types with the correct type
annotation. Other methods return the generic `Object` type hint, but the underlying type
is still valid (can be checked with ``isinstance``). To put it concretely:

- Use iterator with known type:

.. code-block:: python

    import pyhwloc
    from pyhwloc.hwobject import NumaNode

    with pyhwloc.from_this_system() as topo:
        for node in topo.iter_numa_nodes():
            assert isinstance(node, NumaNode)
            # Local memory is specific to the NumaNode object type.
            print(f"Local memory: {node.local_memory // (1024 * 1024)} MB")

- Use runtime-defined object type:

.. code-block:: python

    import pyhwloc
    from pyhwloc.hwobject import NumaNode, Object

    with pyhwloc.from_this_system() as topo:
        # We don't know what the child is.
        for child in topo.iter_all_breadth_first():
            if child.is_numa_node():
                # The type is always the most specialized type.
                assert isinstance(child, NumaNode)
                # NumaNode is a sub-class of the Object
                assert isinstance(child, Object)


Working with Enum Flags
-----------------------

PyHwloc uses enums extensively for options and flags, following hwloc's C API design. We
provide some syntax sugar to work with these flags in Python.

**Simple Enums**

For basic enum values, you can work with them like standard Python enums:

.. code-block:: python

    from pyhwloc.topology import MemBindPolicy

    # Use enum values directly (integer 2)
    policy = MemBindPolicy.BIND

    # Get human-readable name
    policy_name = MemBindPolicy(policy).name
    print(f"Policy: {policy_name}")

**Composite Flags**

Some flags can be combined using bitwise OR operations. ``pyhwloc`` provides convenient
ways to work with these:

.. code-block:: python

    from pyhwloc.topology import MemBindFlags
    from pyhwloc import Topology

    with Topology.from_this_system() as topo:
        # Method 1: Pass a list of flags (recommended)
        topo.set_membind(
            target_set,
            MemBindPolicy.BIND,
            [MemBindFlags.STRICT, MemBindFlags.THREAD],
        )

        # Method 2: Use bitwise OR manually
        combined_flags = MemBindFlags.STRICT | MemBindFlags.THREAD
        topo.set_membind(
            target_set,
            MemBindPolicy.BIND,
            combined_flags,
        )

Please note that you can't create an instance of ``MemBindFlags`` with the ``combined``
here. The composite value is not a valid Python enum. We are using integer values after
the composition.

**Testing Flag Membership**

To check if a specific flag is present in a composite flag value:

.. code-block:: python

    # Check if a flag is set
    is_strict = bool(flags & MemBindFlags.STRICT)


Using the Bitmap
----------------

The :py:class:`~pyhwloc.bitmap.Bitmap` is a core data structure used by hwloc. One can
convert the bitmap into a Python set using the
:py:meth:`~pyhwloc.bitmap.Bitmap.to_sched_set` for interpolation with the Python
``os.sched_`` module. Similarly, one can construct a bitmap from an integer set:

.. code-block::

   import os

   from pyhwloc.bitmap import Bitmap

   affinity = os.sched_getaffinity(0)
   cpuset = Bitmap.from_sched_set(affinity)
   print(cpuset)

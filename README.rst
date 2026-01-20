###################################################################
Python Interface for the Portable Hardware Locality (hwloc) Library
###################################################################

- `Documentation <https://pyhwloc.readthedocs.io/>`__
- `Official site <https://www.open-mpi.org/projects/hwloc/>`__ of the hwloc library.


Quick Start Example
===================

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


Supported Platforms
===================

- Linux distributions, tested with latest Ubuntu LTS.
- Latest Windows.
# Copyright (c) 2025, NVIDIA CORPORATION.
# SPDX-License-Identifier: BSD-3-Clause
"""
High-level API Example
======================

This example demonstrates the high-level Object interface that provides a more Pythonic
way to work with hwloc objects compared to the low level one.

"""

import pyhwloc


def main() -> int:
    # Create and load topology using context manager for automatic cleanup
    with pyhwloc.from_this_system() as topo:
        print(f"Topology depth: {topo.depth}")

        # Print basic system information
        print(f"""
=== System Overview ===
CPUs: {topo.n_cpus()}
Cores: {topo.n_cores()}
NUMA nodes: {topo.n_numa_nodes()}
Packages: {topo.n_packages()}
""")

        # Iterate through all objects by depth
        print("=== Objects by Depth ===")
        for depth in range(topo.depth):
            print(f"Depth {depth}:")
            for obj in topo.iter_objs_by_depth(depth):
                print(f"  {obj}")
            print()

        # Work with specific object types
        print("=== CPU Information ===")
        for cpu in topo.iter_cpus():
            print(f"CPU {cpu.logical_index}: {cpu}")

        print("=== Core Information ===")
        for core in topo.iter_cores():
            print(f"Core {core.logical_index}: {core}")
            # Print children (PUs)
            print("  PUs:")
            for pu in core.iter_children():
                print(f"    {pu}")

        print("=== NUMA Node Information ===")
        for node in topo.iter_numa_nodes():
            print(f"NUMA Node {node.logical_index}: {node}")
            print(f"  Memory: {node.total_memory // (1024 * 1024)} MB")
            # Local memory is specific to the NumaNode object type.
            print(f"  Local memory: {node.local_memory // (1024 * 1024)} MB")

        # Demonstrate object navigation
        print()
        print("=== Object Navigation ===")
        # Get first CPU and navigate the topology
        first_cpu = next(topo.iter_cpus(), None)
        if first_cpu:
            print(f"First CPU: {first_cpu}")

            # Walk up the hierarchy
            current = first_cpu
            while current.parent:
                current = current.parent
                print(f"Parent: {current}")

            print()
            # Explore first core's children
            first_core = next(topo.iter_cores(), None)
            if first_core:
                print(f"First core: {first_core}")
                print("Children:")
                for child in first_core.iter_children():
                    print(f"  {child}")

                print("Siblings:")
                for sibling in first_core.iter_siblings():
                    print(f"  {sibling}")

        # Object comparison and attributes
        print()
        print("=== Object Attributes ===")
        root = topo.get_obj_by_depth(0, 0)  # Root object
        assert root is not None
        print(f"Root object: {root}")
        print(f"Type: {root.type}")
        print(f"Name: {root.name}")
        print(f"Subtype: {root.subtype}")
        print(f"OS Index: {root.os_index}")
        print(f"Depth: {root.depth}")
        print(f"Logical Index: {root.logical_index}")
        print(f"Arity: {root.arity}")
        print(f"Symmetric Subtree: {root.symmetric_subtree}")

    return 0


if __name__ == "__main__":
    main()

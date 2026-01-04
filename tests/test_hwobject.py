# Copyright (c) 2025, NVIDIA CORPORATION.
# SPDX-License-Identifier: BSD-3-Clause
from __future__ import annotations

import pickle

import pytest

from pyhwloc.hwloc.lib import _IS_V3
from pyhwloc.hwobject import Object, ObjType
from pyhwloc.topology import Topology


def test_get_root_object() -> None:
    with Topology.from_synthetic("node:2 core:2 pu:2") as topo:
        # Get root object (should be at depth 0, index 0)
        root = topo.get_obj_by_depth(0, 0)
        assert root == topo.get_root_obj()
        assert root is not None
        # Root should be at depth 0
        assert root.depth == 0
        # Root should have logical index 0
        assert root.logical_index == 0
        # Root should be a machine type
        assert root.type == ObjType.MACHINE
        assert root.parent is None
        # Root should have children (the NUMA nodes)
        assert root.arity > 0
        assert root.first_child is not None


def test_invalid_topo() -> None:
    with Topology.from_synthetic("node:2 core:2 pu:2") as topo:
        root = topo.get_obj_by_depth(0, 0)
        assert root is not None
        assert root.type is not None

    # After context exits, accessing the object should raise an error
    with pytest.raises(RuntimeError, match="Topology is invalid"):
        _ = root.native_handle

    with pytest.raises(RuntimeError, match="Topology is invalid"):
        _ = root.type


def test_object_properties() -> None:
    with Topology.from_synthetic("node:2 core:2 pu:4") as topo:
        # Get a CPU object to test properties
        cpu = next(topo.iter_cpus(), None)
        assert cpu is not None

        # Test basic properties
        assert isinstance(cpu.type, ObjType)
        assert cpu.type == ObjType.PU
        assert cpu.depth >= 0
        assert cpu.logical_index >= 0
        assert cpu.sibling_rank >= 0
        assert cpu.arity >= 0
        assert cpu.memory_arity >= 0
        assert cpu.io_arity >= 0
        assert cpu.misc_arity >= 0

        # Test optional properties
        assert cpu.subtype is None or isinstance(cpu.subtype, str)
        assert cpu.name is None or isinstance(cpu.name, str)
        assert cpu.total_memory >= 0

        # Test boolean properties
        assert isinstance(cpu.symmetric_subtree, bool)

        # Test bitmap properties
        assert cpu.cpuset is not None
        assert cpu.complete_cpuset is not None

        # Test navigation properties
        assert cpu.parent is not None  # CPU should have a parent (core)
        assert isinstance(cpu.parent, Object)


def test_object_navigation() -> None:
    with Topology.from_synthetic("node:2 core:2 pu:2") as topo:
        root = topo.get_obj_by_depth(0, 0)
        assert root is not None

        # Test children iteration
        children = list(root.iter_children())
        assert len(children) == root.arity
        assert len(children) > 0

        for c in root.children:
            assert c.is_normal()
        assert root.children == children

        # Test sibling iteration
        if len(children) > 1:
            first_child = children[0]
            siblings = list(first_child.iter_siblings())
            assert len(siblings) >= 2  # At least the child itself and one sibling
            assert first_child in siblings

        # Test parent-child relationships
        for child in children:
            assert child.parent == root

        # Test next/prev sibling relationships
        if len(children) >= 2:
            first = children[0]
            second = children[1]
            assert first.next_sibling == second
            assert second.prev_sibling == first


def test_object_string_representation() -> None:
    with Topology.from_synthetic("node:2 core:2 pu:2") as topo:
        # Test root object
        root = topo.get_obj_by_depth(0, 0)
        assert root is not None

        # Test __str__ method
        str_repr = str(root)
        assert "MACHINE" in str_repr
        assert "#0" in str_repr  # Should show logical index

        # Test __repr__ method
        repr_str = repr(root)
        assert "Object(" in repr_str
        assert "type=" in repr_str
        assert "logical_index=" in repr_str
        assert "depth=" in repr_str

        # Test CPU object representation
        cpu = next(topo.iter_cpus(), None)
        if cpu is not None:
            cpu_str = str(cpu)
            assert "PU" in cpu_str
            assert f"#{cpu.logical_index}" in cpu_str


def test_object_equality_and_hashing() -> None:
    with Topology.from_synthetic("node:2 core:2 pu:2") as topo:
        # Get same object twice
        obj1 = topo.get_obj_by_depth(0, 0)
        obj2 = topo.get_obj_by_depth(0, 0)

        assert obj1 is not None
        assert obj2 is not None

        # Should be equal (same underlying pointer)
        assert obj1 == obj2
        assert hash(obj1) == hash(obj2)

        # Get different objects
        if topo.depth > 1:
            obj3 = topo.get_obj_by_depth(1, 0)
            assert obj3 is not None
            assert obj1 != obj3
            # Hash may or may not be different, but objects should be unequal

        # Test inequality with non-Object
        assert obj1 != "not an object"
        assert obj1 != 42

        with pytest.raises(ValueError, match="cannot be pickled"):
            pickle.dumps(obj1)


def test_query_ancestor() -> None:
    with Topology.from_synthetic("node:2 core:2 pu:2") as topo:
        objs = list(topo.iter_objs_by_depth(topo.depth - 1))
        assert len(objs) == 8
        ancestor = objs[0].common_ancestor_obj(objs[1])
        assert ancestor.is_normal()
        assert ancestor.type == ObjType.CORE
        assert objs[0].is_in_subtree(ancestor)
        assert objs[1].is_in_subtree(ancestor)


def test_info() -> None:
    with Topology.from_synthetic("node:2 core:2 pu:2") as topo:
        obj = topo.get_root_obj()
        obj.add_info("Foo0", "Bar0")
        obj.add_info("Foo1", "Bar1")
        if _IS_V3:
            info = obj.info
            assert info == {"Foo0": "Bar0", "Foo1": "Bar1"}

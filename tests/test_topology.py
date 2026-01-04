# Copyright (c) 2025-2026, NVIDIA CORPORATION.
# SPDX-License-Identifier: BSD-3-Clause
from __future__ import annotations

import copy
import os
import pickle
import platform

import pytest

from pyhwloc.bitmap import Bitmap
from pyhwloc.hwloc.lib import _IS_V3, normpath
from pyhwloc.hwobject import Bridge, ObjType, OsDevice, PciDevice
from pyhwloc.topology import (
    AllowFlags,
    ExportXmlFlags,
    RestrictFlags,
    Topology,
    TopologyFlags,
    TypeFilter,
)


def test_context_manager_current_system() -> None:
    with Topology() as topo:
        # Verify topology is loaded and accessible
        assert topo.is_loaded
        assert isinstance(topo.depth, int)
        assert topo.depth > 0
        assert topo.is_this_system()
        if _IS_V3:
            assert "hwlocVersion" in topo.info

    # After context manager exits, topology should be destroyed
    assert not topo.is_loaded
    with pytest.raises(RuntimeError):
        _ = topo.depth

    with pytest.raises(RuntimeError, match="not loaded"):
        topo = Topology.from_this_system()
        topo.depth

    topo = Topology()
    topo.destroy()  # Make it unloaded

    # Method should raise RuntimeError
    with pytest.raises(RuntimeError, match="Topology has been destroyed"):
        topo.get_nbobjs_by_type(ObjType.PU)

    # Properties should also raise RuntimeError
    with pytest.raises(RuntimeError, match="Topology has been destroyed"):
        _ = topo.n_cpus()

    with Topology.from_this_system().set_components("no_os") as topo:
        assert topo.is_loaded


def test_direct_usage_current_system() -> None:
    topo = Topology()
    try:
        # Verify topology is loaded and accessible
        assert topo.is_loaded
        assert isinstance(topo.depth, int)
        assert topo.depth > 0
        assert topo.is_this_system()

    finally:
        topo.destroy()

    # After destroy(), topology should not be accessible
    assert not topo.is_loaded
    with pytest.raises(RuntimeError):
        _ = topo.depth


def test_context_manager_synthetic() -> None:
    desc = "node:2 core:2 pu:2"

    with Topology.from_synthetic(desc) as topo:
        # Verify synthetic topology is loaded
        assert topo.is_loaded
        assert isinstance(topo.depth, int)
        assert topo.depth > 0
        # Synthetic topology should not be "this system"
        assert not topo.is_this_system()

    # After context manager exits, topology should be destroyed
    assert not topo.is_loaded

    desc = "node:2 core:2 foo:2"
    with pytest.raises(ValueError, match="Invalid argument"):
        with Topology.from_synthetic(desc) as topo:
            pass


def test_direct_usage_synthetic() -> None:
    synthetic_desc = "node:2 core:2 pu:2"

    topo = Topology.from_synthetic(synthetic_desc).load()
    try:
        # Verify synthetic topology is loaded
        assert topo.is_loaded
        assert isinstance(topo.depth, int)
        assert topo.depth > 0
        # Synthetic topology should not be "this system"
        assert not topo.is_this_system()

    finally:
        topo.destroy()

    # After destroy(), topology should not be accessible
    assert not topo.is_loaded


def test_destroy_safety() -> None:
    # Test that calling destroy() multiple times is safe.
    topo = Topology()
    # First destroy should work
    topo.destroy()
    assert not topo.is_loaded
    # Second destroy should be safe (no exception)
    topo.destroy()
    assert not topo.is_loaded

    topo_ref = None
    try:
        with Topology() as topo:
            topo_ref = topo
            assert topo.is_loaded
            # Simulate an exception in the context
            raise ValueError("Test exception")
    except ValueError:
        pass  # Expected exception

    # Topology should still be cleaned up after exception
    assert topo_ref is not None
    assert not topo_ref.is_loaded

    # Test access after destroy
    topo = Topology()
    topo.destroy()

    # All property access should fail after destroy
    with pytest.raises(RuntimeError):
        _ = topo.native_handle
    with pytest.raises(RuntimeError):
        _ = topo.depth

    # But these should still work
    assert not topo.is_loaded


def test_copy_export() -> None:
    desc = "node:2 core:2 pu:2"
    try:
        topo = Topology.from_synthetic(desc).load()
        cp = copy.copy(topo)
        dcp = copy.deepcopy(topo)
        assert (
            cp.export_synthetic(0)
            == topo.export_synthetic(0)
            == dcp.export_synthetic(0)
        )
        assert (
            cp.export_xml_buffer(0)
            == topo.export_xml_buffer(0)
            == dcp.export_xml_buffer(0)
        )
        assert len(cp.export_xml_buffer(ExportXmlFlags.V2)) > 2
    finally:
        topo.destroy()
        cp.destroy()
        dcp.destroy()


def run_pickling(original: Topology) -> None:
    restored = None
    try:
        # Pickle the topology
        pickled_data = pickle.dumps(original)
        restored = pickle.loads(pickled_data)
        # Verify the restored topology has same properties
        assert restored.is_loaded
        assert restored.depth == original.depth

        # Verify topologies have same structure by comparing exports
        assert restored.export_synthetic(0) == original.export_synthetic(0)
    finally:
        if restored is not None:
            restored.destroy()


def test_pickle_current_system() -> None:
    original = Topology()
    try:
        run_pickling(original)
    finally:
        original.destroy()


def test_pickle_foreign() -> None:
    desc = "node:2 core:2 pu:2"
    original = Topology.from_synthetic(desc).load()
    try:
        run_pickling(original)
    finally:
        original.destroy()

    with Topology.from_synthetic(desc) as topo:
        try:
            run_pickling(topo)
        finally:
            topo.destroy()


def test_pickle_unloaded_topology() -> None:
    topo = Topology()
    topo.destroy()  # Make it unloaded

    # Should raise RuntimeError when trying to pickle unloaded topology
    with pytest.raises(RuntimeError, match="destroyed"):
        pickle.dumps(topo)


def test_get_support() -> None:
    with Topology() as topo:
        sup = topo.get_support()
        sup.membind.bind_membind


def test_get_nbobjs_by_type() -> None:
    with Topology.from_synthetic("node:2 core:2 pu:2") as topo:
        # Should have exactly:
        # - 1 machine
        # - 2 NUMA nodes
        # - 4 cores (2 nodes * 2 cores each)
        # - 8 PUs (2 nodes * 2 cores * 2 PUs each)

        # Test direct method calls
        assert topo.get_nbobjs_by_type(ObjType.MACHINE) == 1
        assert topo.get_nbobjs_by_type(ObjType.NUMANODE) == 2
        assert topo.get_nbobjs_by_type(ObjType.CORE) == 4
        assert topo.get_nbobjs_by_type(ObjType.PU) == 8

        # Test convenience properties
        assert topo.n_cpus() == 8
        assert topo.n_cores() == 4
        assert topo.n_numa_nodes() == 2
        assert topo.n_packages() >= 0
        # OS devices and PCI devices should be 0 in synthetic topology
        assert topo.n_os_devices() == 0
        assert topo.n_pci_devices() == 0


def test_get_nbobjs_by_type_with_filter() -> None:
    # Create topology with I/O filter that removes all I/O objects
    with Topology.from_this_system().set_io_types_filter(
        type_filter=TypeFilter.KEEP_NONE
    ) as topo:
        # I/O objects should be filtered out
        assert topo.n_os_devices() == 0
        assert topo.n_pci_devices() == 0

        # Non-I/O objects should be unaffected
        assert topo.n_cpus() > 0
        assert topo.n_cores() >= 0

    if platform.system() == "Windows":
        pytest.skip("Skipping OS device test on Windows.")

    with Topology.from_this_system().set_io_types_filter(
        type_filter=TypeFilter.KEEP_IMPORTANT
    ) as topo:
        assert topo.get_nbobjs_by_type(ObjType.OS_DEVICE) > 0

    with Topology.from_this_system().set_all_types_filter(
        TypeFilter.KEEP_IMPORTANT
    ) as topo:
        assert topo.get_nbobjs_by_type(ObjType.OS_DEVICE) > 0


def test_object_iteration() -> None:
    desc = "node:2 core:2 pu:2"

    with Topology.from_synthetic(desc) as topo:
        # Test basic properties
        assert topo.depth > 0
        assert topo.n_cpus() == 8  # 2 nodes * 2 cores * 2 PUs
        assert topo.n_cores() == 4  # 2 nodes * 2 cores
        assert topo.n_numa_nodes() == 2  # 2 nodes

        # Test object counts by depth
        total_objects = 0
        for depth in range(topo.depth):
            count = topo.get_nbobjs_by_depth(depth)
            assert count > 0
            total_objects += count

            # Verify depth type
            obj_type = topo.get_depth_type(depth)
            assert isinstance(obj_type, ObjType)

        # Test object access by depth and index
        root = topo.get_obj_by_depth(0, 0)
        assert root is not None

        # Test object access by type
        machine = topo.get_obj_by_type(ObjType.MACHINE, 0)
        assert machine is not None

        # Test iteration by depth
        depth_objects = []
        for depth in range(topo.depth):
            objects = list(topo.iter_objs_by_depth(depth))
            assert len(objects) == topo.get_nbobjs_by_depth(depth)
            depth_objects.extend(objects)

        # Test iteration by type
        cpu_objects = list(topo.iter_cpus())
        core_objects = list(topo.iter_cores())
        numa_objects = list(topo.iter_numa_nodes())

        assert len(cpu_objects) == topo.n_cpus()
        assert len(core_objects) == topo.n_cores()
        assert len(numa_objects) == topo.n_numa_nodes()

        # Test iteration of all objects
        all_objects = list(topo.iter_all_breadth_first())
        assert len(all_objects) == total_objects
        assert len(all_objects) == len(depth_objects)


def test_find_io_devices() -> None:
    sample_osdev_path = os.path.join(
        os.path.dirname(normpath(__file__)), "sample_osdev.xml"
    )
    with Topology.from_xml_file(sample_osdev_path).set_io_types_filter(
        TypeFilter.KEEP_ALL
    ) as topo:
        for pci in topo.iter_pci_devices():
            assert pci.pci_id.domain == pci.pci_id.dev == 0
            assert pci.type == ObjType.PCI_DEVICE
            assert isinstance(pci, PciDevice)
        for bridge in topo.iter_bridges():
            assert bridge.type == ObjType.BRIDGE
            assert isinstance(bridge, Bridge)
        for osdev in topo.iter_os_devices():
            assert isinstance(osdev, OsDevice)
            assert osdev.type == ObjType.OS_DEVICE


def test_helpers() -> None:
    desc = "node:2 core:2 pu:2"

    with Topology.from_synthetic(desc) as topo:
        assert topo.cpuset.weight() == 8
        assert topo.allowed_cpuset.weight() == 8
        assert topo.allowed_nodeset.weight() == 2

        obj = topo.get_numanode_obj_by_os_index(0)
        assert obj is not None
        assert obj.is_numa_node()

        obj = topo.get_pu_obj_by_os_index(0)
        assert obj is not None
        assert obj.is_normal()


def test_topology_restrict() -> None:
    desc = "node:2 core:2 pu:2"

    with Topology.from_synthetic(desc) as topo:
        initial_cpuset = topo.cpuset
        assert initial_cpuset.weight() == 8

        nodeset = Bitmap()
        nodeset.set(0)
        topo.restrict(nodeset, RestrictFlags.BYNODESET)
        topo.refresh()

        assert topo.cpuset.weight() == 8
        assert topo.allowed_nodeset.weight() == 1
        assert topo.get_nbobjs_by_type(ObjType.NUMANODE) == 1


def test_topology_allow() -> None:
    desc = "node:2 core:2 pu:2"

    with Topology.from_synthetic(desc).set_flags(
        TopologyFlags.INCLUDE_DISALLOWED
    ) as topo:
        allowed_cpuset = topo.allowed_cpuset
        assert allowed_cpuset.weight() == 8

        cpuset = Bitmap()
        cpuset.set(0)

        with pytest.raises(ValueError):
            topo.allow(cpuset, None, AllowFlags.ALL)

        topo.allow(cpuset, None, AllowFlags.CUSTOM)
        topo.refresh()

        assert topo.allowed_cpuset.weight() == 1
        assert topo.allowed_nodeset.weight() == 2

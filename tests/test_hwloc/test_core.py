# Copyright (c) 2025-2026, NVIDIA CORPORATION.
# SPDX-License-Identifier: BSD-3-Clause
from __future__ import annotations

import ctypes

import pytest

from pyhwloc.hwloc.bitmap import (
    bitmap_alloc,
    bitmap_copy,
    bitmap_first,
    bitmap_free,
    bitmap_isequal,
    bitmap_isset,
    bitmap_iszero,
    bitmap_set,
    bitmap_weight,
)
from pyhwloc.hwloc.core import (
    ExportSyntheticFlags,
    ExportXmlFlags,
    Info,
    Infos,
    ObjAttr,
    ObjType,
    TopologyComponentsFlag,
    TopologyFlags,
    TypeFilter,
    bridge_covers_pcibus,
    compare_types,
    cpukinds_get_by_cpuset,
    cpukinds_get_info,
    cpukinds_get_nr,
    cpukinds_register,
    cpuset_from_nodeset,
    cpuset_to_nodeset,
    get_ancestor_obj_by_depth,
    get_ancestor_obj_by_type,
    get_api_version,
    get_cache_type_depth,
    get_child_covering_cpuset,
    get_common_ancestor_obj,
    get_depth_type,
    get_first_largest_obj_inside_cpuset,
    get_memory_parents_depth,
    get_nbobjs_by_depth,
    get_next_bridge,
    get_next_child,
    get_obj_by_depth,
    get_obj_covering_cpuset,
    get_root_obj,
    get_type_depth,
    get_type_or_above_depth,
    get_type_or_below_depth,
    hwloc_obj_cache_type_t,
    is_same_obj,
    obj_add_info,
    obj_attr_snprintf,
    obj_get_info_by_name,
    obj_is_in_subtree,
    obj_set_subtype,
    obj_type_is_memory,
    obj_type_is_normal,
    obj_type_snprintf,
    topology_abi_check,
    topology_check,
    topology_destroy,
    topology_dup,
    topology_export_synthetic,
    topology_export_xmlbuffer,
    topology_get_allowed_cpuset,
    topology_get_allowed_nodeset,
    topology_get_complete_cpuset,
    topology_get_complete_nodeset,
    topology_get_depth,
    topology_get_flags,
    topology_get_infos,
    topology_get_topology_cpuset,
    topology_get_topology_nodeset,
    topology_init,
    topology_is_thissystem,
    topology_load,
    topology_restrict,
    topology_set_components,
    topology_set_flags,
    topology_set_io_types_filter,
    topology_set_xmlbuffer,
    topology_t,
    type_sscanf,
    type_sscanf_as_depth,
)
from pyhwloc.hwloc.lib import _IS_V3, HwLocError


def test_get_api_version() -> None:
    major, minor, patch = get_api_version()
    assert isinstance(major, int)
    assert major >= 2


##############
# Object Types
##############


def test_compare_types() -> None:
    # Test equal types
    r = compare_types(ObjType.CORE, ObjType.CORE)
    assert r == 0
    r = compare_types(ObjType.PU, ObjType.PU)
    assert r == 0

    r = compare_types(ObjType.MACHINE, ObjType.CORE)
    assert r != 0
    r = compare_types(ObjType.CORE, ObjType.MACHINE)
    assert r != 0


###################################
# Topology Creation and Destruction
###################################


class Topology:
    def __init__(self, filters: list[TypeFilter] = []) -> None:
        self.hdl = topology_t()
        topology_init(self.hdl)
        if filters:
            for f in filters:
                topology_set_io_types_filter(self.hdl, f)
        topology_load(self.hdl)

    def __del__(self) -> None:
        topology_destroy(self.hdl)


def test_topology_init() -> None:
    hdl = topology_t()
    topology_init(hdl)
    topology_load(hdl)
    topology_check(hdl)
    topology_abi_check(hdl)
    topology_destroy(hdl)


def test_topology_dup() -> None:
    topo = Topology()
    depth_0 = topology_get_depth(topo.hdl)
    new = topology_dup(topo.hdl)
    depth_1 = topology_get_depth(topo.hdl)
    assert depth_0 == depth_1
    topology_destroy(new)


def test_topology_get_depth() -> None:
    topo = Topology()
    depth = topology_get_depth(topo.hdl)
    assert depth >= 0
    for d in range(depth):
        n_objs = get_nbobjs_by_depth(topo.hdl, d)
        assert n_objs >= 0


def test_topology_get_infos() -> None:
    topo = topology_t()
    topology_init(topo)

    topology_set_io_types_filter(topo, TypeFilter.KEEP_IMPORTANT)
    topology_load(topo)

    if not _IS_V3:
        with pytest.raises(NotImplementedError, match="Only valid"):
            infos = topology_get_infos(topo)
        return

    infos = topology_get_infos(topo)

    cnt = infos.contents.count
    assert cnt > 0
    names = [infos.contents.array[i].name for i in range(cnt)]
    assert b"OSName" in names

    topology_destroy(topo)


def test_error() -> None:
    with pytest.raises(HwLocError, match="error:"):
        topo = Topology()
        topology_set_io_types_filter(topo.hdl, TypeFilter.KEEP_IMPORTANT)


#################################
# Object levels, depths and types
#################################


def test_get_type_depth() -> None:
    topo = Topology()

    # Test common object types
    machine_depth = get_type_depth(topo.hdl, ObjType.MACHINE)
    assert machine_depth == 0

    pu_depth = get_type_depth(topo.hdl, ObjType.PU)
    # PU should typically be at the deepest level
    assert pu_depth > 0

    total_depth = topology_get_depth(topo.hdl)
    assert pu_depth < total_depth


def test_get_depth_type() -> None:
    topo = Topology()
    total_depth = topology_get_depth(topo.hdl)

    # Test each depth level
    for depth in range(total_depth):
        obj_type = get_depth_type(topo.hdl, depth)
        assert isinstance(obj_type, ObjType)
        assert obj_type >= 0

        # Roundtrip
        type_depth = get_type_depth(topo.hdl, obj_type)
        if type_depth >= 0:  # Skip special depth values
            assert type_depth == depth


def test_get_nbobjs_by_depth() -> None:
    topo = Topology()
    total_depth = topology_get_depth(topo.hdl)

    # Test each depth level
    for depth in range(total_depth):
        n_objs = get_nbobjs_by_depth(topo.hdl, depth)
        assert n_objs > 0  # Each level should have at least one object

        # Verify we can actually get objects at this depth
        obj = get_obj_by_depth(topo.hdl, depth, 0)
        assert obj is not None
        assert obj.contents.depth == depth

    # Test invalid depth
    invalid_depth = total_depth + 10
    n_objs = get_nbobjs_by_depth(topo.hdl, invalid_depth)
    assert n_objs == 0


def test_get_type_or_above_depth() -> None:
    topo = Topology()

    # Test with common types
    core_depth = get_type_or_above_depth(topo.hdl, ObjType.CORE)
    assert core_depth > 0
    # Should be a valid depth
    total_depth = topology_get_depth(topo.hdl)
    assert core_depth < total_depth

    obj_type = get_depth_type(topo.hdl, core_depth)
    assert obj_type == ObjType.CORE


def test_get_type_or_below_depth() -> None:
    topo = Topology()

    # Test with machine type - should find machine or something below it
    machine_depth = get_type_or_below_depth(topo.hdl, ObjType.MACHINE)
    assert machine_depth >= 0  # Should always find something

    # Test with core type
    core_depth = get_type_or_below_depth(topo.hdl, ObjType.CORE)
    assert core_depth > 0
    total_depth = topology_get_depth(topo.hdl)
    assert core_depth < total_depth

    # The returned depth should contain objects of the requested type or below
    obj_type = get_depth_type(topo.hdl, core_depth)
    assert obj_type == ObjType.CORE


def test_get_memory_parents_depth() -> None:
    topo = Topology()

    mem_depth = get_memory_parents_depth(topo.hdl)
    assert mem_depth >= 0
    total_depth = topology_get_depth(topo.hdl)
    assert mem_depth < total_depth


def test_depth_consistency() -> None:
    topo = Topology()
    total_depth = topology_get_depth(topo.hdl)

    # Test that get_type_depth and get_depth_type are consistent
    for depth in range(total_depth):
        obj_type = get_depth_type(topo.hdl, depth)
        type_depth = get_type_depth(topo.hdl, obj_type)

        # If type_depth is a normal depth (not special value), it should match
        if type_depth >= 0:
            assert type_depth == depth


def test_get_root_obj() -> None:
    topo = Topology()

    # Get the root object
    root_obj = get_root_obj(topo.hdl)
    assert root_obj is not None and root_obj.contents.depth == 0

    # Root object should be of type MACHINE
    assert root_obj.contents.type == ObjType.MACHINE

    buf = ctypes.create_string_buffer(1024)
    length = obj_type_snprintf(buf, 256, root_obj, 1)
    assert buf.value.decode("utf-8") == "Machine" and len("Machine") == length
    obj_attr_snprintf(buf, 1024, root_obj, "\n", 1)
    assert buf.value is not None and len(buf.value.decode("utf-8")) > 2

    # Root object should have no parent
    parent = ctypes.cast(root_obj.contents.parent, ctypes.c_void_p)
    assert parent.value is None

    # Root object should be the same as getting object at depth 0, index 0
    depth_0_obj = get_obj_by_depth(topo.hdl, 0, 0)
    assert depth_0_obj is not None
    assert root_obj.contents.type == depth_0_obj.contents.type
    assert root_obj.contents.depth == depth_0_obj.contents.depth

    # Root should have children (unless it's a very simple topology)
    total_depth = topology_get_depth(topo.hdl)
    if total_depth > 1:
        assert root_obj.contents.arity > 0
        assert root_obj.contents.first_child is not None

        # First child should have root as parent
        first_child = root_obj.contents.first_child
        assert is_same_obj(root_obj, first_child.contents.parent)

    # Root object should have valid cpuset and nodeset
    assert root_obj.contents.cpuset is not None
    assert root_obj.contents.nodeset is not None


######################
# Kinds of object Type
######################


def test_kinds_of_object_type() -> None:
    # Test normal object types
    normal_types = [
        ObjType.MACHINE,
        ObjType.PACKAGE,
    ]

    for obj_type in normal_types:
        result = obj_type_is_normal(obj_type)
        assert result is True

    # Test non-normal object types
    non_normal_types = [
        ObjType.BRIDGE,
        ObjType.PCI_DEVICE,
    ]

    # Verify non-normal types return False
    for obj_type in non_normal_types:
        result = obj_type_is_normal(obj_type)
        assert isinstance(result, bool)
        assert result is False

    # Others
    assert obj_type_is_memory(ObjType.NUMANODE) is True


#############################################################
# Converting between Object Types and Attributes, and Strings
#############################################################


def test_type_sscanf_functions() -> None:
    topo = Topology()

    # Test parsing basic object type strings
    test_cases = ["Machine", "Package", "Core", "PU", "L1Cache", "L2Cache", "L3Cache"]

    for type_str in test_cases:
        # Test type_sscanf without attributes
        obj_type, attr = type_sscanf(type_str)
        assert isinstance(obj_type, ObjType)
        assert attr is not None
        # The depth should be reliable. Other info like size is set to 0 for some reason
        if obj_type == ObjType.L1CACHE:
            assert attr.cache.depth == 1
        if obj_type == ObjType.L2CACHE:
            assert attr.cache.depth == 2
        if obj_type == ObjType.L3CACHE:
            assert attr.cache.depth == 3
        # Test type_sscanf_as_depth
        obj_type_depth, depth = type_sscanf_as_depth(type_str, topo.hdl)
        assert isinstance(obj_type_depth, ObjType)
        assert isinstance(depth, int)

        assert obj_type == obj_type_depth

    # Test invalid string
    with pytest.raises(Exception):
        type_sscanf("FooBar")


def test_hwloc_obj_attr_u_union() -> None:
    # Test creating and accessing the union
    attr_union = ObjAttr()

    # Test cache attributes
    attr_union.cache.size = 32768  # 32KB cache
    attr_union.cache.depth = 1  # L1 cache
    attr_union.cache.linesize = 64  # 64-byte cache lines
    attr_union.cache.associativity = 8  # 8-way associative
    attr_union.cache.type = 0  # hwloc_obj_cache_type_t.UNIFIED

    assert attr_union.cache.size == 32768
    assert attr_union.cache.depth == 1
    assert attr_union.cache.linesize == 64
    assert attr_union.cache.associativity == 8
    assert attr_union.cache.type == 0

    # Test PCI device attributes
    attr_union.pcidev.domain = 0
    attr_union.pcidev.bus = 1
    attr_union.pcidev.dev = 0
    attr_union.pcidev.func = 0
    attr_union.pcidev.vendor_id = 0x10DE  # NVIDIA
    attr_union.pcidev.device_id = 0x1234
    attr_union.pcidev.class_id = 0x0300  # Display controller

    assert attr_union.pcidev.domain == 0
    assert attr_union.pcidev.bus == 1
    assert attr_union.pcidev.dev == 0
    assert attr_union.pcidev.func == 0
    assert attr_union.pcidev.vendor_id == 0x10DE
    assert attr_union.pcidev.device_id == 0x1234
    assert attr_union.pcidev.class_id == 0x0300


def find_numa_depth() -> int:
    topo = Topology()
    for depth in range(10):  # reasonable upper limit
        if get_nbobjs_by_depth(topo.hdl, depth) > 0:
            obj = get_obj_by_depth(topo.hdl, depth, 0)
            if obj and obj.contents.type == ObjType.NUMANODE:
                numa_depth = depth
                break
    return numa_depth


#####################
# Finding I/O objects
#####################


def test_bridge_covers_pcibus() -> None:
    # Create a topology with I/O devices enabled
    topo = Topology([TypeFilter.KEEP_IMPORTANT])

    # Use prev=None to find the first bridge.
    bridge = get_next_bridge(topo.hdl, None)
    if bridge is None:
        pytest.skip("Failed to find bridge.")
    assert bridge
    assert ctypes.cast(bridge, ctypes.c_void_p).value is not None

    # Test with bridge attributes if the bridge has PCI attributes
    assert bridge.contents.attr
    bridge_attr = bridge.contents.attr.contents
    assert bridge_attr.bridge.depth >= 0

    # Test that a bridge covers its own bus range
    # For a valid bridge, it should cover some bus range
    result = bridge_covers_pcibus(bridge, 0, 0)
    assert isinstance(result, int)

    # Test with clearly invalid domain/bus combinations
    result_invalid = bridge_covers_pcibus(bridge, 0xFFFF, 0xFFFF)
    assert isinstance(result_invalid, int)


#############################
# Exporting Topologies to XML
#############################


def test_topology_export_xmlbuffer() -> None:
    topo = Topology()
    result = topology_export_xmlbuffer(topo.hdl, ExportXmlFlags.V2)
    assert """<!DOCTYPE topology SYSTEM "hwloc2.dtd">""" in result


###################################
# Exporting Topologies to Synthetic
###################################


def test_topology_export_synthetic() -> None:
    topo = Topology()
    buf = bytearray(1024)
    c_buf = (ctypes.c_char * len(buf)).from_buffer(buf)

    ExFlags = ExportSyntheticFlags
    flags = ExFlags.NO_EXTENDED_TYPES
    topology_export_synthetic(topo.hdl, c_buf, len(buf), flags)
    result = buf.decode("utf-8")
    # V3 is Package, V2 is Socket
    assert "Package" in result or "Socket" in result


####################
# Kinds of CPU cores
####################


def test_cpukinds_get_info() -> None:
    topo = Topology()

    nr_kinds = cpukinds_get_nr(topo.hdl)
    assert isinstance(nr_kinds, int)
    assert nr_kinds >= 0


@pytest.mark.skipif(condition=not _IS_V3, reason="Not implemented for V2.")
def test_cpukinds_register_and_get_functions() -> None:
    topo = Topology()

    # Get initial number of CPU kinds
    initial_nr_kinds = cpukinds_get_nr(topo.hdl)

    # Create a test cpuset (use first CPU)
    test_cpuset = bitmap_alloc()
    bitmap_set(test_cpuset, 0)  # Set CPU 0

    # Create test info
    test_info = Info()
    test_info.name = b"TestCPUKind"
    test_info.value = b"TestValue"

    infos = Infos()
    infos.array = ctypes.pointer(test_info)
    infos.count = 1

    # Register a new CPU kind
    cpukinds_register(topo.hdl, test_cpuset, 100, infos)

    # Verify the number of kinds increased
    new_nr_kinds = cpukinds_get_nr(topo.hdl)
    assert new_nr_kinds == initial_nr_kinds + 1

    # Test cpukinds_get_by_cpuset
    kind_index = cpukinds_get_by_cpuset(topo.hdl, test_cpuset)
    assert isinstance(kind_index, int)
    assert kind_index >= 0

    # Test cpukinds_get_info
    cpuset, efficiency, ninfos = cpukinds_get_info(topo.hdl, kind_index)
    assert cpuset is not None
    assert isinstance(efficiency, int)
    assert efficiency >= 0 or efficiency == -1
    assert ninfos.contents is not None

    bitmap_free(cpuset)
    bitmap_free(test_cpuset)

    assert any(
        ninfos.contents.array[i].name == b"TestCPUKind"
        for i in range(ninfos.contents.count)
    )
    assert any(
        ninfos.contents.array[i].value == b"TestValue"
        for i in range(ninfos.contents.count)
    )


def test_cpukinds_register_empty_infos() -> None:
    topo = Topology()

    # Get initial number of CPU kinds
    initial_nr_kinds = cpukinds_get_nr(topo.hdl)

    # Create a test cpuset (use CPU 1 if available, otherwise CPU 0)
    test_cpuset = bitmap_alloc()
    bitmap_set(test_cpuset, 1)

    # Register a CPU kind with no infos
    cpukinds_register(topo.hdl, test_cpuset, 50, None)

    # Verify the number of kinds increased
    new_nr_kinds = cpukinds_get_nr(topo.hdl)
    assert new_nr_kinds == initial_nr_kinds + 1

    bitmap_free(test_cpuset)


#######################################
# Consulting and Adding Info Attributes
#######################################


def test_obj_get_info_by_name() -> None:
    topo = Topology()

    # Get the root object
    root_obj = get_root_obj(topo.hdl)
    assert root_obj is not None

    # Test getting existing info (root object typically has OS-related info)
    # Try common info keys that are usually present
    os_name = obj_get_info_by_name(root_obj, "OSName")
    if os_name is not None:
        assert isinstance(os_name, str)
        assert len(os_name) > 0

    # Test getting non-existent info
    non_existent = obj_get_info_by_name(root_obj, "NonExistentKey")
    assert non_existent is None

    # Test with empty string key
    empty_key_result = obj_get_info_by_name(root_obj, "")
    assert empty_key_result is None


def test_obj_add_info() -> None:
    topo = Topology()

    # Get the root object
    root_obj = get_root_obj(topo.hdl)
    assert root_obj is not None

    obj_add_info(root_obj, "TestName", "TestValue")

    value = obj_get_info_by_name(root_obj, "TestName")
    assert value == "TestValue"


def test_obj_set_subtype() -> None:
    topo = Topology()

    # Get the root object
    root_obj = get_root_obj(topo.hdl)
    assert root_obj is not None

    # Test setting a basic subtype
    test_subtype = "TestSubtype"
    obj_set_subtype(topo.hdl, root_obj, test_subtype)

    assert root_obj.contents.subtype is not None
    retrieved_subtype = ctypes.string_at(root_obj.contents.subtype).decode("utf-8")
    assert retrieved_subtype == test_subtype

    # Test setting a different subtype.
    new_subtype = "NewSubtype"
    obj_set_subtype(topo.hdl, root_obj, new_subtype)

    updated_subtype = ctypes.string_at(root_obj.contents.subtype).decode("utf-8")
    assert updated_subtype == new_subtype


##########################
# Looking at Cache Objects
##########################


def test_get_cache_type_depth() -> None:
    topo = Topology()

    # Test getting cache type depth for different cache levels and types

    l1_unified_depth = get_cache_type_depth(topo.hdl, 1, hwloc_obj_cache_type_t.UNIFIED)
    assert l1_unified_depth >= -1

    l1_data_depth = get_cache_type_depth(topo.hdl, 1, hwloc_obj_cache_type_t.DATA)
    assert l1_data_depth > 0

    # Test L1 instruction cache
    l1_inst_depth = get_cache_type_depth(
        topo.hdl, 1, hwloc_obj_cache_type_t.INSTRUCTION
    )
    assert isinstance(l1_inst_depth, int)
    assert l1_inst_depth >= -1


###########################################
# Converting between CPU sets and node sets
###########################################


def test_cpuset_nodeset_conversion() -> None:
    topo = Topology()

    # Allocate bitmaps for testing
    original_cpuset = bitmap_alloc()
    converted_nodeset = bitmap_alloc()
    roundtrip_cpuset = bitmap_alloc()

    # Create a test CPU set (set CPU 0)
    bitmap_set(original_cpuset, 0)

    cpuset_to_nodeset(topo.hdl, original_cpuset, converted_nodeset)
    cpuset_from_nodeset(topo.hdl, roundtrip_cpuset, converted_nodeset)

    bitmap_free(original_cpuset)
    bitmap_free(converted_nodeset)
    bitmap_free(roundtrip_cpuset)


########################################
# CPU and node sets of entire topologies
########################################


def test_topology_get_cpuset() -> None:
    topo = Topology()

    cpuset = topology_get_complete_cpuset(topo.hdl)
    assert cpuset is not None
    assert not bitmap_iszero(cpuset)

    cpuset = topology_get_topology_cpuset(topo.hdl)
    assert cpuset is not None
    assert not bitmap_iszero(cpuset)

    cpuset = topology_get_allowed_cpuset(topo.hdl)
    assert cpuset is not None
    assert not bitmap_iszero(cpuset)


def test_topology_get_nodeset() -> None:
    topo = Topology()
    nodeset = topology_get_complete_nodeset(topo.hdl)
    assert not bitmap_iszero(nodeset)

    nodeset = topology_get_topology_nodeset(topo.hdl)
    assert nodeset is not None
    assert not bitmap_iszero(nodeset)

    nodeset = topology_get_allowed_nodeset(topo.hdl)
    assert nodeset is not None
    assert not bitmap_iszero(nodeset)


###########################################
# Changing the source of topology discovery
###########################################


def test_topology_set_components() -> None:
    # Simple test case from tests/hwloc/hwloc_backends.c
    hdl = topology_t()
    topology_init(hdl)
    topology_set_components(
        hdl,
        TopologyComponentsFlag.BLACKLIST,
        "synthetic",
    )
    topology_load(hdl)
    assert topology_is_thissystem(hdl)
    topology_destroy(hdl)


def test_topology_set_xmlbuffer() -> None:
    topo = Topology()
    assert topology_is_thissystem(topo.hdl)
    buf = topology_export_xmlbuffer(topo.hdl, 0)

    hdl = topology_t()
    topology_init(hdl)
    topology_set_xmlbuffer(hdl, buf)
    topology_load(hdl)
    assert not topology_is_thissystem(hdl)
    topology_destroy(hdl)


############################################
# Topology Detection Configuration and Query
############################################


def test_topology_flags() -> None:
    hdl = topology_t()
    topology_init(hdl)
    topology_set_flags(hdl, TopologyFlags.INCLUDE_DISALLOWED)
    topology_load(hdl)
    flags = topology_get_flags(hdl)
    assert flags == TopologyFlags.INCLUDE_DISALLOWED
    topology_destroy(hdl)


#############################
# Modifying a loaded Topology
#############################


def test_topology_restrict() -> None:
    topo = Topology()

    tmp = topology_get_complete_cpuset(topo.hdl)
    original_cpuset = bitmap_alloc()
    bitmap_copy(original_cpuset, tmp)
    assert not bitmap_iszero(original_cpuset)

    # Create a restricted cpuset with just CPU 0
    restricted_cpuset = bitmap_alloc()
    bitmap_set(restricted_cpuset, 0)

    # Test that topology_restrict doesn't raise an exception
    topology_restrict(topo.hdl, restricted_cpuset, 0)

    # After restriction, the complete cpuset should be different (smaller)
    new_cpuset = topology_get_complete_cpuset(topo.hdl)
    assert not bitmap_iszero(new_cpuset)

    assert bitmap_isset(new_cpuset, 0)
    assert bitmap_weight(new_cpuset) == 1

    # Clean up
    bitmap_free(restricted_cpuset)

    topo = Topology()
    reloaded = topology_get_complete_cpuset(topo.hdl)
    assert bitmap_isequal(reloaded, original_cpuset)
    bitmap_free(original_cpuset)


##################################
# Finding Objects inside a CPU set
##################################


def test_get_first_largest_obj_inside_cpuset() -> None:
    topo = Topology()

    complete_cpuset = topology_get_complete_cpuset(topo.hdl)
    assert not bitmap_iszero(complete_cpuset)

    largest_obj = get_first_largest_obj_inside_cpuset(topo.hdl, complete_cpuset)
    assert largest_obj is not None

    # The returned object should have valid properties
    assert largest_obj.contents.type >= 0
    assert largest_obj.contents.cpuset is not None
    assert not bitmap_iszero(largest_obj.contents.cpuset)


###########################################
# Finding Objects covering at least CPU set
###########################################


def test_get_child_covering_cpuset() -> None:
    topo = Topology()

    root_obj = get_root_obj(topo.hdl)
    assert root_obj is not None

    # Get the root's cpuset to use as our test cpuset
    root_cpuset = root_obj.contents.cpuset
    assert not bitmap_iszero(root_cpuset)

    # Test with the full root cpuset - should return a child that covers it
    child_obj = get_child_covering_cpuset(topo.hdl, root_cpuset, root_obj)
    assert child_obj is not None
    assert not bitmap_iszero(child_obj.contents.cpuset)
    assert is_same_obj(root_obj, child_obj.contents.parent)

    # Test with a subset cpuset - create a bitmap with just the first CPU
    assert bitmap_weight(root_cpuset) > 0
    # Find first set bit and create a single-CPU cpuset
    test_cpuset = bitmap_alloc()
    fst = bitmap_first(root_cpuset)
    bitmap_set(test_cpuset, fst)

    # Get child covering this single CPU
    child_obj = get_child_covering_cpuset(topo.hdl, test_cpuset, root_obj)
    assert child_obj is not None

    bitmap_free(test_cpuset)


def test_get_obj_covering_cpuset() -> None:
    topo = Topology()

    # Get the complete cpuset for the topology
    complete_cpuset = topology_get_complete_cpuset(topo.hdl)
    assert not bitmap_iszero(complete_cpuset)

    # Test with the complete cpuset - should return root object
    covering_obj = get_obj_covering_cpuset(topo.hdl, complete_cpuset)
    assert covering_obj is not None
    assert not bitmap_iszero(covering_obj.contents.cpuset)

    # Test with a single CPU cpuset
    test_cpuset = bitmap_alloc()
    first_cpu = bitmap_first(complete_cpuset)
    bitmap_set(test_cpuset, first_cpu)

    # Get object covering this single CPU
    covering_obj = get_obj_covering_cpuset(topo.hdl, test_cpuset)
    assert covering_obj is not None
    assert bitmap_isset(covering_obj.contents.cpuset, first_cpu)

    bitmap_free(test_cpuset)


#######################################
# Looking at Ancestor and Child Objects
#######################################


def test_get_ancestor_obj_by_depth() -> None:
    topo = Topology()

    # Get a leaf object (processing unit) to test with
    depth = topology_get_depth(topo.hdl)
    assert depth > 1
    leaf_obj = get_obj_by_depth(topo.hdl, depth - 1, 0)
    assert leaf_obj is not None

    # Test getting ancestor at root depth (depth 0)
    root_ancestor = get_ancestor_obj_by_depth(topo.hdl, 0, leaf_obj)
    assert root_ancestor is not None
    assert root_ancestor.contents.depth == 0

    # Test with invalid depth (deeper than the object)
    invalid_ancestor = get_ancestor_obj_by_depth(topo.hdl, depth + 1, leaf_obj)
    assert invalid_ancestor is None


def test_get_ancestor_obj_by_type() -> None:
    topo = Topology()

    # Get a leaf object (processing unit) to test with
    depth = topology_get_depth(topo.hdl)
    assert depth > 1
    leaf_obj = get_obj_by_depth(topo.hdl, depth - 1, 0)
    assert leaf_obj is not None

    # Test getting ancestor of type MACHINE (root)
    machine_ancestor = get_ancestor_obj_by_type(topo.hdl, ObjType.MACHINE, leaf_obj)
    assert machine_ancestor is not None
    assert machine_ancestor.contents.type == ObjType.MACHINE

    # Test with a type that doesn't exist as ancestor
    nonexistent_ancestor = get_ancestor_obj_by_type(topo.hdl, ObjType.MISC, leaf_obj)
    assert nonexistent_ancestor is None


def test_get_common_ancestor_obj() -> None:
    topo = Topology()

    # Get two different objects to find their common ancestor
    depth = topology_get_depth(topo.hdl)
    assert depth > 1

    # Get two leaf objects (processing units)
    obj1 = get_obj_by_depth(topo.hdl, depth - 1, 0)
    assert obj1 is not None

    # Try to get a second object, or use the same one if only one exists
    num_objs = get_nbobjs_by_depth(topo.hdl, depth - 1)
    if num_objs > 1:
        obj2 = get_obj_by_depth(topo.hdl, depth - 1, 1)
        assert obj2 is not None
    else:
        obj2 = obj1

    # Find common ancestor
    common_ancestor = get_common_ancestor_obj(topo.hdl, obj1, obj2)
    assert common_ancestor is not None

    # Common ancestor should be at a depth less than or equal to both objects
    assert common_ancestor.contents.depth <= obj1.contents.depth
    assert common_ancestor.contents.depth <= obj2.contents.depth

    # Test with the same object - should return the object itself
    same_obj_ancestor = get_common_ancestor_obj(topo.hdl, obj1, obj1)
    assert same_obj_ancestor is not None
    assert is_same_obj(same_obj_ancestor, obj1)


def test_get_next_child_is_in_subtree() -> None:
    topo = Topology()

    root_obj = get_root_obj(topo.hdl)
    assert root_obj is not None
    assert root_obj.contents.arity > 0

    depth = topology_get_depth(topo.hdl)
    assert depth > 1
    leaf_obj = get_obj_by_depth(topo.hdl, depth - 1, 0)
    assert leaf_obj is not None

    # The leaf object should be in the subtree of root
    assert obj_is_in_subtree(topo.hdl, leaf_obj, root_obj) is True
    # The root object should be in its own subtree
    assert obj_is_in_subtree(topo.hdl, root_obj, root_obj) is True
    # The root object should NOT be in the subtree of leaf
    assert obj_is_in_subtree(topo.hdl, root_obj, leaf_obj) is False

    first_child = get_next_child(topo.hdl, root_obj, None)
    assert first_child is not None
    assert is_same_obj(first_child.contents.parent, root_obj)

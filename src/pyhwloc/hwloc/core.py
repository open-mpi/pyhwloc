# Copyright (c) 2025-2026, NVIDIA CORPORATION.
# SPDX-License-Identifier: BSD-3-Clause
"""
Core API
========
"""

from __future__ import annotations

import ctypes
import errno
import sys
from enum import IntEnum
from typing import TYPE_CHECKING, Any, Callable

from .bitmap import bitmap_alloc, bitmap_t, const_bitmap_t
from .lib import (
    _IS_V3,
    _LIB,
    HwLocError,
    _cenumdoc,
    _cfndoc,
    _checkc,
    _cstructdoc,
    _cuniondoc,
    _hwloc_error,
    _PrintableStruct,
    _pyhwloc_lib,
)
from .lib import get_api_version as get_api_ver
from .libc import strerror as _strerror

hwloc_uint64_t = ctypes.c_uint64
HWLOC_UNKNOWN_INDEX = ctypes.c_uint(-1).value


#############
# API version
#############

# https://www.open-mpi.org/projects/hwloc/doc/v2.12.2/group__hwlocality__api__version.html


@_cfndoc
def get_api_version() -> tuple[int, int, int]:
    return get_api_ver()


##################################################
# Object Sets (hwloc_cpuset_t and hwloc_nodeset_t)
##################################################

# https://www.open-mpi.org/projects/hwloc/doc/v2.12.1/a00139.php


hwloc_cpuset_t = bitmap_t
hwloc_nodeset_t = bitmap_t

hwloc_const_cpuset_t = const_bitmap_t
hwloc_const_nodeset_t = const_bitmap_t


##############
# Object Types
##############

# https://www.open-mpi.org/projects/hwloc/doc/v2.12.1/a00140.php

if _IS_V3:

    @_cenumdoc("hwloc_obj_type_t")
    class ObjType(IntEnum):
        MACHINE = 0
        PACKAGE = 1
        DIE = 2
        CORE = 3
        PU = 4
        L1CACHE = 5
        L2CACHE = 6
        L3CACHE = 7
        L4CACHE = 8
        L5CACHE = 9
        L1ICACHE = 10
        L2ICACHE = 11
        L3ICACHE = 12
        GROUP = 13
        NUMANODE = 14
        MEMCACHE = 15
        BRIDGE = 16
        PCI_DEVICE = 17
        OS_DEVICE = 18
        MISC = 19
        TYPE_MAX = 20

else:

    @_cenumdoc("hwloc_obj_type_t")
    class ObjType(IntEnum):  # type: ignore[no-redef]
        MACHINE = 0
        PACKAGE = 1
        CORE = 2
        PU = 3
        L1CACHE = 4
        L2CACHE = 5
        L3CACHE = 6
        L4CACHE = 7
        L5CACHE = 8
        L1ICACHE = 9
        L2ICACHE = 10
        L3ICACHE = 11
        GROUP = 12
        NUMANODE = 13
        BRIDGE = 14
        PCI_DEVICE = 15
        OS_DEVICE = 16
        MISC = 17
        MEMCACHE = 18
        DIE = 19
        TYPE_MAX = 20


@_cenumdoc("hwloc_obj_cache_type_e")
class ObjCacheType(IntEnum):
    UNIFIED = 0
    DATA = 1
    INSTRUCTION = 2


# typedef in hwloc.h
hwloc_obj_cache_type_t = ObjCacheType


@_cenumdoc("hwloc_obj_bridge_type_e")
class ObjBridgeType(IntEnum):
    HOST = 0
    PCI = 1


@_cenumdoc("hwloc_obj_osdev_type_e")
class ObjOsdevType(IntEnum):
    STORAGE = 1 << 0
    MEMORY = 1 << 1
    GPU = 1 << 2
    COPROC = 1 << 3
    NETWORK = 1 << 4
    OPENFABRICS = 1 << 5
    DMA = 1 << 6


HWLOC_TYPE_UNORDERED = 2147483647

_LIB.hwloc_compare_types.argtypes = [ctypes.c_int, ctypes.c_int]
_LIB.hwloc_compare_types.restype = ctypes.c_int


@_cfndoc
def compare_types(type1: ObjType, type2: ObjType) -> int:
    return _LIB.hwloc_compare_types(type1, type2)


#################################
# Object Structure and Attributes
#################################


# https://www.open-mpi.org/projects/hwloc/doc/v2.12.1/a00141.php


# The info_s and infos_s are dictionaries in Python.


@_cstructdoc("hwloc_info_s")
class Info(_PrintableStruct):
    _fields_ = [
        ("name", ctypes.c_char_p),  # Info name
        ("value", ctypes.c_char_p),  # Info value
    ]


@_cstructdoc("hwloc_infos_s")
class Infos(_PrintableStruct):
    _fields_ = [
        ("array", ctypes.POINTER(Info)),
        ("count", ctypes.c_uint),
        ("allocated", ctypes.c_uint),
    ]


if TYPE_CHECKING:
    InfosPtr = ctypes._Pointer[Infos]
else:
    InfosPtr = ctypes._Pointer


if _IS_V3:

    @_cstructdoc("hwloc_numanode_attr_s", parent="hwloc_obj_attr_u")
    class NumanodeAttr(_PrintableStruct):
        _fields_ = [
            ("local_memory", hwloc_uint64_t),  # Local memory (in bytes)
        ]

else:

    @_cstructdoc("hwloc_memory_page_type_s", parent="hwloc_obj_attr_u")
    class MemoryPageType(_PrintableStruct):
        _fields_ = [
            ("size", hwloc_uint64_t),  # Size of pages
            ("count", hwloc_uint64_t),  # Number of pages of this size
        ]

    @_cstructdoc("hwloc_numanode_attr_s", parent="hwloc_obj_attr_u")
    class NumanodeAttr(_PrintableStruct):  # type: ignore[no-redef]
        _fields_ = [
            ("local_memory", hwloc_uint64_t),  # Local memory (in bytes)
            ("page_types_len", ctypes.c_uint),  # Size of array page_types
            (
                "page_types",
                ctypes.POINTER(MemoryPageType),
            ),  # Array of local memory page types
        ]


@_cstructdoc("hwloc_cache_attr_s", parent="hwloc_obj_attr_u")
class CacheAttr(_PrintableStruct):
    _fields_ = [
        ("size", hwloc_uint64_t),  # Size of cache in bytes
        ("depth", ctypes.c_uint),  # Depth of cache (e.g., L1, L2, ...etc.)
        ("linesize", ctypes.c_uint),  # Cache-line size in bytes. 0 if unknown
        (
            "associativity",
            ctypes.c_int,
        ),  # Ways of associativity, -1 if fully associative, 0 if unknown
        ("type", ctypes.c_int),  # hwloc_obj_cache_type_t - Cache type
    ]


@_cstructdoc("hwloc_group_attr_s", parent="hwloc_obj_attr_u")
class GroupAttr(_PrintableStruct):
    _fields_ = [
        ("depth", ctypes.c_uint),  # Depth of group object
        ("kind", ctypes.c_uint),  # Internally-used kind of group
        (
            "subkind",
            ctypes.c_uint,
        ),  # Internally-used subkind to distinguish different levels
        (
            "dont_merge",
            ctypes.c_ubyte,
        ),  # Flag preventing groups from being automatically merged
    ]


@_cstructdoc("hwloc_pcidev_attr_s", parent="hwloc_obj_attr_u")
class PcidevAttr(_PrintableStruct):
    _fields_ = [
        (
            "domain",
            ctypes.c_uint,
        ),  # Domain number (xxxx in PCI BDF notation xxxx:yy:zz.t)
        ("bus", ctypes.c_ubyte),  # Bus number (yy in PCI BDF notation xxxx:yy:zz.t)
        ("dev", ctypes.c_ubyte),  # Device number (zz in PCI BDF notation xxxx:yy:zz.t)
        (
            "func",
            ctypes.c_ubyte,
        ),  # Function number (t in PCI BDF notation xxxx:yy:zz.t)
        ("prog_if", ctypes.c_ubyte),  # Register-level programming interface number
        (
            "class_id",
            ctypes.c_ushort,
        ),  # The class number (first two bytes, without prog_if)
        ("vendor_id", ctypes.c_ushort),  # Vendor ID (xxxx in [xxxx:yyyy])
        ("device_id", ctypes.c_ushort),  # Device ID (yyyy in [xxxx:yyyy])
        ("subvendor_id", ctypes.c_ushort),  # Sub-Vendor ID
        ("subdevice_id", ctypes.c_ushort),  # Sub-Device ID
        ("revision", ctypes.c_ubyte),  # Revision number
        ("linkspeed", ctypes.c_float),  # Link speed in GB/s
    ]

    @property
    def base_class(self) -> int:
        # upper byte
        return self.class_id >> 8

    @property
    def subclass(self) -> int:
        # lower byte
        return self.class_id & 0xFF


@_cuniondoc("hwloc_bridge_upstream_u", parent="hwloc_obj_attr_u.hwloc_bridge_attr_s")
class BridgeUpstream(ctypes.Union):
    _fields_ = [
        (
            "pci",
            PcidevAttr,
        ),  # PCI attribute of the upstream part as a PCI device
    ]


@_cstructdoc(
    "hwloc_bridge_downstream_pci_s", parent="hwloc_obj_attr_u.BridgeDownstream"
)
class BridgeDownstreamPci(_PrintableStruct):
    _fields_ = [
        ("domain", ctypes.c_uint),  # Domain number the downstream PCI buses
        ("secondary_bus", ctypes.c_ubyte),  # First PCI bus number below the bridge
        ("subordinate_bus", ctypes.c_ubyte),  # Highest PCI bus number below the bridge
    ]


@_cuniondoc("hwloc_bridge_downstream_u", parent="hwloc_obj_attr_u")
class BridgeDownstream(ctypes.Union):
    _fields_ = [
        ("pci", BridgeDownstreamPci),
    ]


@_cstructdoc("hwloc_bridge_attr_s", parent="hwloc_obj_attr_u")
class BridgeAttr(_PrintableStruct):
    _fields_ = [
        ("upstream", BridgeUpstream),
        (
            "upstream_type",
            ctypes.c_int,
        ),  # hwloc_obj_bridge_type_e - Upstream Bridge type
        ("downstream", BridgeDownstream),
        (
            "downstream_type",
            ctypes.c_int,
        ),  # hwloc_obj_bridge_type_e - Downstream Bridge type
        ("depth", ctypes.c_uint),
    ]


# OR'ed set of ::ObjOsdevType.
hwloc_obj_osdev_types_t = ctypes.c_ulong


@_cstructdoc("hwloc_osdev_attr_s", parent="hwloc_obj_attr_u")
class OsdevAttr(_PrintableStruct):
    _fields_ = [
        (
            "types",
            hwloc_obj_osdev_types_t,
        ),  # hwloc_obj_osdev_types_t - OR'ed set of at least one hwloc_obj_osdev_type_e
    ]


# Main attribute union
@_cuniondoc("hwloc_obj_attr_u")
class ObjAttr(ctypes.Union):
    _fields_ = [
        ("numanode", NumanodeAttr),  # NUMA node-specific Object Attributes
        ("cache", CacheAttr),  # Cache-specific Object Attributes
        ("group", GroupAttr),  # Group-specific Object Attributes
        ("pcidev", PcidevAttr),  # PCI Device specific Object Attributes
        ("bridge", BridgeAttr),  # Bridge specific Object Attributes
        ("osdev", OsdevAttr),  # OS Device specific Object Attributes
    ]


@_cstructdoc("hwloc_obj")
class Obj(_PrintableStruct):
    pass


obj_t = ctypes.POINTER(Obj)


_obj_fields: list[tuple[str, Any]] = [
    ("type", ctypes.c_int),  # hwloc_obj_type_t
    ("subtype", ctypes.c_char_p),
    ("os_index", ctypes.c_uint),
    ("name", ctypes.c_char_p),
    ("total_memory", hwloc_uint64_t),
    ("attr", ctypes.POINTER(ObjAttr)),
    ("depth", ctypes.c_int),
    ("logical_index", ctypes.c_uint),
    ("next_cousin", obj_t),
    ("prev_cousin", obj_t),
    ("parent", obj_t),
    ("sibling_rank", ctypes.c_uint),
    ("next_sibling", obj_t),
    ("prev_sibling", obj_t),
    ("arity", ctypes.c_uint),
    ("children", ctypes.POINTER(ctypes.POINTER(Obj))),
    ("first_child", obj_t),
    ("last_child", obj_t),
    ("symmetric_subtree", ctypes.c_int),
    ("memory_arity", ctypes.c_uint),
    ("memory_first_child", obj_t),
    ("io_arity", ctypes.c_uint),
    ("io_first_child", obj_t),
    ("misc_arity", ctypes.c_uint),
    ("misc_first_child", obj_t),
    ("cpuset", hwloc_cpuset_t),
    ("complete_cpuset", hwloc_cpuset_t),
    ("nodeset", hwloc_nodeset_t),
    ("complete_nodeset", hwloc_nodeset_t),
]

if _IS_V3:
    _obj_fields.append(("infos", Infos))
else:
    _obj_fields.extend(
        [
            ("infos", ctypes.POINTER(Info)),
            ("infos_count", ctypes.c_uint),
        ]
    )
_obj_fields.extend(
    [
        ("userdata", ctypes.c_void_p),
        ("gp_index", hwloc_uint64_t),
    ]
)

Obj._fields_ = _obj_fields


if TYPE_CHECKING:
    ObjPtr = ctypes._Pointer[Obj]
else:
    ObjPtr = ctypes._Pointer


###################################
# Topology Creation and Destruction
###################################

# https://www.open-mpi.org/projects/hwloc/doc/v2.12.1/a00142.php#ga9d1e76ee15a7dee158b786c30b6a6e38

topology_t = ctypes.c_void_p

_LIB.hwloc_topology_init.argtypes = [ctypes.POINTER(topology_t)]
_LIB.hwloc_topology_init.restype = ctypes.c_int


@_cfndoc
def topology_init(topology: topology_t) -> None:
    _checkc(_LIB.hwloc_topology_init(ctypes.byref(topology)))


_LIB.hwloc_topology_load.argtypes = [topology_t]
_LIB.hwloc_topology_load.restype = ctypes.c_int


@_cfndoc
def topology_load(topology: topology_t) -> None:
    _checkc(_LIB.hwloc_topology_load(topology))


_LIB.hwloc_topology_destroy.argtypes = [topology_t]
_LIB.hwloc_topology_destroy.restype = None


@_cfndoc
def topology_destroy(topology: topology_t) -> None:
    _LIB.hwloc_topology_destroy(topology)


_LIB.hwloc_topology_dup.argtypes = [ctypes.POINTER(topology_t), topology_t]
_LIB.hwloc_topology_dup.restype = ctypes.c_int


@_cfndoc
def topology_dup(topology: topology_t) -> topology_t:
    new = topology_t()
    _checkc(_LIB.hwloc_topology_dup(ctypes.byref(new), topology))
    return new


@_cfndoc
def topology_abi_check(topology: topology_t) -> None:
    _checkc(_LIB.hwloc_topology_abi_check(topology))


@_cfndoc
def topology_check(topology: topology_t) -> None:
    _LIB.hwloc_topology_check(topology)


#################################
# Object levels, depths and types
#################################

# https://www.open-mpi.org/projects/hwloc/doc/v2.12.1/a00143.php#gae54d1782ca9b54bea915f5c18a9158fa


@_cenumdoc("hwloc_get_type_depth_e")
class GetTypeDepth(IntEnum):
    UNKNOWN = -1
    MULTIPLE = -2
    NUMANODE = -3
    BRIDGE = -4
    PCI_DEVICE = -5
    OS_DEVICE = -6
    MISC = -7
    MEMCACHE = -8


_LIB.hwloc_topology_get_depth.argtypes = [topology_t]
_LIB.hwloc_topology_get_depth.restype = ctypes.c_int


@_cfndoc
def topology_get_depth(topology: topology_t) -> int:
    return _LIB.hwloc_topology_get_depth(topology)


_LIB.hwloc_get_type_depth.argtypes = [topology_t, ctypes.c_int]
_LIB.hwloc_get_type_depth.restype = ctypes.c_int


@_cfndoc
def get_type_depth(topology: topology_t, obj_type: ObjType) -> int:
    return _LIB.hwloc_get_type_depth(topology, obj_type)


if _IS_V3:
    _LIB.hwloc_get_type_depth_with_attr.argtypes = [
        topology_t,
        ctypes.c_int,  # ObjType
        ctypes.POINTER(ObjAttr),
        ctypes.c_size_t,
    ]
    _LIB.hwloc_get_type_depth_with_attr.restype = ctypes.c_int

    @_cfndoc
    def get_type_depth_with_attr(
        topology: topology_t,
        obj_type: ObjType,
        attr: ctypes._Pointer,  # [hwloc_obj_attr_u]
        attrsize: int,
    ) -> int:
        return _LIB.hwloc_get_type_depth_with_attr(topology, obj_type, attr, attrsize)


_LIB.hwloc_get_memory_parents_depth.argtypes = [topology_t]
_LIB.hwloc_get_memory_parents_depth.restype = ctypes.c_int


@_cfndoc
def get_memory_parents_depth(topology: topology_t) -> int:
    return _LIB.hwloc_get_memory_parents_depth(topology)


_pyhwloc_lib.pyhwloc_get_type_or_above_depth.argtypes = [topology_t, ctypes.c_int]
_pyhwloc_lib.pyhwloc_get_type_or_above_depth.restype = ctypes.c_int


@_cfndoc
def get_type_or_below_depth(topology: topology_t, obj_type: ObjType) -> int:
    return _pyhwloc_lib.pyhwloc_get_type_or_below_depth(topology, obj_type)


@_cfndoc
def get_type_or_above_depth(topology: topology_t, obj_type: ObjType) -> int:
    return _pyhwloc_lib.pyhwloc_get_type_or_above_depth(topology, obj_type)


_LIB.hwloc_get_depth_type.argtypes = [topology_t, ctypes.c_int]
_LIB.hwloc_get_depth_type.restype = ctypes.c_int


@_cfndoc
def get_depth_type(topology: topology_t, depth: int) -> ObjType:
    return ObjType(_LIB.hwloc_get_depth_type(topology, depth))


_pyhwloc_lib.pyhwloc_get_nbobjs_by_type.argtypes = [topology_t, ctypes.c_int]
_pyhwloc_lib.pyhwloc_get_nbobjs_by_type.restype = ctypes.c_int


@_cfndoc
def get_nbobjs_by_type(topology: topology_t, obj_type: ObjType) -> int:
    return _pyhwloc_lib.pyhwloc_get_nbobjs_by_type(topology, obj_type)


_pyhwloc_lib.pyhwloc_get_root_obj.argtypes = [topology_t]
_pyhwloc_lib.pyhwloc_get_root_obj.restype = obj_t


@_cfndoc
def get_root_obj(topology: topology_t) -> ObjPtr:
    # This function cannot return NULL.
    return _pyhwloc_lib.pyhwloc_get_root_obj(topology)


_pyhwloc_lib.pyhwloc_get_obj_by_type.argtypes = [
    topology_t,
    ctypes.c_int,
    ctypes.c_uint,
]
_pyhwloc_lib.pyhwloc_get_obj_by_type.restype = obj_t


@_cfndoc
def get_obj_by_type(topology: topology_t, obj_type: ObjType, idx: int) -> ObjPtr | None:
    obj = _pyhwloc_lib.pyhwloc_get_obj_by_type(topology, obj_type, idx)
    if not obj:
        return None
    return obj


_pyhwloc_lib.pyhwloc_get_next_obj_by_depth.argtypes = [
    topology_t,
    ctypes.c_int,
    obj_t,
]
_pyhwloc_lib.pyhwloc_get_next_obj_by_depth.restype = obj_t


@_cfndoc
def get_next_obj_by_depth(
    topology: topology_t, depth: int, prev: ObjPtr | None
) -> ObjPtr | None:
    obj = _pyhwloc_lib.pyhwloc_get_next_obj_by_depth(topology, depth, prev)
    if not obj:
        return None
    return obj


_pyhwloc_lib.pyhwloc_get_next_obj_by_type.argtypes = [
    topology_t,
    ctypes.c_int,
    obj_t,
]
_pyhwloc_lib.pyhwloc_get_next_obj_by_type.restype = obj_t


@_cfndoc
def get_next_obj_by_type(
    topology: topology_t, obj_type: ObjType, prev: ObjPtr | None
) -> ObjPtr | None:
    obj = _pyhwloc_lib.pyhwloc_get_next_obj_by_type(topology, obj_type, prev)
    if not obj:
        return None
    return obj


@_cfndoc
def get_nbobjs_by_depth(topology: topology_t, depth: int) -> int:
    return _LIB.hwloc_get_nbobjs_by_depth(topology, depth)


_LIB.hwloc_get_obj_by_depth.argtypes = [topology_t, ctypes.c_int, ctypes.c_uint]
_LIB.hwloc_get_obj_by_depth.restype = obj_t


@_cfndoc
def get_obj_by_depth(topology: topology_t, depth: int, idx: int) -> ObjPtr | None:
    obj = _LIB.hwloc_get_obj_by_depth(topology, depth, idx)
    if not obj:
        return None
    return obj


#############################################################
# Converting between Object Types and Attributes, and Strings
#############################################################

# https://www.open-mpi.org/projects/hwloc/doc/v2.12.1/a00144.php

_LIB.hwloc_obj_type_string.argtypes = [ctypes.c_int]
_LIB.hwloc_obj_type_string.restype = ctypes.c_char_p


@_cfndoc
def hwloc_obj_type_string(obj_type: ObjType) -> bytes:
    return _LIB.hwloc_obj_type_string(obj_type).value


@_cenumdoc("hwloc_obj_snprintf_flag_e")
class ObjSnprintfFlag(IntEnum):
    OLD_VERBOSE = 1 << 0
    LONG_NAMES = 1 << 1
    SHORT_NAMES = 1 << 2
    MORE_ATTRS = 1 << 3
    NO_UNITS = 1 << 4
    UNITS_1000 = 1 << 5


_LIB.hwloc_obj_type_snprintf.argtypes = [
    ctypes.c_char_p,
    ctypes.c_size_t,
    obj_t,
    ctypes.c_ulong,
]
_LIB.hwloc_obj_type_snprintf.restype = ctypes.c_int


@_cfndoc
def obj_type_snprintf(
    string: ctypes.c_char_p | ctypes.Array, size: int, obj: ObjPtr, flags: int
) -> int:
    # flags are hwloc_obj_snprintf_flag_e
    return _LIB.hwloc_obj_type_snprintf(string, size, obj, int(flags))


_LIB.hwloc_obj_attr_snprintf.argtypes = [
    ctypes.c_char_p,
    ctypes.c_size_t,
    obj_t,
    ctypes.c_char_p,
    ctypes.c_ulong,
]
_LIB.hwloc_obj_attr_snprintf.restype = ctypes.c_int


@_cfndoc
def obj_attr_snprintf(
    string: ctypes.c_char_p | ctypes.Array,
    size: int,
    obj: ObjPtr,
    separator: str,
    flags: int,
) -> int:
    # flags are hwloc_obj_snprintf_flag_e
    return _LIB.hwloc_obj_attr_snprintf(
        string, size, obj, separator.encode("utf-8"), int(flags)
    )


_LIB.hwloc_type_sscanf.argtypes = [
    ctypes.c_char_p,
    ctypes.POINTER(ctypes.c_int),
    ctypes.POINTER(ObjAttr),
    ctypes.c_size_t,
]
_LIB.hwloc_type_sscanf.restype = ctypes.c_int


@_cfndoc
def type_sscanf(string: str) -> tuple[ObjType, ObjAttr | None]:
    string_bytes = string.encode("utf-8")
    typep = ctypes.c_int()

    attrp = ObjAttr()
    result = _LIB.hwloc_type_sscanf(
        string_bytes, ctypes.byref(typep), ctypes.byref(attrp), ctypes.sizeof(attrp)
    )
    _checkc(result)
    return ObjType(typep.value), attrp


_LIB.hwloc_type_sscanf_as_depth.argtypes = [
    ctypes.c_char_p,
    ctypes.POINTER(ctypes.c_int),
    topology_t,
    ctypes.POINTER(ctypes.c_int),
]
_LIB.hwloc_type_sscanf_as_depth.restype = ctypes.c_int


@_cfndoc
def type_sscanf_as_depth(string: str, topology: topology_t) -> tuple[ObjType, int]:
    string_bytes = string.encode("utf-8")
    typep = ctypes.c_int()
    depthp = ctypes.c_int()

    _checkc(
        _LIB.hwloc_type_sscanf_as_depth(
            string_bytes, ctypes.byref(typep), topology, ctypes.byref(depthp)
        )
    )

    return ObjType(typep.value), depthp.value


#######################################
# Consulting and Adding Info Attributes
#######################################

# https://www.open-mpi.org/projects/hwloc/doc/v2.12.1/a00145.php


if _IS_V3:
    _pyhwloc_lib.pyhwloc_get_info_by_name.argtypes = [
        ctypes.POINTER(Infos),
        ctypes.c_char_p,
    ]
    _pyhwloc_lib.pyhwloc_get_info_by_name.restype = ctypes.c_char_p
else:
    _pyhwloc_lib.pyhwloc_obj_get_info_by_name.argtypes = [obj_t, ctypes.c_char_p]
    _pyhwloc_lib.pyhwloc_obj_get_info_by_name.restype = ctypes.c_char_p


@_cfndoc
def obj_get_info_by_name(obj: ObjPtr, name: str) -> str | None:
    name_bytes = name.encode("utf-8")
    if _IS_V3:
        result = _pyhwloc_lib.pyhwloc_get_info_by_name(
            ctypes.byref(obj.contents.infos), name_bytes
        )
    else:
        result = _pyhwloc_lib.pyhwloc_obj_get_info_by_name(obj, name_bytes)
    if result:
        return result.decode("utf-8")
    return None


_pyhwloc_lib.pyhwloc_obj_add_info.argtypes = [obj_t, ctypes.c_char_p, ctypes.c_char_p]
_pyhwloc_lib.pyhwloc_obj_add_info.restype = ctypes.c_int


@_cfndoc
def obj_add_info(obj: ObjPtr, name: str, value: str) -> None:
    if not name or not value:
        raise ValueError("name and value must be non-empty strings")

    name_bytes = name.encode("utf-8")
    value_bytes = value.encode("utf-8")
    _checkc(_pyhwloc_lib.pyhwloc_obj_add_info(obj, name_bytes, value_bytes))


_LIB.hwloc_obj_set_subtype.argtypes = [topology_t, obj_t, ctypes.c_char_p]
_LIB.hwloc_obj_set_subtype.restype = ctypes.c_int


@_cfndoc
def obj_set_subtype(topology: topology_t, obj: ObjPtr, subtype: str) -> None:
    subtype_bytes = subtype.encode("utf-8")
    _checkc(_LIB.hwloc_obj_set_subtype(topology, obj, subtype_bytes))


if _IS_V3:
    _LIB.hwloc_topology_get_infos.argtypes = [topology_t]
    _LIB.hwloc_topology_get_infos.restype = ctypes.POINTER(Infos)


@_cfndoc
def topology_get_infos(topology: topology_t) -> InfosPtr:
    if not _IS_V3:
        raise NotImplementedError("Only valid in v3.")
    infos = _LIB.hwloc_topology_get_infos(topology)
    return infos


#############
# CPU binding
#############

# https://www.open-mpi.org/projects/hwloc/doc/v2.12.1/a00146.php


@_cenumdoc("hwloc_cpubind_flags_t")
class CpuBindFlags(IntEnum):
    PROCESS = 1 << 0
    THREAD = 1 << 1
    STRICT = 1 << 2
    NOMEMBIND = 1 << 3


if sys.platform == "win32":
    hwloc_thread_t = ctypes.c_void_p
    hwloc_pid_t = ctypes.c_void_p

    ctypes.windll.kernel32.OpenThread.restype = hwloc_thread_t
    ctypes.windll.kernel32.OpenThread.argtypes = [
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
    ]

    def _open_thread_handle(thread_id: int, read_only: bool = True) -> hwloc_thread_t:
        THREAD_SET_INFORMATION = 0x0020
        THREAD_QUERY_INFORMATION = 0x0040

        access = THREAD_QUERY_INFORMATION
        if not read_only:
            access |= THREAD_SET_INFORMATION
        hdl = ctypes.windll.kernel32.OpenThread(access, 0, thread_id)
        if not hdl:
            raise ctypes.WinError()
        return ctypes.cast(hdl, hwloc_thread_t)

    ctypes.windll.kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    ctypes.windll.kernel32.CloseHandle.restype = ctypes.c_int

    def _close_thread_handle(thread_hdl: hwloc_thread_t) -> None:
        status = ctypes.windll.kernel32.CloseHandle(thread_hdl)
        if status == 0:
            raise ctypes.WinError()

    ctypes.windll.kernel32.OpenProcess.restype = hwloc_pid_t
    ctypes.windll.kernel32.OpenProcess.argtypes = [
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
    ]

    def _open_proc_handle(pid: int, read_only: bool = True) -> hwloc_pid_t:
        PROCESS_SET_INFORMATION = 0x0200
        PROCESS_QUERY_INFORMATION = 0x0400

        access = PROCESS_QUERY_INFORMATION
        if not read_only:
            access |= PROCESS_SET_INFORMATION
        hdl = ctypes.windll.kernel32.OpenProcess(access, 0, pid)
        if not hdl:
            raise ctypes.WinError()
        return ctypes.cast(hdl, hwloc_pid_t)

    def _close_proc_handle(proc_hdl: hwloc_pid_t) -> None:
        status = ctypes.windll.kernel32.CloseHandle(proc_hdl)
        if status == 0:
            raise ctypes.WinError()

else:
    hwloc_thread_t = ctypes.c_ulong
    hwloc_pid_t = ctypes.c_int

    def _open_thread_handle(thread_id: int, read_only: bool = True) -> hwloc_thread_t:
        return hwloc_thread_t(thread_id)

    def _close_thread_handle(thread_hdl: hwloc_thread_t) -> None:
        pass

    def _open_proc_handle(pid: int, read_only: bool = True) -> hwloc_pid_t:
        return hwloc_pid_t(pid)

    def _close_proc_handle(thread_hdl: hwloc_pid_t) -> None:
        pass


_LIB.hwloc_set_cpubind.argtypes = [topology_t, hwloc_const_cpuset_t, ctypes.c_int]
_LIB.hwloc_set_cpubind.restype = ctypes.c_int


@_cfndoc
def set_cpubind(topology: topology_t, cpuset: hwloc_const_cpuset_t, flags: int) -> None:
    _checkc(_LIB.hwloc_set_cpubind(topology, cpuset, flags))


_LIB.hwloc_get_cpubind.argtypes = [topology_t, hwloc_cpuset_t, ctypes.c_int]
_LIB.hwloc_get_cpubind.restype = ctypes.c_int


@_cfndoc
def get_cpubind(topology: topology_t, cpuset: hwloc_cpuset_t, flags: int) -> None:
    _checkc(_LIB.hwloc_get_cpubind(topology, cpuset, flags))


_LIB.hwloc_set_proc_cpubind.argtypes = [
    topology_t,
    hwloc_pid_t,
    hwloc_const_cpuset_t,
    ctypes.c_int,
]
_LIB.hwloc_set_proc_cpubind.restype = ctypes.c_int


@_cfndoc
def set_proc_cpubind(
    topology: topology_t, pid: hwloc_pid_t, cpuset: hwloc_const_cpuset_t, flags: int
) -> None:
    _checkc(_LIB.hwloc_set_proc_cpubind(topology, pid, cpuset, flags))


_LIB.hwloc_get_proc_cpubind.argtypes = [
    topology_t,
    hwloc_pid_t,
    hwloc_cpuset_t,
    ctypes.c_int,
]
_LIB.hwloc_get_proc_cpubind.restype = ctypes.c_int


@_cfndoc
def get_proc_cpubind(
    topology: topology_t, pid: hwloc_pid_t, cpuset: hwloc_cpuset_t, flags: int
) -> None:
    _checkc(_LIB.hwloc_get_proc_cpubind(topology, pid, cpuset, flags))


_LIB.hwloc_set_thread_cpubind.argtypes = [
    topology_t,
    hwloc_thread_t,
    hwloc_const_cpuset_t,
    ctypes.c_int,
]
_LIB.hwloc_set_thread_cpubind.restype = ctypes.c_int


@_cfndoc
def set_thread_cpubind(
    topology: topology_t,
    thread: hwloc_thread_t,
    cpuset: hwloc_const_cpuset_t,
    flags: int,
) -> None:
    _checkc(_LIB.hwloc_set_thread_cpubind(topology, thread, cpuset, flags))


_LIB.hwloc_get_thread_cpubind.argtypes = [
    topology_t,
    hwloc_thread_t,
    hwloc_cpuset_t,
    ctypes.c_int,
]
_LIB.hwloc_get_thread_cpubind.restype = ctypes.c_int


@_cfndoc
def get_thread_cpubind(
    topology: topology_t, thread: hwloc_thread_t, cpuset: hwloc_cpuset_t, flags: int
) -> None:
    _checkc(_LIB.hwloc_get_thread_cpubind(topology, thread, cpuset, flags))


_LIB.hwloc_get_last_cpu_location.argtypes = [topology_t, hwloc_cpuset_t, ctypes.c_int]
_LIB.hwloc_get_last_cpu_location.restype = ctypes.c_int


@_cfndoc
def get_last_cpu_location(
    topology: topology_t, cpuset: hwloc_cpuset_t, flags: int
) -> None:
    _checkc(_LIB.hwloc_get_last_cpu_location(topology, cpuset, flags))


_LIB.hwloc_get_proc_last_cpu_location.argtypes = [
    topology_t,
    hwloc_pid_t,
    hwloc_cpuset_t,
    ctypes.c_int,
]
_LIB.hwloc_get_proc_last_cpu_location.restype = ctypes.c_int


@_cfndoc
def get_proc_last_cpu_location(
    topology: topology_t, pid: hwloc_pid_t, cpuset: hwloc_cpuset_t, flags: int
) -> None:
    _checkc(_LIB.hwloc_get_proc_last_cpu_location(topology, pid, cpuset, flags))


################
# Memory binding
################

# https://www.open-mpi.org/projects/hwloc/doc/v2.12.1/a00147.php


@_cenumdoc("hwloc_membind_policy_t")
class MemBindPolicy(IntEnum):
    DEFAULT = 0
    FIRSTTOUCH = 1
    BIND = 2
    INTERLEAVE = 3
    WEIGHTED_INTERLEAVE = 5
    NEXTTOUCH = 4
    MIXED = -1


@_cenumdoc("hwloc_membind_flags_t")
class MemBindFlags(IntEnum):
    PROCESS = 1 << 0
    THREAD = 1 << 1
    STRICT = 1 << 2
    # Only used by Linux `set_area_membind` and `set_thisthread_membind`.
    MIGRATE = 1 << 3
    NOCPUBIND = 1 << 4
    BYNODESET = 1 << 5


_LIB.hwloc_set_membind.argtypes = [
    topology_t,
    const_bitmap_t,
    ctypes.c_int,
    ctypes.c_int,
]
_LIB.hwloc_set_membind.restype = ctypes.c_int


@_cfndoc
def set_membind(
    topology: topology_t,
    set: const_bitmap_t,
    policy: MemBindPolicy,
    flags: int,
) -> None:
    _checkc(_LIB.hwloc_set_membind(topology, set, policy, flags))


_LIB.hwloc_get_membind.argtypes = [
    topology_t,
    bitmap_t,
    ctypes.POINTER(ctypes.c_int),
    ctypes.c_int,
]
_LIB.hwloc_get_membind.restype = ctypes.c_int


@_cfndoc
def get_membind(topology: topology_t, set: bitmap_t, flags: int) -> MemBindPolicy:
    policy = ctypes.c_int()
    _checkc(_LIB.hwloc_get_membind(topology, set, ctypes.byref(policy), flags))
    return MemBindPolicy(policy.value)


_LIB.hwloc_set_proc_membind.argtypes = [
    topology_t,
    hwloc_pid_t,
    const_bitmap_t,
    ctypes.c_int,
    ctypes.c_int,
]
_LIB.hwloc_set_proc_membind.restype = ctypes.c_int


@_cfndoc
def set_proc_membind(
    topology: topology_t,
    pid: hwloc_pid_t,
    set: const_bitmap_t,
    policy: MemBindPolicy,
    flags: int,
) -> None:
    _checkc(_LIB.hwloc_set_proc_membind(topology, pid, set, policy, flags))


_LIB.hwloc_get_proc_membind.argtypes = [
    topology_t,
    hwloc_pid_t,
    bitmap_t,
    ctypes.POINTER(ctypes.c_int),
    ctypes.c_int,
]
_LIB.hwloc_get_proc_membind.restype = ctypes.c_int


@_cfndoc
def get_proc_membind(
    topology: topology_t, pid: hwloc_pid_t, set: bitmap_t, flags: int
) -> MemBindPolicy:
    # Note that it does not make sense to pass ::HWLOC_MEMBIND_THREAD to this function.
    policy = ctypes.c_int()
    _checkc(
        _LIB.hwloc_get_proc_membind(topology, pid, set, ctypes.byref(policy), flags)
    )
    return MemBindPolicy(policy.value)


_LIB.hwloc_set_area_membind.argtypes = [
    topology_t,
    ctypes.c_void_p,
    ctypes.c_size_t,
    const_bitmap_t,
    ctypes.c_int,
    ctypes.c_int,
]
_LIB.hwloc_set_area_membind.restype = ctypes.c_int


@_cfndoc
def set_area_membind(
    topology: topology_t,
    addr: ctypes.c_void_p,
    length: int,
    set: const_bitmap_t,
    policy: MemBindPolicy,
    flags: int,
) -> None:
    _checkc(_LIB.hwloc_set_area_membind(topology, addr, length, set, policy, flags))


_LIB.hwloc_get_area_membind.argtypes = [
    topology_t,
    ctypes.c_void_p,
    ctypes.c_size_t,
    bitmap_t,
    ctypes.POINTER(ctypes.c_int),
    ctypes.c_int,
]
_LIB.hwloc_get_area_membind.restype = ctypes.c_int


@_cfndoc
def get_area_membind(
    topology: topology_t, addr: ctypes.c_void_p, length: int, set: bitmap_t, flags: int
) -> MemBindPolicy:
    policy = ctypes.c_int()
    _checkc(
        _LIB.hwloc_get_area_membind(
            topology, addr, length, set, ctypes.byref(policy), flags
        )
    )
    return MemBindPolicy(policy.value)


_LIB.hwloc_get_area_memlocation.argtypes = [
    topology_t,
    ctypes.c_void_p,
    ctypes.c_size_t,
    bitmap_t,
    ctypes.c_int,
]
_LIB.hwloc_get_area_memlocation.restype = ctypes.c_int


@_cfndoc
def get_area_memlocation(
    topology: topology_t, addr: ctypes.c_void_p, length: int, set: bitmap_t, flags: int
) -> None:
    _checkc(_LIB.hwloc_get_area_memlocation(topology, addr, length, set, flags))


_LIB.hwloc_alloc.argtypes = [topology_t, ctypes.c_size_t]
_LIB.hwloc_alloc.restype = ctypes.c_void_p


@_cfndoc
def alloc(topology: topology_t, length: int) -> ctypes.c_void_p:
    result = _LIB.hwloc_alloc(topology, length)
    if not result:
        raise _hwloc_error("hwloc_alloc")
    return result


_LIB.hwloc_alloc_membind.argtypes = [
    topology_t,
    ctypes.c_size_t,
    const_bitmap_t,
    ctypes.c_int,
    ctypes.c_int,
]
_LIB.hwloc_alloc_membind.restype = ctypes.c_void_p


@_cfndoc
def alloc_membind(
    topology: topology_t,
    length: int,
    set: const_bitmap_t,
    policy: MemBindPolicy,
    flags: int,
) -> ctypes.c_void_p:
    result = _LIB.hwloc_alloc_membind(topology, length, set, policy, flags)
    if not result:
        raise _hwloc_error("hwloc_alloc_membind")
    return result


_pyhwloc_lib.pyhwloc_alloc_membind_policy.argtypes = [
    topology_t,
    ctypes.c_size_t,
    const_bitmap_t,
    ctypes.c_int,
    ctypes.c_int,
]
_pyhwloc_lib.pyhwloc_alloc_membind_policy.restype = ctypes.c_void_p


@_cfndoc
def alloc_membind_policy(
    topology: topology_t,
    length: int,
    set: const_bitmap_t,
    policy: MemBindPolicy,
    flags: int,
) -> ctypes.c_void_p:
    result = _pyhwloc_lib.pyhwloc_alloc_membind_policy(
        topology, length, set, policy, flags
    )
    if not result:
        raise _hwloc_error("hwloc_alloc_membind_policy")
    return result


_LIB.hwloc_free.argtypes = [topology_t, ctypes.c_void_p, ctypes.c_size_t]
_LIB.hwloc_free.restype = ctypes.c_int


@_cfndoc
def free(topology: topology_t, addr: ctypes.c_void_p, length: int) -> None:
    _checkc(_LIB.hwloc_free(topology, addr, length))


###########################################
# Changing the Source of Topology Discovery
###########################################


# https://www.open-mpi.org/projects/hwloc/doc/v2.12.0/a00148.php


class TopologyComponentsFlag(IntEnum):
    BLACKLIST = 1 << 0


_LIB.hwloc_topology_set_pid.argtypes = [topology_t, hwloc_pid_t]
_LIB.hwloc_topology_set_pid.restype = ctypes.c_int


@_cfndoc
def topology_set_pid(topology: topology_t, pid: int) -> None:
    _checkc(_LIB.hwloc_topology_set_pid(topology, hwloc_pid_t(pid)))


_LIB.hwloc_topology_set_synthetic.argtypes = [topology_t, ctypes.c_char_p]
_LIB.hwloc_topology_set_synthetic.restype = ctypes.c_int


@_cfndoc
def topology_set_synthetic(topology: topology_t, description: str) -> None:
    description_bytes = description.encode("utf-8")
    _checkc(_LIB.hwloc_topology_set_synthetic(topology, description_bytes))


_LIB.hwloc_topology_set_xml.argtypes = [topology_t, ctypes.c_char_p]
_LIB.hwloc_topology_set_xml.restype = ctypes.c_int


@_cfndoc
def topology_set_xml(topology: topology_t, xmlpath: str) -> None:
    xmlpath_bytes = xmlpath.encode("utf-8")
    _checkc(_LIB.hwloc_topology_set_xml(topology, xmlpath_bytes))


_LIB.hwloc_topology_set_xmlbuffer.argtypes = [topology_t, ctypes.c_char_p, ctypes.c_int]
_LIB.hwloc_topology_set_xmlbuffer.restype = ctypes.c_int


@_cfndoc
def topology_set_xmlbuffer(topology: topology_t, buf: str) -> None:
    buffer_bytes = buf.encode("utf-8")
    _checkc(
        _LIB.hwloc_topology_set_xmlbuffer(topology, buffer_bytes, len(buffer_bytes))
    )


_LIB.hwloc_topology_set_components.argtypes = [
    topology_t,
    ctypes.c_ulong,
    ctypes.c_char_p,
]
_LIB.hwloc_topology_set_components.restype = ctypes.c_int


@_cfndoc
def topology_set_components(topology: topology_t, flags: int, name: str) -> None:
    name_bytes = name.encode("utf-8")
    _checkc(_LIB.hwloc_topology_set_components(topology, flags, name_bytes))


############################################
# Topology Detection Configuration and Query
############################################


# https://www.open-mpi.org/projects/hwloc/doc/v2.12.0/a00149.php


@_cstructdoc("hwloc_topology_discovery_support")
class TopologyDiscoverySupport(_PrintableStruct):
    _fields_ = [
        ("pu", ctypes.c_ubyte),
        ("numa", ctypes.c_ubyte),
        ("numa_memory", ctypes.c_ubyte),
        ("disallowed_pu", ctypes.c_ubyte),
        ("disallowed_numa", ctypes.c_ubyte),
        ("cpukind_efficiency", ctypes.c_ubyte),
    ]


@_cstructdoc("hwloc_topology_cpubind_support")
class TopologyCpubindSupport(_PrintableStruct):
    _fields_ = [
        ("set_thisproc_cpubind", ctypes.c_ubyte),
        ("get_thisproc_cpubind", ctypes.c_ubyte),
        ("set_proc_cpubind", ctypes.c_ubyte),
        ("get_proc_cpubind", ctypes.c_ubyte),
        ("set_thisthread_cpubind", ctypes.c_ubyte),
        ("get_thisthread_cpubind", ctypes.c_ubyte),
        ("set_thread_cpubind", ctypes.c_ubyte),
        ("get_thread_cpubind", ctypes.c_ubyte),
        ("get_thisproc_last_cpu_location", ctypes.c_ubyte),
        ("get_proc_last_cpu_location", ctypes.c_ubyte),
        ("get_thisthread_last_cpu_location", ctypes.c_ubyte),
    ]


@_cstructdoc("hwloc_topology_membind_support")
class TopologyMembindSupport(_PrintableStruct):
    _fields_ = [
        ("set_thisproc_membind", ctypes.c_ubyte),
        ("get_thisproc_membind", ctypes.c_ubyte),
        ("set_proc_membind", ctypes.c_ubyte),
        ("get_proc_membind", ctypes.c_ubyte),
        ("set_thisthread_membind", ctypes.c_ubyte),
        ("get_thisthread_membind", ctypes.c_ubyte),
        ("alloc_membind", ctypes.c_ubyte),
        ("set_area_membind", ctypes.c_ubyte),
        ("get_area_membind", ctypes.c_ubyte),
        ("get_area_memlocation", ctypes.c_ubyte),
        ("firsttouch_membind", ctypes.c_ubyte),
        ("bind_membind", ctypes.c_ubyte),
        ("interleave_membind", ctypes.c_ubyte),
        ("weighted_interleave_membind", ctypes.c_ubyte),
        ("nexttouch_membind", ctypes.c_ubyte),
        ("migrate_membind", ctypes.c_ubyte),
    ]


@_cstructdoc("hwloc_topology_misc_support")
class TopologyMiscSupport(_PrintableStruct):
    _fields_ = [
        ("imported_support", ctypes.c_ubyte),
    ]


@_cstructdoc("hwloc_topology_support")
class TopologySupport(_PrintableStruct):
    _fields_ = [
        ("discovery", ctypes.POINTER(TopologyDiscoverySupport)),
        ("cpubind", ctypes.POINTER(TopologyCpubindSupport)),
        ("membind", ctypes.POINTER(TopologyMembindSupport)),
        ("misc", ctypes.POINTER(TopologyMiscSupport)),
    ]


@_cenumdoc("hwloc_topology_flags_e")
class TopologyFlags(IntEnum):
    INCLUDE_DISALLOWED = 1 << 0
    IS_THISSYSTEM = 1 << 1
    THISSYSTEM_ALLOWED_RESOURCES = 1 << 2
    IMPORT_SUPPORT = 1 << 3
    RESTRICT_TO_CPUBINDING = 1 << 4
    RESTRICT_TO_MEMBINDING = 1 << 5
    DONT_CHANGE_BINDING = 1 << 6
    NO_DISTANCES = 1 << 7
    NO_MEMATTRS = 1 << 8
    NO_CPUKINDS = 1 << 9


@_cenumdoc("hwloc_type_filter_e")
class TypeFilter(IntEnum):
    KEEP_ALL = 0
    KEEP_NONE = 1
    KEEP_STRUCTURE = 2
    KEEP_IMPORTANT = 3


_LIB.hwloc_topology_set_flags.argtypes = [topology_t, ctypes.c_ulong]
_LIB.hwloc_topology_set_flags.restype = ctypes.c_int


@_cfndoc
def topology_set_flags(topology: topology_t, flags: int) -> None:
    _checkc(_LIB.hwloc_topology_set_flags(topology, flags))


_LIB.hwloc_topology_get_flags.argtypes = [topology_t]
_LIB.hwloc_topology_get_flags.restype = ctypes.c_ulong


@_cfndoc
def topology_get_flags(topology: topology_t) -> int:
    return _LIB.hwloc_topology_get_flags(topology)


_LIB.hwloc_topology_is_thissystem.argtypes = [topology_t]
_LIB.hwloc_topology_is_thissystem.restype = ctypes.c_int


@_cfndoc
def topology_is_thissystem(topology: topology_t) -> bool:
    return bool(_LIB.hwloc_topology_is_thissystem(topology))


_LIB.hwloc_topology_get_support.argtypes = [topology_t]
_LIB.hwloc_topology_get_support.restype = ctypes.POINTER(TopologySupport)


if TYPE_CHECKING:
    SupportType = ctypes._Pointer[TopologySupport]
else:
    SupportType = ctypes._Pointer


@_cfndoc
def topology_get_support(topology: topology_t) -> SupportType:
    return _LIB.hwloc_topology_get_support(topology)


_LIB.hwloc_topology_set_type_filter.argtypes = [topology_t, ctypes.c_int, ctypes.c_int]
_LIB.hwloc_topology_set_type_filter.restype = ctypes.c_int


@_cfndoc
def topology_set_type_filter(
    topology: topology_t, obj_type: ObjType, f: TypeFilter
) -> None:
    _checkc(_LIB.hwloc_topology_set_type_filter(topology, obj_type, f))


_LIB.hwloc_topology_get_type_filter.argtypes = [
    topology_t,
    ctypes.c_int,
    ctypes.POINTER(ctypes.c_int),
]
_LIB.hwloc_topology_get_type_filter.restype = ctypes.c_int


@_cfndoc
def topology_get_type_filter(topology: topology_t, obj_type: ObjType) -> TypeFilter:
    f = ctypes.c_int()
    _checkc(_LIB.hwloc_topology_get_type_filter(topology, obj_type, ctypes.byref(f)))
    return TypeFilter(f.value)


@_cfndoc
def topology_set_all_types_filter(topology: topology_t, f: TypeFilter) -> None:
    _checkc(_LIB.hwloc_topology_set_all_types_filter(topology, f))


@_cfndoc
def topology_set_cache_types_filter(topology: topology_t, f: TypeFilter) -> None:
    _checkc(_LIB.hwloc_topology_set_cache_types_filter(topology, f))


@_cfndoc
def topology_set_icache_types_filter(topology: topology_t, f: TypeFilter) -> None:
    _checkc(_LIB.hwloc_topology_set_icache_types_filter(topology, f))


@_cfndoc
def topology_set_io_types_filter(topology: topology_t, f: TypeFilter) -> None:
    _checkc(_LIB.hwloc_topology_set_io_types_filter(topology, f))


_LIB.hwloc_topology_set_userdata.argtypes = [topology_t, ctypes.c_void_p]
_LIB.hwloc_topology_set_userdata.restype = None


@_cfndoc
def topology_set_userdata(topology: topology_t, userdata: int) -> None:
    _LIB.hwloc_topology_set_userdata(topology, userdata)


_LIB.hwloc_topology_get_userdata.argtypes = [topology_t]
_LIB.hwloc_topology_get_userdata.restype = ctypes.c_void_p


@_cfndoc
def topology_get_userdata(topology: topology_t) -> int:
    return _LIB.hwloc_topology_get_userdata(topology)


#############################
# Modifying a Loaded Topology
#############################

# https://www.open-mpi.org/projects/hwloc/doc/v2.12.0/a00150.php


@_cenumdoc("hwloc_restrict_flags_e")
class RestrictFlags(IntEnum):
    REMOVE_CPULESS = 1 << 0
    ADAPT_MISC = 1 << 1
    ADAPT_IO = 1 << 2
    BYNODESET = 1 << 3
    REMOVE_MEMLESS = 1 << 4


@_cenumdoc("hwloc_allow_flags_e")
class AllowFlags(IntEnum):
    ALL = 1 << 0
    LOCAL_RESTRICTIONS = 1 << 1
    CUSTOM = 1 << 2


_LIB.hwloc_topology_restrict.argtypes = [
    topology_t,
    const_bitmap_t,
    ctypes.c_ulong,
]
_LIB.hwloc_topology_restrict.restype = ctypes.c_int


@_cfndoc
def topology_restrict(topology: topology_t, cpuset: const_bitmap_t, flags: int) -> None:
    _checkc(_LIB.hwloc_topology_restrict(topology, cpuset, flags))


_LIB.hwloc_topology_allow.argtypes = [
    topology_t,
    hwloc_const_cpuset_t,
    hwloc_const_nodeset_t,
    ctypes.c_ulong,
]
_LIB.hwloc_topology_allow.restype = ctypes.c_int


@_cfndoc
def topology_allow(
    topology: topology_t,
    cpuset: hwloc_const_cpuset_t | None,
    nodeset: hwloc_const_nodeset_t | None,
    flags: int,
) -> None:
    _checkc(_LIB.hwloc_topology_allow(topology, cpuset, nodeset, flags))


_LIB.hwloc_topology_insert_misc_object.argtypes = [topology_t, obj_t, ctypes.c_char_p]
_LIB.hwloc_topology_insert_misc_object.restype = obj_t


@_cfndoc
def topology_insert_misc_object(
    topology: topology_t, parent: ObjPtr, name: str
) -> ObjPtr | None:
    name_bytes = name.encode("utf-8")
    # null return can be caused by error and filter, how do we know which one is the
    # case?
    ctypes.set_errno(0)
    obj = _LIB.hwloc_topology_insert_misc_object(topology, parent, name_bytes)
    if not obj:
        err = ctypes.get_errno()
        if err != 0:
            _checkc(-1)
        return None
    return obj


_LIB.hwloc_topology_alloc_group_object.argtypes = [topology_t]
_LIB.hwloc_topology_alloc_group_object.restype = obj_t


@_cfndoc
def topology_alloc_group_object(topology: topology_t) -> ObjPtr:
    obj = _LIB.hwloc_topology_alloc_group_object(topology)
    if not obj:
        raise _hwloc_error("hwloc_topology_alloc_group_object")
    return obj


_LIB.hwloc_topology_free_group_object.argtypes = [topology_t, obj_t]
_LIB.hwloc_topology_free_group_object.restype = ctypes.c_int


@_cfndoc
def topology_free_group_object(topology: topology_t, group: ObjPtr) -> None:
    _checkc(_LIB.hwloc_topology_free_group_object(topology, group))


_LIB.hwloc_topology_insert_group_object.argtypes = [topology_t, obj_t]
_LIB.hwloc_topology_insert_group_object.restype = obj_t


@_cfndoc
def topology_insert_group_object(topology: topology_t, group: ObjPtr) -> ObjPtr | None:
    # fixme: null return can be caused by error and filter, how do we know which one is
    # the case?
    obj = _LIB.hwloc_topology_insert_group_object(topology, group)
    if not obj:
        return None
    return obj


_LIB.hwloc_obj_add_other_obj_sets.argtypes = [obj_t, obj_t]
_LIB.hwloc_obj_add_other_obj_sets.restype = ctypes.c_int


@_cfndoc
def obj_add_other_obj_sets(dst: ObjPtr, src: ObjPtr) -> None:
    _checkc(_LIB.hwloc_obj_add_other_obj_sets(dst, src))


_LIB.hwloc_topology_refresh.argtypes = [topology_t]
_LIB.hwloc_topology_refresh.restype = ctypes.c_int


@_cfndoc
def topology_refresh(topology: topology_t) -> None:
    _checkc(_LIB.hwloc_topology_refresh(topology))


######################
# Kinds of object Type
######################


# https://www.open-mpi.org/projects/hwloc/doc/v2.12.1/a00151.php


_LIB.hwloc_obj_type_is_normal.argtypes = [ctypes.c_int]
_LIB.hwloc_obj_type_is_normal.restype = ctypes.c_int


@_cfndoc
def obj_type_is_normal(obj_type: ObjType) -> bool:
    # For the definition of normal:
    # https://www.open-mpi.org/projects/hwloc/doc/v2.12.1/a00343.php
    return bool(_LIB.hwloc_obj_type_is_normal(int(obj_type)))


_LIB.hwloc_obj_type_is_io.argtypes = [ctypes.c_int]
_LIB.hwloc_obj_type_is_io.restype = ctypes.c_int


@_cfndoc
def obj_type_is_io(obj_type: ObjType) -> bool:
    return bool(_LIB.hwloc_obj_type_is_io(obj_type))


_LIB.hwloc_obj_type_is_memory.argtypes = [ctypes.c_int]
_LIB.hwloc_obj_type_is_memory.restype = ctypes.c_int


@_cfndoc
def obj_type_is_memory(obj_type: ObjType) -> bool:
    return bool(_LIB.hwloc_obj_type_is_memory(obj_type))


_LIB.hwloc_obj_type_is_cache.argtypes = [ctypes.c_int]
_LIB.hwloc_obj_type_is_cache.restype = ctypes.c_int


@_cfndoc
def obj_type_is_cache(obj_type: ObjType) -> bool:
    return bool(_LIB.hwloc_obj_type_is_cache(obj_type))


_LIB.hwloc_obj_type_is_dcache.argtypes = [ctypes.c_int]
_LIB.hwloc_obj_type_is_dcache.restype = ctypes.c_int


@_cfndoc
def obj_type_is_dcache(obj_type: ObjType) -> bool:
    return bool(_LIB.hwloc_obj_type_is_dcache(obj_type))


_LIB.hwloc_obj_type_is_icache.argtypes = [ctypes.c_int]
_LIB.hwloc_obj_type_is_icache.restype = ctypes.c_int


@_cfndoc
def obj_type_is_icache(obj_type: ObjType) -> bool:
    return bool(_LIB.hwloc_obj_type_is_icache(obj_type))


##################################
# Finding Objects inside a CPU set
##################################

_pyhwloc_lib.pyhwloc_get_first_largest_obj_inside_cpuset.argtypes = [
    topology_t,
    hwloc_const_cpuset_t,
]
_pyhwloc_lib.pyhwloc_get_first_largest_obj_inside_cpuset.restype = obj_t


@_cfndoc
def get_first_largest_obj_inside_cpuset(
    topology: topology_t, cpuset: hwloc_const_cpuset_t
) -> ObjPtr | None:
    obj = _pyhwloc_lib.pyhwloc_get_first_largest_obj_inside_cpuset(topology, cpuset)
    if not obj:
        return None
    return obj


_pyhwloc_lib.pyhwloc_get_largest_objs_inside_cpuset.argtypes = [
    topology_t,
    hwloc_const_cpuset_t,
    ctypes.POINTER(obj_t),
    ctypes.c_int,
]
_pyhwloc_lib.pyhwloc_get_largest_objs_inside_cpuset.restype = ctypes.c_int


@_cfndoc
def get_largest_objs_inside_cpuset(
    topology: topology_t,
    cpuset: hwloc_const_cpuset_t,
    objs: ctypes.Array,
    max_objs: int,
) -> int:
    return _pyhwloc_lib.pyhwloc_get_largest_objs_inside_cpuset(
        topology, cpuset, objs, max_objs
    )


_pyhwloc_lib.pyhwloc_get_next_obj_inside_cpuset_by_depth.argtypes = [
    topology_t,
    hwloc_const_cpuset_t,
    ctypes.c_int,
    obj_t,
]
_pyhwloc_lib.pyhwloc_get_next_obj_inside_cpuset_by_depth.restype = obj_t


@_cfndoc
def get_next_obj_inside_cpuset_by_depth(
    topology: topology_t, cpuset: hwloc_const_cpuset_t, depth: int, prev: ObjPtr
) -> ObjPtr | None:
    obj = _pyhwloc_lib.pyhwloc_get_next_obj_inside_cpuset_by_depth(
        topology, cpuset, depth, prev
    )
    if not obj:
        return None
    return obj


_pyhwloc_lib.pyhwloc_get_next_obj_inside_cpuset_by_type.argtypes = [
    topology_t,
    hwloc_const_cpuset_t,
    ctypes.c_int,
    obj_t,
]
_pyhwloc_lib.pyhwloc_get_next_obj_inside_cpuset_by_type.restype = obj_t


@_cfndoc
def get_next_obj_inside_cpuset_by_type(
    topology: topology_t,
    cpuset: hwloc_const_cpuset_t,
    obj_type: ObjType,
    prev: ObjPtr,
) -> ObjPtr | None:
    obj = _pyhwloc_lib.pyhwloc_get_next_obj_inside_cpuset_by_type(
        topology, cpuset, obj_type, prev
    )
    if not obj:
        return None
    return obj


_pyhwloc_lib.pyhwloc_get_obj_inside_cpuset_by_depth.argtypes = [
    topology_t,
    hwloc_const_cpuset_t,
    ctypes.c_int,
    ctypes.c_uint,
]
_pyhwloc_lib.pyhwloc_get_obj_inside_cpuset_by_depth.restype = obj_t


@_cfndoc
def get_obj_inside_cpuset_by_depth(
    topology: topology_t, cpuset: hwloc_const_cpuset_t, depth: int, idx: int
) -> ObjPtr | None:
    obj = _pyhwloc_lib.pyhwloc_get_obj_inside_cpuset_by_depth(
        topology, cpuset, depth, idx
    )
    if not obj:
        return None
    return obj


_pyhwloc_lib.pyhwloc_get_obj_inside_cpuset_by_type.argtypes = [
    topology_t,
    hwloc_const_cpuset_t,
    ctypes.c_int,
    ctypes.c_uint,
]
_pyhwloc_lib.pyhwloc_get_obj_inside_cpuset_by_type.restype = obj_t


@_cfndoc
def get_obj_inside_cpuset_by_type(
    topology: topology_t,
    cpuset: hwloc_const_cpuset_t,
    obj_type: ObjType,
    idx: int,
) -> ObjPtr | None:
    obj = _pyhwloc_lib.pyhwloc_get_obj_inside_cpuset_by_type(
        topology, cpuset, obj_type, idx
    )
    if not obj:
        return None
    return obj


_pyhwloc_lib.pyhwloc_get_nbobjs_inside_cpuset_by_depth.argtypes = [
    topology_t,
    hwloc_const_cpuset_t,
    ctypes.c_int,
]
_pyhwloc_lib.pyhwloc_get_nbobjs_inside_cpuset_by_depth.restype = ctypes.c_uint


@_cfndoc
def get_nbobjs_inside_cpuset_by_depth(
    topology: topology_t, cpuset: hwloc_const_cpuset_t, depth: int
) -> int:
    return _pyhwloc_lib.pyhwloc_get_nbobjs_inside_cpuset_by_depth(
        topology, cpuset, depth
    )


_pyhwloc_lib.pyhwloc_get_nbobjs_inside_cpuset_by_type.argtypes = [
    topology_t,
    hwloc_const_cpuset_t,
    ctypes.c_int,
]
_pyhwloc_lib.pyhwloc_get_nbobjs_inside_cpuset_by_type.restype = ctypes.c_int


@_cfndoc
def get_nbobjs_inside_cpuset_by_type(
    topology: topology_t, cpuset: hwloc_const_cpuset_t, obj_type: ObjType
) -> int:
    return _pyhwloc_lib.pyhwloc_get_nbobjs_inside_cpuset_by_type(
        topology, cpuset, obj_type
    )


_pyhwloc_lib.pyhwloc_get_obj_index_inside_cpuset.argtypes = [
    topology_t,
    hwloc_const_cpuset_t,
    obj_t,
]
_pyhwloc_lib.pyhwloc_get_obj_index_inside_cpuset.restype = ctypes.c_int


@_cfndoc
def get_obj_index_inside_cpuset(
    topology: topology_t, cpuset: hwloc_const_cpuset_t, obj: ObjPtr
) -> int:
    return _pyhwloc_lib.pyhwloc_get_obj_index_inside_cpuset(topology, cpuset, obj)


###########################################
# Finding Objects covering at least CPU set
###########################################

# https://www.open-mpi.org/projects/hwloc/doc/v2.12.1/a00153.php


_pyhwloc_lib.pyhwloc_get_child_covering_cpuset.argtypes = [
    topology_t,
    hwloc_const_cpuset_t,
    obj_t,
]
_pyhwloc_lib.pyhwloc_get_child_covering_cpuset.restype = obj_t


@_cfndoc
def get_child_covering_cpuset(
    topology: topology_t, cpuset: hwloc_const_cpuset_t, parent: ObjPtr
) -> ObjPtr | None:
    child_obj = _pyhwloc_lib.pyhwloc_get_child_covering_cpuset(topology, cpuset, parent)
    if not child_obj:
        return None
    return child_obj


_pyhwloc_lib.pyhwloc_get_obj_covering_cpuset.argtypes = [
    topology_t,
    hwloc_const_cpuset_t,
]
_pyhwloc_lib.pyhwloc_get_obj_covering_cpuset.restype = obj_t


@_cfndoc
def get_obj_covering_cpuset(
    topology: topology_t, cpuset: hwloc_const_cpuset_t
) -> ObjPtr | None:
    obj = _pyhwloc_lib.pyhwloc_get_obj_covering_cpuset(topology, cpuset)
    if not obj:
        return None
    return obj


_pyhwloc_lib.pyhwloc_get_next_obj_covering_cpuset_by_depth.argtypes = [
    topology_t,
    hwloc_const_cpuset_t,
    ctypes.c_int,
    obj_t,
]
_pyhwloc_lib.pyhwloc_get_next_obj_covering_cpuset_by_depth.restype = obj_t


@_cfndoc
def get_next_obj_covering_cpuset_by_depth(
    topology: topology_t, cpuset: hwloc_const_cpuset_t, depth: int, prev: ObjPtr
) -> ObjPtr | None:
    obj = _pyhwloc_lib.pyhwloc_get_next_obj_covering_cpuset_by_depth(
        topology, cpuset, depth, prev
    )
    if not obj:
        return None
    return obj


_pyhwloc_lib.pyhwloc_get_next_obj_covering_cpuset_by_type.argtypes = [
    topology_t,
    hwloc_const_cpuset_t,
    ctypes.c_int,
    obj_t,
]
_pyhwloc_lib.pyhwloc_get_next_obj_covering_cpuset_by_type.restype = obj_t


@_cfndoc
def get_next_obj_covering_cpuset_by_type(
    topology: topology_t,
    cpuset: hwloc_const_cpuset_t,
    obj_type: ObjType,
    prev: ObjPtr,
) -> ObjPtr | None:
    obj = _pyhwloc_lib.pyhwloc_get_next_obj_covering_cpuset_by_type(
        topology, cpuset, obj_type, prev
    )
    if not obj:
        return None
    return obj


#######################################
# Looking at Ancestor and Child Objects
#######################################

# https://www.open-mpi.org/projects/hwloc/doc/v2.12.1/a00154.php


_pyhwloc_lib.pyhwloc_get_ancestor_obj_by_depth.argtypes = [
    topology_t,
    ctypes.c_int,
    obj_t,
]
_pyhwloc_lib.pyhwloc_get_ancestor_obj_by_depth.restype = obj_t


@_cfndoc
def get_ancestor_obj_by_depth(
    topology: topology_t, depth: int, obj: ObjPtr
) -> ObjPtr | None:
    obj = _pyhwloc_lib.pyhwloc_get_ancestor_obj_by_depth(topology, depth, obj)
    if not obj:
        return None
    return obj


_pyhwloc_lib.pyhwloc_get_ancestor_obj_by_type.argtypes = [
    topology_t,
    ctypes.c_int,
    obj_t,
]
_pyhwloc_lib.pyhwloc_get_ancestor_obj_by_type.restype = obj_t


@_cfndoc
def get_ancestor_obj_by_type(
    topology: topology_t, obj_type: ObjType, obj: ObjPtr
) -> ObjPtr | None:
    obj = _pyhwloc_lib.pyhwloc_get_ancestor_obj_by_type(topology, obj_type, obj)
    if not obj:
        return None
    return obj


_pyhwloc_lib.pyhwloc_get_common_ancestor_obj.argtypes = [
    topology_t,
    obj_t,
    obj_t,
]
_pyhwloc_lib.pyhwloc_get_common_ancestor_obj.restype = obj_t


@_cfndoc
def get_common_ancestor_obj(topology: topology_t, obj1: ObjPtr, obj2: ObjPtr) -> ObjPtr:
    # This function cannot return NULL.
    if not obj1 or not obj2:
        raise ValueError("null object.")
    return _pyhwloc_lib.pyhwloc_get_common_ancestor_obj(topology, obj1, obj2)


_pyhwloc_lib.pyhwloc_obj_is_in_subtree.argtypes = [
    topology_t,
    obj_t,
    obj_t,
]
_pyhwloc_lib.pyhwloc_obj_is_in_subtree.restype = ctypes.c_int


@_cfndoc
def obj_is_in_subtree(topology: topology_t, obj: ObjPtr, subtree_root: ObjPtr) -> bool:
    result = _pyhwloc_lib.pyhwloc_obj_is_in_subtree(topology, obj, subtree_root)
    return bool(result)


_pyhwloc_lib.pyhwloc_get_next_child.argtypes = [
    topology_t,
    obj_t,
    obj_t,
]
_pyhwloc_lib.pyhwloc_get_next_child.restype = obj_t


@_cfndoc
def get_next_child(
    topology: topology_t, parent: ObjPtr, prev: ObjPtr | None
) -> ObjPtr | None:
    child_obj = _pyhwloc_lib.pyhwloc_get_next_child(topology, parent, prev)
    if not child_obj:
        return None
    return child_obj


##########################
# Looking at Cache Objects
##########################


# https://www.open-mpi.org/projects/hwloc/doc/v2.12.1/a00155.php


_pyhwloc_lib.pyhwloc_get_cache_type_depth.argtypes = [
    topology_t,
    ctypes.c_uint,
    ctypes.c_int,
]
_pyhwloc_lib.pyhwloc_get_cache_type_depth.restype = ctypes.c_int


@_cfndoc
def get_cache_type_depth(
    topology: topology_t, cachelevel: int, cachetype: hwloc_obj_cache_type_t
) -> int:
    # This can return HWLOC_TYPE_DEPTH_UNKNOWN (-1) and HWLOC_TYPE_DEPTH_MULTIPLE (-2)
    return _pyhwloc_lib.pyhwloc_get_cache_type_depth(topology, cachelevel, cachetype)


_pyhwloc_lib.pyhwloc_get_cache_covering_cpuset.argtypes = [
    topology_t,
    hwloc_const_cpuset_t,
]
_pyhwloc_lib.pyhwloc_get_cache_covering_cpuset.restype = obj_t


@_cfndoc
def get_cache_covering_cpuset(
    topology: topology_t, cpuset: hwloc_const_cpuset_t
) -> ObjPtr | None:
    obj = _pyhwloc_lib.pyhwloc_get_cache_covering_cpuset(topology, cpuset)
    if not obj:
        return None
    return obj


_pyhwloc_lib.pyhwloc_get_shared_cache_covering_obj.argtypes = [topology_t, obj_t]
_pyhwloc_lib.pyhwloc_get_shared_cache_covering_obj.restype = obj_t


@_cfndoc
def get_shared_cache_covering_obj(topology: topology_t, obj: ObjPtr) -> ObjPtr | None:
    robj = _pyhwloc_lib.pyhwloc_get_shared_cache_covering_obj(topology, obj)
    if not robj:
        return None
    return robj


########################################
# Finding objects, miscellaneous helpers
########################################


# https://www.open-mpi.org/projects/hwloc/doc/v2.12.1/a00156.php


_pyhwloc_lib.pyhwloc_bitmap_singlify_per_core.argtypes = [
    topology_t,
    bitmap_t,
    ctypes.c_uint,
]
_pyhwloc_lib.pyhwloc_bitmap_singlify_per_core.restype = ctypes.c_int


@_cfndoc
def bitmap_singlify_per_core(
    topology: topology_t, cpuset: bitmap_t, which: int
) -> None:
    _checkc(_pyhwloc_lib.pyhwloc_bitmap_singlify_per_core(topology, cpuset, which))


_pyhwloc_lib.pyhwloc_get_pu_obj_by_os_index.argtypes = [topology_t, ctypes.c_uint]
_pyhwloc_lib.pyhwloc_get_pu_obj_by_os_index.restype = obj_t


@_cfndoc
def get_pu_obj_by_os_index(topology: topology_t, os_index: int) -> ObjPtr | None:
    obj = _pyhwloc_lib.pyhwloc_get_pu_obj_by_os_index(topology, os_index)
    if not obj:
        return None
    return obj


_pyhwloc_lib.pyhwloc_get_numanode_obj_by_os_index.argtypes = [topology_t, ctypes.c_uint]
_pyhwloc_lib.pyhwloc_get_numanode_obj_by_os_index.restype = obj_t


@_cfndoc
def get_numanode_obj_by_os_index(topology: topology_t, os_index: int) -> ObjPtr | None:
    obj = _pyhwloc_lib.pyhwloc_get_numanode_obj_by_os_index(topology, os_index)
    if not obj:
        return None
    return obj


_pyhwloc_lib.pyhwloc_get_closest_objs.argtypes = [
    topology_t,
    obj_t,
    ctypes.POINTER(obj_t),
    ctypes.c_uint,
]
_pyhwloc_lib.pyhwloc_get_closest_objs.restype = ctypes.c_uint


@_cfndoc
def get_closest_objs(
    topology: topology_t, src: ObjPtr, objs: ctypes.Array, max_objs: int
) -> int:
    return _pyhwloc_lib.pyhwloc_get_closest_objs(topology, src, objs, max_objs)


_pyhwloc_lib.pyhwloc_get_obj_below_by_type.argtypes = [
    topology_t,
    ctypes.c_int,
    ctypes.c_uint,
    ctypes.c_int,
    ctypes.c_uint,
]
_pyhwloc_lib.pyhwloc_get_obj_below_by_type.restype = obj_t


@_cfndoc
def get_obj_below_by_type(
    topology: topology_t,
    type1: ObjType,
    idx1: int,
    type2: ObjType,
    idx2: int,
) -> ObjPtr | None:
    obj = _pyhwloc_lib.pyhwloc_get_obj_below_by_type(topology, type1, idx1, type2, idx2)
    if not obj:
        return None
    return obj


_pyhwloc_lib.pyhwloc_get_obj_below_array_by_type.argtypes = [
    topology_t,
    ctypes.c_int,
    ctypes.POINTER(ctypes.c_int),
    ctypes.POINTER(ctypes.c_uint),
]
_pyhwloc_lib.pyhwloc_get_obj_below_array_by_type.restype = obj_t


@_cfndoc
def get_obj_below_array_by_type(
    topology: topology_t,
    nr: int,
    typev: ctypes.Array,
    idxv: ctypes.Array,
) -> ObjPtr | None:
    obj = _pyhwloc_lib.pyhwloc_get_obj_below_array_by_type(topology, nr, typev, idxv)
    if not obj:
        return None
    return obj


_pyhwloc_lib.pyhwloc_get_obj_with_same_locality.argtypes = [
    topology_t,
    obj_t,
    ctypes.c_int,
    ctypes.c_char_p,
    ctypes.c_char_p,
    ctypes.c_ulong,
]
_pyhwloc_lib.pyhwloc_get_obj_with_same_locality.restype = obj_t


@_cfndoc
def get_obj_with_same_locality(
    topology: topology_t,
    src: ObjPtr,
    obj_type: ObjType,
    subtype: str | None,
    nameprefix: str | None,
    flags: int,
) -> ObjPtr | None:
    subtype_bytes = subtype.encode("utf-8") if subtype else None
    nameprefix_bytes = nameprefix.encode("utf-8") if nameprefix else None
    obj = _pyhwloc_lib.pyhwloc_get_obj_with_same_locality(
        topology, src, obj_type, subtype_bytes, nameprefix_bytes, flags
    )
    if not obj:
        return None
    return obj


####################################
# Distributing items over a topology
####################################

# https://www.open-mpi.org/projects/hwloc/doc/v2.12.0/a00157.php


@_cenumdoc("hwloc_allow_flags_e")
class DistribFlags(IntEnum):
    REVERSE = 1 << 0


_pyhwloc_lib.pyhwloc_distrib.argtypes = [
    topology_t,
    ctypes.POINTER(obj_t),
    ctypes.c_uint,
    ctypes.POINTER(hwloc_cpuset_t),
    ctypes.c_uint,
    ctypes.c_int,
    ctypes.c_ulong,
]
_pyhwloc_lib.pyhwloc_distrib.restype = ctypes.c_int


@_cfndoc
def distrib(
    topology: topology_t,
    roots: ctypes._Pointer,  # Pointer[obj_t]
    n_roots: int,
    cpuset: ctypes._Pointer,  # Pointer[hwloc_cpuset_t]
    n: int,
    until: int,
    flags: int,
) -> None:
    _checkc(
        _pyhwloc_lib.pyhwloc_distrib(topology, roots, n_roots, cpuset, n, until, flags)
    )


########################################
# CPU and node sets of entire topologies
########################################

# https://www.open-mpi.org/projects/hwloc/doc/v2.12.1/a00158.php

_LIB.hwloc_topology_get_complete_cpuset.argtypes = [topology_t]
_LIB.hwloc_topology_get_complete_cpuset.restype = hwloc_const_cpuset_t


@_cfndoc
def topology_get_complete_cpuset(topology: topology_t) -> hwloc_const_cpuset_t:
    # No need for free.
    return _LIB.hwloc_topology_get_complete_cpuset(topology)


_LIB.hwloc_topology_get_topology_cpuset.argtypes = [topology_t]
_LIB.hwloc_topology_get_topology_cpuset.restype = hwloc_const_cpuset_t


@_cfndoc
def topology_get_topology_cpuset(topology: topology_t) -> hwloc_const_cpuset_t:
    return _LIB.hwloc_topology_get_topology_cpuset(topology)


_LIB.hwloc_topology_get_allowed_cpuset.argtypes = [topology_t]
_LIB.hwloc_topology_get_allowed_cpuset.restype = hwloc_const_cpuset_t


@_cfndoc
def topology_get_allowed_cpuset(topology: topology_t) -> hwloc_const_cpuset_t:
    return _LIB.hwloc_topology_get_allowed_cpuset(topology)


_LIB.hwloc_topology_get_complete_nodeset.argtypes = [topology_t]
_LIB.hwloc_topology_get_complete_nodeset.restype = hwloc_const_nodeset_t


@_cfndoc
def topology_get_complete_nodeset(topology: topology_t) -> hwloc_const_nodeset_t:
    return _LIB.hwloc_topology_get_complete_nodeset(topology)


_LIB.hwloc_topology_get_topology_nodeset.argtypes = [topology_t]
_LIB.hwloc_topology_get_topology_nodeset.restype = hwloc_const_nodeset_t


@_cfndoc
def topology_get_topology_nodeset(topology: topology_t) -> hwloc_const_nodeset_t:
    return _LIB.hwloc_topology_get_topology_nodeset(topology)


_LIB.hwloc_topology_get_allowed_nodeset.argtypes = [topology_t]
_LIB.hwloc_topology_get_allowed_nodeset.restype = hwloc_const_nodeset_t


@_cfndoc
def topology_get_allowed_nodeset(topology: topology_t) -> hwloc_const_nodeset_t:
    return _LIB.hwloc_topology_get_allowed_nodeset(topology)


###########################################
# Converting between CPU sets and node sets
###########################################

# https://www.open-mpi.org/projects/hwloc/doc/v2.12.1/a00159.php


_pyhwloc_lib.pyhwloc_cpuset_to_nodeset.argtypes = [
    topology_t,
    hwloc_const_cpuset_t,
    hwloc_nodeset_t,
]
_pyhwloc_lib.pyhwloc_cpuset_to_nodeset.restype = ctypes.c_int


@_cfndoc
def cpuset_to_nodeset(
    topology: topology_t, cpuset: hwloc_const_cpuset_t, nodeset: hwloc_nodeset_t
) -> None:
    _checkc(_pyhwloc_lib.pyhwloc_cpuset_to_nodeset(topology, cpuset, nodeset))


_pyhwloc_lib.pyhwloc_cpuset_from_nodeset.argtypes = [
    topology_t,
    hwloc_cpuset_t,
    hwloc_const_nodeset_t,
]
_pyhwloc_lib.pyhwloc_cpuset_from_nodeset.restype = ctypes.c_int


@_cfndoc
def cpuset_from_nodeset(
    topology: topology_t, cpuset: hwloc_cpuset_t, nodeset: hwloc_const_nodeset_t
) -> None:
    _checkc(_pyhwloc_lib.pyhwloc_cpuset_from_nodeset(topology, cpuset, nodeset))


#####################
# Finding I/O objects
#####################

# https://www.open-mpi.org/projects/hwloc/doc/v2.12.1/a00160.php


_pyhwloc_lib.pyhwloc_get_non_io_ancestor_obj.argtypes = [
    topology_t,
    obj_t,
]
_pyhwloc_lib.pyhwloc_get_non_io_ancestor_obj.restype = obj_t


@_cfndoc
def get_non_io_ancestor_obj(topology: topology_t, ioobj: ObjPtr) -> ObjPtr:
    # This function cannot return NULL.
    return _pyhwloc_lib.pyhwloc_get_non_io_ancestor_obj(topology, ioobj)


_pyhwloc_lib.pyhwloc_get_next_pcidev.argtypes = [topology_t, obj_t]
_pyhwloc_lib.pyhwloc_get_next_pcidev.restype = obj_t


@_cfndoc
def get_next_pcidev(topology: topology_t, prev: ObjPtr | None) -> ObjPtr | None:
    obj = _pyhwloc_lib.pyhwloc_get_next_pcidev(topology, prev)
    if not obj:
        return None
    return obj


_pyhwloc_lib.pyhwloc_get_pcidev_by_busid.argtypes = [
    topology_t,
    ctypes.c_uint,
    ctypes.c_uint,
    ctypes.c_uint,
    ctypes.c_uint,
]
_pyhwloc_lib.pyhwloc_get_pcidev_by_busid.restype = obj_t


@_cfndoc
def get_pcidev_by_busid(
    topology: topology_t, domain: int, bus: int, dev: int, func: int
) -> ObjPtr | None:
    obj = _pyhwloc_lib.pyhwloc_get_pcidev_by_busid(topology, domain, bus, dev, func)
    if not obj:
        return None
    return obj


_pyhwloc_lib.pyhwloc_get_pcidev_by_busidstring.argtypes = [topology_t, ctypes.c_char_p]
_pyhwloc_lib.pyhwloc_get_pcidev_by_busidstring.restype = obj_t


@_cfndoc
def get_pcidev_by_busidstring(topology: topology_t, busid: str) -> ObjPtr | None:
    obj = _pyhwloc_lib.pyhwloc_get_pcidev_by_busidstring(
        topology, busid.encode("utf-8")
    )
    if not obj:
        return None
    return obj


_pyhwloc_lib.pyhwloc_get_next_osdev.argtypes = [topology_t, obj_t]
_pyhwloc_lib.pyhwloc_get_next_osdev.restype = obj_t


@_cfndoc
def get_next_osdev(topology: topology_t, prev: ObjPtr | None) -> ObjPtr | None:
    obj = _pyhwloc_lib.pyhwloc_get_next_osdev(topology, prev)
    if not obj:
        return None
    return obj


_pyhwloc_lib.pyhwloc_get_next_bridge.argtypes = [topology_t, obj_t]
_pyhwloc_lib.pyhwloc_get_next_bridge.restype = obj_t


@_cfndoc
def get_next_bridge(topology: topology_t, prev: ObjPtr | None) -> ObjPtr | None:
    obj = _pyhwloc_lib.pyhwloc_get_next_bridge(topology, prev)
    if not obj:
        return None
    return obj


_pyhwloc_lib.pyhwloc_bridge_covers_pcibus.argtypes = [
    obj_t,
    ctypes.c_uint,
    ctypes.c_uint,
]
_pyhwloc_lib.pyhwloc_bridge_covers_pcibus.restype = ctypes.c_int


@_cfndoc
def bridge_covers_pcibus(bridge: ObjPtr, domain: int, bus: int) -> int:
    return _pyhwloc_lib.pyhwloc_bridge_covers_pcibus(bridge, domain, bus)


#############################
# Exporting Topologies to XML
#############################


if _IS_V3:

    @_cenumdoc("hwloc_topology_export_xml_flags_e")
    class ExportXmlFlags(IntEnum):
        V2 = 1 << 1

else:

    @_cenumdoc("hwloc_topology_export_xml_flags_e")
    class ExportXmlFlags(IntEnum):  # type: ignore[no-redef]
        V1 = 1 << 0


_LIB.hwloc_topology_export_xml.argtypes = [topology_t, ctypes.c_char_p, ctypes.c_ulong]
_LIB.hwloc_topology_export_xml.restype = ctypes.c_int


@_cfndoc
def topology_export_xml(topology: topology_t, xmlpath: str, flags: int) -> None:
    _checkc(_LIB.hwloc_topology_export_xml(topology, xmlpath.encode("utf-8"), flags))


_LIB.hwloc_topology_export_xmlbuffer.argtypes = [
    topology_t,
    ctypes.POINTER(ctypes.c_char_p),
    ctypes.POINTER(ctypes.c_int),
    ctypes.c_ulong,
]
_LIB.hwloc_topology_export_xmlbuffer.restype = ctypes.c_int


@_cfndoc
def topology_export_xmlbuffer(topology: topology_t, flags: int) -> str:
    xmlbuffer = ctypes.c_char_p()
    buflen = ctypes.c_int()
    _checkc(
        _LIB.hwloc_topology_export_xmlbuffer(
            topology, ctypes.byref(xmlbuffer), ctypes.byref(buflen), flags
        )
    )
    result = xmlbuffer.value.decode("utf-8") if xmlbuffer.value else ""
    _free_xmlbuffer(topology, xmlbuffer)
    return result


_LIB.hwloc_free_xmlbuffer.argtypes = [topology_t, ctypes.c_char_p]
_LIB.hwloc_free_xmlbuffer.restype = None


# This function is only used internally since we return python strings.
def _free_xmlbuffer(topology: topology_t, xmlbuffer: ctypes.c_char_p) -> None:
    _LIB.hwloc_free_xmlbuffer(topology, xmlbuffer)


export_callback_t = ctypes.CFUNCTYPE(None, ctypes.c_void_p, topology_t, obj_t)

_LIB.hwloc_topology_set_userdata_export_callback.argtypes = [
    topology_t,
    export_callback_t,
]
_LIB.hwloc_topology_set_userdata_export_callback.restype = None


@_cfndoc
def topology_set_userdata_export_callback(
    topology: topology_t, export_cb: Callable
) -> None:
    _LIB.hwloc_topology_set_userdata_export_callback(topology, export_cb)


_LIB.hwloc_export_obj_userdata.argtypes = [
    ctypes.c_void_p,
    topology_t,
    obj_t,
    ctypes.c_char_p,
    ctypes.c_void_p,
    ctypes.c_size_t,
]
_LIB.hwloc_export_obj_userdata.restype = ctypes.c_int


@_cfndoc
def export_obj_userdata(
    reserved: ctypes.c_void_p,
    topology: topology_t,
    obj: ObjPtr,
    name: str,
    buf: ctypes.c_void_p,
    length: int,
) -> None:
    _checkc(
        _LIB.hwloc_export_obj_userdata(
            reserved, topology, obj, name.encode("utf-8"), buf, length
        )
    )


_LIB.hwloc_export_obj_userdata_base64.argtypes = [
    ctypes.c_void_p,
    topology_t,
    obj_t,
    ctypes.c_char_p,
    ctypes.c_void_p,
    ctypes.c_size_t,
]
_LIB.hwloc_export_obj_userdata_base64.restype = ctypes.c_int


@_cfndoc
def export_obj_userdata_base64(
    reserved: ctypes.c_void_p,
    topology: topology_t,
    obj: ObjPtr,
    name: str,
    buffer: ctypes.c_void_p,
    length: int,
) -> None:
    _checkc(
        _LIB.hwloc_export_obj_userdata_base64(
            reserved, topology, obj, name.encode("utf-8"), buffer, length
        )
    )


import_callback_t = ctypes.CFUNCTYPE(
    None,
    topology_t,
    obj_t,
    ctypes.c_char_p,
    ctypes.c_void_p,
    ctypes.c_size_t,
)

_LIB.hwloc_topology_set_userdata_import_callback.argtypes = [
    topology_t,
    import_callback_t,
]
_LIB.hwloc_topology_set_userdata_import_callback.restype = None


@_cfndoc
def topology_set_userdata_import_callback(
    topology: topology_t, import_cb: Callable
) -> None:
    _LIB.hwloc_topology_set_userdata_import_callback(topology, import_cb)


###################################
# Exporting Topologies to Synthetic
###################################

# https://www.open-mpi.org/projects/hwloc/doc/v2.12.1/a00163.php


if _IS_V3:

    @_cenumdoc("hwloc_topology_export_synthetic_flags_e")
    class ExportSyntheticFlags(IntEnum):
        NO_EXTENDED_TYPES = 1 << 0
        NO_ATTRS = 1 << 1
        IGNORE_MEMORY = 1 << 2

else:

    @_cenumdoc("hwloc_topology_export_synthetic_flags_e")
    class ExportSyntheticFlags(IntEnum):  # type: ignore[no-redef]
        NO_EXTENDED_TYPES = 1 << 0
        NO_ATTRS = 1 << 1
        V1 = 1 << 2
        IGNORE_MEMORY = 1 << 3


_LIB.hwloc_topology_export_synthetic.argtypes = [
    topology_t,
    ctypes.c_char_p,
    ctypes.c_size_t,
    ctypes.c_ulong,
]
_LIB.hwloc_topology_export_synthetic.restype = ctypes.c_int


@_cfndoc
def topology_export_synthetic(
    topology: topology_t,
    buf: ctypes.c_char_p | ctypes.Array,
    buflen: int,
    flags: int,
) -> int:
    # A 1024-byte buffer should be large enough for exporting topologies in the vast
    # majority of cases.
    n_written = _LIB.hwloc_topology_export_synthetic(topology, buf, buflen, flags)
    if n_written == -1:
        raise _hwloc_error("hwloc_topology_export_synthetic")
    return n_written


####################################
# Retrieve distances between objects
####################################

# https://www.open-mpi.org/projects/hwloc/doc/v2.12.0/a00164.php


@_cenumdoc("hwloc_distances_kind_e")
class DistancesKind(IntEnum):
    FROM_OS = 1 << 0
    FROM_USER = 1 << 1
    VALUE_LATENCY = 1 << 2
    VALUE_BANDWIDTH = 1 << 3
    HETEROGENEOUS_TYPES = 1 << 4
    VALUE_HOPS = 1 << 5


@_cenumdoc("hwloc_distances_transform_e")
class DistancesTransform(IntEnum):
    REMOVE_NULL = 0
    LINKS = 1
    MERGE_SWITCH_PORTS = 2
    TRANSITIVE_CLOSURE = 3


@_cstructdoc("hwloc_distances_s")
class Distances(_PrintableStruct):
    _fields_ = [
        ("nbobjs", ctypes.c_uint),
        ("objs", ctypes.POINTER(obj_t)),
        ("kind", ctypes.c_ulong),
        ("values", ctypes.POINTER(hwloc_uint64_t)),
    ]


_LIB.hwloc_distances_get.argtypes = [
    topology_t,
    ctypes.POINTER(ctypes.c_uint),
    ctypes.POINTER(ctypes.POINTER(Distances)),
    ctypes.c_ulong,
    ctypes.c_ulong,
]
_LIB.hwloc_distances_get.restype = ctypes.c_int


if TYPE_CHECKING:
    DistancesPtr = ctypes._Pointer[Distances]
    DistancesPtrPtr = (
        ctypes._Pointer[ctypes._Pointer[Distances]]
        | ctypes._CArgObject
        | ctypes.Array[ctypes._Pointer[Distances]]
        | None
    )
    UintPtr = ctypes._Pointer[ctypes.c_uint] | ctypes._CArgObject
else:
    DistancesPtr = ctypes._Pointer
    DistancesPtrPtr = ctypes._Pointer
    UintPtr = ctypes._Pointer


@_cfndoc
def distances_get(
    topology: topology_t,
    nr: UintPtr,
    distances: DistancesPtrPtr,
    kind: int,
) -> None:
    # flag must be 0 for now.
    _checkc(_LIB.hwloc_distances_get(topology, nr, distances, kind, 0))


_LIB.hwloc_distances_get_by_depth.argtypes = [
    topology_t,
    ctypes.c_int,
    ctypes.POINTER(ctypes.c_uint),
    ctypes.POINTER(ctypes.POINTER(Distances)),
    ctypes.c_ulong,
    ctypes.c_ulong,
]
_LIB.hwloc_distances_get_by_depth.restype = ctypes.c_int


@_cfndoc
def distances_get_by_depth(
    topology: topology_t,
    depth: int,
    nr: UintPtr,
    distances: DistancesPtrPtr,
    kind: int,
    flags: int,
) -> None:
    _checkc(
        _LIB.hwloc_distances_get_by_depth(topology, depth, nr, distances, kind, flags)
    )


_LIB.hwloc_distances_get_by_type.argtypes = [
    topology_t,
    ctypes.c_int,
    ctypes.POINTER(ctypes.c_uint),
    ctypes.POINTER(ctypes.POINTER(Distances)),
    ctypes.c_ulong,
    ctypes.c_ulong,
]
_LIB.hwloc_distances_get_by_type.restype = ctypes.c_int


@_cfndoc
def distances_get_by_type(
    topology: topology_t,
    obj_type: ObjType,
    nr: UintPtr,  # this is both input and output
    distances: DistancesPtrPtr,
    kind: int,
) -> None:
    # flags must be 0 for now
    _checkc(
        _LIB.hwloc_distances_get_by_type(topology, obj_type, nr, distances, kind, 0)
    )


_LIB.hwloc_distances_get_by_name.argtypes = [
    topology_t,
    ctypes.c_char_p,
    ctypes.POINTER(ctypes.c_uint),
    ctypes.POINTER(ctypes.POINTER(Distances)),
    ctypes.c_ulong,
]
_LIB.hwloc_distances_get_by_name.restype = ctypes.c_int


@_cfndoc
def distances_get_by_name(
    topology: topology_t,
    name: bytes,
    nr: UintPtr,
    distances: DistancesPtrPtr,
    flags: int,
) -> None:
    _checkc(_LIB.hwloc_distances_get_by_name(topology, name, nr, distances, flags))


_LIB.hwloc_distances_get_name.argtypes = [
    topology_t,
    ctypes.POINTER(Distances),
]
_LIB.hwloc_distances_get_name.restype = ctypes.c_char_p


@_cfndoc
def distances_get_name(topology: topology_t, distances: DistancesPtr) -> str | None:
    result = _LIB.hwloc_distances_get_name(topology, distances)
    if result:
        return result.decode("utf-8")
    return None


_LIB.hwloc_distances_release.argtypes = [
    topology_t,
    ctypes.POINTER(Distances),
]
_LIB.hwloc_distances_release.restype = None


@_cfndoc
def distances_release(topology: topology_t, distances: DistancesPtr) -> None:
    _LIB.hwloc_distances_release(topology, distances)


_LIB.hwloc_distances_transform.argtypes = [
    topology_t,
    ctypes.POINTER(Distances),
    ctypes.c_int,  # DistancesTransform
    ctypes.c_void_p,
    ctypes.c_ulong,
]
_LIB.hwloc_distances_transform.restype = ctypes.c_int


@_cfndoc
def distances_transform(
    topology: topology_t,
    distances: DistancesPtr,
    transform: DistancesTransform,
    transform_attr: ctypes.c_void_p,
    flags: int,
) -> None:
    _checkc(
        _LIB.hwloc_distances_transform(
            topology, distances, transform, transform_attr, flags
        )
    )


##########################################
# Helpers for consulting distance matrices
##########################################

# https://www.open-mpi.org/projects/hwloc/doc/v2.12.0/a00165.php

_pyhwloc_lib.pyhwloc_distances_obj_index.argtypes = [
    ctypes.POINTER(Distances),
    obj_t,
]
_pyhwloc_lib.pyhwloc_distances_obj_index.restype = ctypes.c_int


@_cfndoc
def distances_obj_index(distances: DistancesPtr, obj: ObjPtr) -> int:
    # Returns -1 if not found
    return _pyhwloc_lib.pyhwloc_distances_obj_index(distances, obj)


_pyhwloc_lib.pyhwloc_distances_obj_pair_values.argtypes = [
    ctypes.POINTER(Distances),
    obj_t,
    obj_t,
    ctypes.POINTER(hwloc_uint64_t),
    ctypes.POINTER(hwloc_uint64_t),
]
_pyhwloc_lib.pyhwloc_distances_obj_pair_values.restype = ctypes.c_int


@_cfndoc
def distances_obj_pair_values(
    distances: DistancesPtr,
    obj1: ObjPtr,
    obj2: ObjPtr,
) -> tuple[int, int]:
    value1to2 = ctypes.c_uint64(0)
    value2to1 = ctypes.c_uint64(0)
    rc = _pyhwloc_lib.pyhwloc_distances_obj_pair_values(
        distances, obj1, obj2, ctypes.byref(value1to2), ctypes.byref(value2to1)
    )
    if rc == -1:
        raise ValueError("obj1 or obj2 is not involved in the distances structure.")
    _checkc(rc)
    return int(value1to2.value), int(value2to1.value)


###############################
# Add distances between objects
###############################

# https://www.open-mpi.org/projects/hwloc/doc/v2.12.0/a00166.php

# This is an opaque pointer of hwloc_internal_distances_s
# FIXME(jiamingy): How to make sure this is not leaked?
hwloc_distances_add_handle_t = ctypes.c_void_p


@_cenumdoc("hwloc_distances_add_flag_e")
class DistancesAddFlag(IntEnum):
    GROUP = 1 << 0
    GROUP_INACCURATE = 1 << 1


_LIB.hwloc_distances_add_create.argtypes = [
    topology_t,
    ctypes.c_char_p,
    ctypes.c_ulong,
    ctypes.c_ulong,
]
_LIB.hwloc_distances_add_create.restype = hwloc_distances_add_handle_t


@_cfndoc
def distances_add_create(
    topology: topology_t, name: str, kind: int
) -> hwloc_distances_add_handle_t:
    # The distance from object i to object j is in slot i*nbobjs+j. (row-major)
    name_bytes = name.encode("utf-8")
    # flags must be 0 for now
    dist_obj = _LIB.hwloc_distances_add_create(topology, name_bytes, kind, 0)
    if not dist_obj:
        raise _hwloc_error("hwloc_distances_add_create")
    return dist_obj


_LIB.hwloc_distances_add_values.argtypes = [
    topology_t,
    hwloc_distances_add_handle_t,
    ctypes.c_uint,
    ctypes.POINTER(obj_t),
    ctypes.POINTER(hwloc_uint64_t),
    ctypes.c_ulong,
]
_LIB.hwloc_distances_add_values.restype = ctypes.c_int


@_cfndoc
def distances_add_values(
    topology: topology_t,
    handle: hwloc_distances_add_handle_t,
    nbobjs: int,
    objs: ctypes.Array,
    values: ctypes.Array,
) -> None:
    # flags must be 0 for now
    _checkc(_LIB.hwloc_distances_add_values(topology, handle, nbobjs, objs, values, 0))


_LIB.hwloc_distances_add_commit.argtypes = [
    topology_t,
    hwloc_distances_add_handle_t,
    ctypes.c_ulong,
]
_LIB.hwloc_distances_add_commit.restype = ctypes.c_int


@_cfndoc
def distances_add_commit(
    topology: topology_t, handle: hwloc_distances_add_handle_t, flags: int
) -> None:
    _checkc(_LIB.hwloc_distances_add_commit(topology, handle, flags))


##################################
# Remove distances between objects
##################################

# https://www.open-mpi.org/projects/hwloc/doc/v2.12.0/a00167.php

_LIB.hwloc_distances_remove.argtypes = [topology_t]
_LIB.hwloc_distances_remove.restype = ctypes.c_int


@_cfndoc
def distances_remove(topology: topology_t) -> None:
    _checkc(_LIB.hwloc_distances_remove(topology))


_LIB.hwloc_distances_remove_by_depth.argtypes = [topology_t, ctypes.c_int]
_LIB.hwloc_distances_remove_by_depth.restype = ctypes.c_int


@_cfndoc
def distances_remove_by_depth(topology: topology_t, depth: int) -> None:
    _checkc(_LIB.hwloc_distances_remove_by_depth(topology, depth))


_pyhwloc_lib.pyhwloc_distances_remove_by_type.argtypes = [topology_t, ctypes.c_int]
_pyhwloc_lib.pyhwloc_distances_remove_by_type.restype = ctypes.c_int


@_cfndoc
def distances_remove_by_type(topology: topology_t, obj_type: ObjType) -> None:
    _checkc(_pyhwloc_lib.pyhwloc_distances_remove_by_type(topology, obj_type))


_LIB.hwloc_distances_release_remove.argtypes = [
    topology_t,
    ctypes.POINTER(Distances),
]
_LIB.hwloc_distances_release_remove.restype = ctypes.c_int


@_cfndoc
def distances_release_remove(topology: topology_t, distances: DistancesPtr) -> None:
    _checkc(_LIB.hwloc_distances_release_remove(topology, distances))


###################################################################
# Comparing memory node attributes for finding where to allocate on
###################################################################

# https://www.open-mpi.org/projects/hwloc/doc/v2.12.0/a00168.php

hwloc_memattr_id_t = ctypes.c_uint


@_cenumdoc("hwloc_memattr_id_e")
class MemAttrId(IntEnum):
    CAPACITY = 0
    LOCALITY = 1
    BANDWIDTH = 2
    LATENCY = 3
    READ_BANDWIDTH = 4
    WRITE_BANDWIDTH = 5
    READ_LATENCY = 6
    WRITE_LATENCY = 7
    MAX = 8


@_cenumdoc("hwloc_location_type_e")
class LocationType(IntEnum):
    OBJECT = 0
    CPUSET = 1


@_cenumdoc("hwloc_local_numanode_flag_e")
class LocalNumaNodeFlag(IntEnum):
    LARGER_LOCALITY = 1 << 0
    SMALLER_LOCALITY = 1 << 1
    ALL = 1 << 2
    INTERSECT_LOCALITY = 1 << 3


@_cuniondoc("hwloc_location_u", parent="hwloc_location")
class hwloc_location_u(ctypes.Union):
    _fields_ = [
        ("cpuset", hwloc_cpuset_t),
        ("object", obj_t),
    ]


@_cstructdoc("hwloc_location")
class Location(_PrintableStruct):
    _fields_ = [
        ("type", ctypes.c_int),  # hwloc_location_type_e
        ("location", hwloc_location_u),
    ]


if TYPE_CHECKING:
    LocationPtr = ctypes._Pointer[Location] | ctypes._CArgObject
else:
    LocationPtr = ctypes._Pointer


_LIB.hwloc_memattr_get_by_name.argtypes = [
    topology_t,
    ctypes.c_char_p,
    ctypes.POINTER(hwloc_memattr_id_t),
]
_LIB.hwloc_memattr_get_by_name.restype = ctypes.c_int


@_cfndoc
def memattr_get_by_name(
    topology: topology_t,
    name: bytes,
) -> int:
    idx = hwloc_memattr_id_t()
    _checkc(_LIB.hwloc_memattr_get_by_name(topology, name, ctypes.byref(idx)))
    return idx.value


_LIB.hwloc_get_local_numanode_objs.argtypes = [
    topology_t,
    ctypes.POINTER(Location),
    ctypes.POINTER(ctypes.c_uint),
    ctypes.POINTER(obj_t),
    ctypes.c_ulong,
]
_LIB.hwloc_get_local_numanode_objs.restype = ctypes.c_int


@_cfndoc
def get_local_numanode_objs(
    topology: topology_t,
    location: LocationPtr,
    nr: UintPtr,
    nodes: ObjPtr | ctypes.Array | None,
    flags: int,
) -> None:
    _checkc(_LIB.hwloc_get_local_numanode_objs(topology, location, nr, nodes, flags))


_LIB.hwloc_topology_get_default_nodeset.argtypes = [
    topology_t,
    hwloc_nodeset_t,
    ctypes.c_ulong,
]
_LIB.hwloc_topology_get_default_nodeset.restype = ctypes.c_int


@_cfndoc
def topology_get_default_nodeset(
    topology: topology_t, nodeset: hwloc_nodeset_t, flags: int
) -> None:
    _checkc(_LIB.hwloc_topology_get_default_nodeset(topology, nodeset, flags))


_LIB.hwloc_memattr_get_value.argtypes = [
    topology_t,
    hwloc_memattr_id_t,
    obj_t,
    ctypes.POINTER(Location),
    ctypes.c_ulong,
    ctypes.POINTER(hwloc_uint64_t),
]
_LIB.hwloc_memattr_get_value.restype = ctypes.c_int


@_cfndoc
def memattr_get_value(
    topology: topology_t,
    attribute: hwloc_memattr_id_t,
    target_node: ObjPtr,
    initiator: LocationPtr | None,
) -> int:
    value = hwloc_uint64_t(0)
    # flags must be 0 for now.
    _checkc(
        _LIB.hwloc_memattr_get_value(
            topology, attribute, target_node, initiator, 0, ctypes.byref(value)
        )
    )
    return int(value.value)


_LIB.hwloc_memattr_get_best_target.argtypes = [
    topology_t,
    hwloc_memattr_id_t,
    ctypes.POINTER(Location),
    ctypes.c_ulong,
    ctypes.POINTER(obj_t),
    ctypes.POINTER(hwloc_uint64_t),
]
_LIB.hwloc_memattr_get_best_target.restype = ctypes.c_int


@_cfndoc
def memattr_get_best_target(
    topology: topology_t,
    attribute: hwloc_memattr_id_t,
    initiator: LocationPtr | None,
) -> tuple[ObjPtr, int]:
    best_target = obj_t()
    value = hwloc_uint64_t()
    # flags must be 0 for now.
    flags = 0
    _checkc(
        _LIB.hwloc_memattr_get_best_target(
            topology,
            attribute,
            initiator,
            flags,
            ctypes.byref(best_target),
            ctypes.byref(value),
        )
    )
    return best_target, value.value


_LIB.hwloc_memattr_get_best_initiator.argtypes = [
    topology_t,
    hwloc_memattr_id_t,
    obj_t,
    ctypes.c_ulong,
    ctypes.POINTER(Location),
    ctypes.POINTER(hwloc_uint64_t),
]
_LIB.hwloc_memattr_get_best_initiator.restype = ctypes.c_int


@_cfndoc
def memattr_get_best_initiator(
    topology: topology_t,
    attribute: hwloc_memattr_id_t,
    target_node: ObjPtr,
) -> tuple[Location, int]:
    best_initiator = Location()
    value = hwloc_uint64_t()
    # flags must be 0 for now.
    flags = 0
    _checkc(
        _LIB.hwloc_memattr_get_best_initiator(
            topology,
            attribute,
            target_node,
            flags,
            ctypes.byref(best_initiator),
            ctypes.byref(value),
        )
    )
    return best_initiator, value.value


_LIB.hwloc_memattr_get_targets.argtypes = [
    topology_t,
    hwloc_memattr_id_t,
    ctypes.POINTER(Location),
    ctypes.c_ulong,
    ctypes.POINTER(ctypes.c_uint),
    ctypes.POINTER(obj_t),
    ctypes.POINTER(hwloc_uint64_t),
]
_LIB.hwloc_memattr_get_targets.restype = ctypes.c_int


@_cfndoc
def memattr_get_targets(
    topology: topology_t,
    attribute: hwloc_memattr_id_t,
    initiator: LocationPtr | None,
    nr: UintPtr,
    targets: ObjPtr | ctypes.Array | None,  # [obj_t]
    values: ctypes._Pointer | ctypes.Array | None,  # [hwloc_uint64_t]
) -> None:
    # flags must be 0 for now.
    flags = 0
    _checkc(
        _LIB.hwloc_memattr_get_targets(
            topology, attribute, initiator, flags, nr, targets, values
        )
    )


_LIB.hwloc_memattr_get_initiators.argtypes = [
    topology_t,
    hwloc_memattr_id_t,
    obj_t,
    ctypes.c_ulong,
    ctypes.POINTER(ctypes.c_uint),
    ctypes.POINTER(Location),
    ctypes.POINTER(hwloc_uint64_t),
]
_LIB.hwloc_memattr_get_initiators.restype = ctypes.c_int


@_cfndoc
def memattr_get_initiators(
    topology: topology_t,
    attribute: hwloc_memattr_id_t,
    target_node: ObjPtr,
    nr: UintPtr,
    initiators: LocationPtr | ctypes.Array | None,  # [hwloc_location]
    values: ctypes._Pointer | ctypes.Array | None,  # [hwloc_uint64_t]
) -> None:
    # flags must be 0 for now.
    flags = 0
    _checkc(
        _LIB.hwloc_memattr_get_initiators(
            topology, attribute, target_node, flags, nr, initiators, values
        )
    )


############################
# Managing memory attributes
############################

# https://www.open-mpi.org/projects/hwloc/doc/v2.12.0/a00169.php


@_cenumdoc("hwloc_memattr_flag_e")
class MemAttrFlag(IntEnum):
    HIGHER_FIRST = 1 << 0
    LOWER_FIRST = 1 << 1
    NEED_INITIATOR = 1 << 2


_LIB.hwloc_memattr_get_name.argtypes = [
    topology_t,
    hwloc_memattr_id_t,
    ctypes.POINTER(ctypes.c_char_p),
]
_LIB.hwloc_memattr_get_name.restype = ctypes.c_int


@_cfndoc
def memattr_get_name(
    topology: topology_t,
    attribute: hwloc_memattr_id_t,
) -> str:
    name = ctypes.c_char_p()
    _checkc(_LIB.hwloc_memattr_get_name(topology, attribute, ctypes.byref(name)))
    assert name.value
    return name.value.decode("utf-8")


_LIB.hwloc_memattr_get_flags.argtypes = [
    topology_t,
    hwloc_memattr_id_t,
    ctypes.POINTER(ctypes.c_ulong),
]
_LIB.hwloc_memattr_get_flags.restype = ctypes.c_int


@_cfndoc
def memattr_get_flags(
    topology: topology_t,
    attribute: hwloc_memattr_id_t,
) -> int:
    flags = ctypes.c_ulong(0)
    _checkc(_LIB.hwloc_memattr_get_flags(topology, attribute, ctypes.byref(flags)))
    return int(flags.value)


_LIB.hwloc_memattr_register.argtypes = [
    topology_t,
    ctypes.c_char_p,
    ctypes.c_ulong,
    ctypes.POINTER(hwloc_memattr_id_t),
]
_LIB.hwloc_memattr_register.restype = ctypes.c_int


@_cfndoc
def memattr_register(
    topology: topology_t,
    name: str,
    flags: int,
) -> hwloc_memattr_id_t:
    attr_id = hwloc_memattr_id_t()
    _checkc(
        _LIB.hwloc_memattr_register(
            topology, name.encode("utf-8"), flags, ctypes.byref(attr_id)
        )
    )
    return attr_id


_LIB.hwloc_memattr_set_value.argtypes = [
    topology_t,
    hwloc_memattr_id_t,
    obj_t,
    ctypes.POINTER(Location),
    ctypes.c_ulong,
    hwloc_uint64_t,
]
_LIB.hwloc_memattr_set_value.restype = ctypes.c_int


@_cfndoc
def memattr_set_value(
    topology: topology_t,
    attribute: hwloc_memattr_id_t,
    target_node: ObjPtr,
    initiator: LocationPtr | None,
    value: int,
) -> None:
    # flags must be 0 for now
    _checkc(
        _LIB.hwloc_memattr_set_value(
            topology, attribute, target_node, initiator, 0, value
        )
    )


####################
# Kinds of CPU cores
####################

# https://www.open-mpi.org/projects/hwloc/doc/v2.12.1/a00170.php

_LIB.hwloc_cpukinds_get_nr.argtypes = [topology_t, ctypes.c_ulong]
_LIB.hwloc_cpukinds_get_nr.restype = ctypes.c_int


@_cfndoc
def cpukinds_get_nr(topology: topology_t) -> int:
    # flags must be 0 for now.
    result = _LIB.hwloc_cpukinds_get_nr(topology, 0)
    if result < 0:
        _checkc(result)
    return result


_LIB.hwloc_cpukinds_get_by_cpuset.argtypes = [
    topology_t,
    const_bitmap_t,
    ctypes.c_ulong,
]
_LIB.hwloc_cpukinds_get_by_cpuset.restype = ctypes.c_int


@_cfndoc
def cpukinds_get_by_cpuset(topology: topology_t, cpuset: const_bitmap_t) -> int:
    # flags must be 0 for now.
    result = _LIB.hwloc_cpukinds_get_by_cpuset(topology, cpuset, 0)
    if result < 0:
        err = ctypes.get_errno()
        msg = _strerror(err)
        if msg is None:
            msg = ""
        else:
            msg += ". "
        if err == errno.EXDEV:
            msg += "The cpuset is only partially included in the some kind."
            raise HwLocError(result, err, msg)
        elif err == errno.ENOENT:
            msg += "The cpuset is not included in any kind, even partially. "
            raise HwLocError(result, err, msg)
        else:
            _checkc(result)
    return result


if _IS_V3:
    _LIB.hwloc_cpukinds_get_info.argtypes = [
        topology_t,
        ctypes.c_uint,
        bitmap_t,
        ctypes.POINTER(ctypes.c_int),
        ctypes.POINTER(ctypes.POINTER(Infos)),
        ctypes.c_ulong,
    ]
else:
    _LIB.hwloc_cpukinds_get_info.argtypes = [
        topology_t,
        ctypes.c_uint,
        bitmap_t,
        ctypes.POINTER(ctypes.c_int),
        ctypes.POINTER(ctypes.c_uint),
        ctypes.POINTER(ctypes.POINTER(Info)),
        ctypes.c_ulong,
    ]
_LIB.hwloc_cpukinds_get_info.restype = ctypes.c_int


@_cfndoc
def cpukinds_get_info(
    topology: topology_t, kind_index: int
) -> tuple[bitmap_t, int, InfosPtr]:
    cpuset = bitmap_alloc()
    efficiency = ctypes.c_int()
    infos_ptr = ctypes.POINTER(Infos)()
    # flags must be 0 for now.
    if _IS_V3:
        _checkc(
            _LIB.hwloc_cpukinds_get_info(
                topology,
                kind_index,
                cpuset,
                ctypes.byref(efficiency),
                ctypes.byref(infos_ptr),
                0,
            )
        )
    else:
        raise NotImplementedError("Only valid in v3.")
    return cpuset, efficiency.value, infos_ptr


_LIB.hwloc_cpukinds_register.argtypes = [
    topology_t,
    bitmap_t,
    ctypes.c_int,
    ctypes.POINTER(Infos),
    ctypes.c_ulong,
]
_LIB.hwloc_cpukinds_register.restype = ctypes.c_int


@_cfndoc
def cpukinds_register(
    topology: topology_t,
    cpuset: bitmap_t,
    forced_efficiency: int,
    infos: Infos | None,
) -> None:
    pinfos = ctypes.byref(infos) if infos is not None else None
    # The parameter flags must be 0 for now.
    if not _IS_V3:
        raise NotImplementedError("Only valid in v3.")
    _checkc(
        _LIB.hwloc_cpukinds_register(topology, cpuset, forced_efficiency, pinfos, 0)
    )


######################################
# Sharing topologies between processes
######################################

# https://www.open-mpi.org/projects/hwloc/doc/v2.12.0/a00185.php

# Not implemented.

###########
# Utilities
###########


def is_same_obj(a: ctypes._Pointer, b: ctypes._Pointer) -> bool:
    return (
        ctypes.cast(a, ctypes.c_void_p).value == ctypes.cast(b, ctypes.c_void_p).value
    )

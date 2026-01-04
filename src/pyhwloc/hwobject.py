# Copyright (c) 2025-2026, NVIDIA CORPORATION.
# SPDX-License-Identifier: BSD-3-Clause
"""
The Object Interface
====================

Python interface of the hwloc_obj type.

"""

from __future__ import annotations

import ctypes
from copy import copy
from dataclasses import dataclass
from enum import IntEnum
from typing import TYPE_CHECKING, Iterator, Protocol, TypeAlias, cast

from .bitmap import Bitmap
from .hwloc import core as _core
from .hwloc.lib import _IS_V3
from .utils import PciId, _Flags, _get_info, _or_flags, _reuse_doc, _TopoRefMixin

if TYPE_CHECKING:
    from .utils import _TopoRef


__all__ = [
    "Object",
    "ObjType",
    "ObjOsdevType",
    "ObjBridgeType",
    "ObjSnprintfFlag",
    "GetTypeDepth",
    "compare_types",
    "ObjTypeCmp",
    "NumaNode",
    "Cache",
    "Group",
    "PciDevice",
    "Bridge",
    "OsDevice",
]


ObjType: TypeAlias = _core.ObjType
ObjOsdevType: TypeAlias = _core.ObjOsdevType
ObjBridgeType: TypeAlias = _core.ObjBridgeType
ObjSnprintfFlag: TypeAlias = _core.ObjSnprintfFlag
GetTypeDepth: TypeAlias = _core.GetTypeDepth


class _HasAttr(Protocol):
    @property
    def attr(self) -> _core.PcidevAttr: ...


class _PciDevAttr(_HasAttr):
    @property
    def func(self) -> int:
        """Function number (t    in the PCI BDF notation xxxx:yy:zz.t)."""
        return self.attr.func

    @property
    def vendor_id(self) -> int:
        """Vendor ID (xxxx in [xxxx:yyyy])."""
        return self.attr.vendor_id

    @property
    def device_id(self) -> int:
        """Device ID (yyyy in [xxxx:yyyy])."""
        return self.attr.device_id

    @property
    def subvendor_id(self) -> int:
        """Sub-Vendor ID."""
        return self.attr.subvendor_id

    @property
    def subdevice_id(self) -> int:
        """Sub-Device ID."""
        return self.attr.subdevice_id

    @property
    def revision(self) -> int:
        """Revision number."""
        return self.attr.revision

    @property
    def prog_if(self) -> int:
        """Register-level programming interface number (3rd byte of the class)."""
        return self.attr.prog_if

    @property
    def linkspeed(self) -> float:
        """Link speed in GB/s."""
        return self.attr.linkspeed

    @property
    def base_class(self) -> int:
        """The base class number"""
        return self.attr.base_class

    @property
    def subclass(self) -> int:
        """The sub-class number"""
        return self.attr.subclass

    @property
    def pci_id(self) -> PciId:
        """Domain, bus, dev."""
        return PciId(self.attr.domain, self.attr.bus, self.attr.dev)


class PciDevAttr(_PciDevAttr):
    def __init__(self, attr: _core.PcidevAttr) -> None:
        self._attr = attr

    @property
    def attr(self) -> _core.PcidevAttr:
        """Get PCI device attributes."""
        return self._attr


class Object(_TopoRefMixin):
    """High-level interface for the hwloc object. Only the topology can return
    objects. User should not use the constructor.

    Parameters
    ----------
    hdl :
        Raw pointer to hwloc object

    """

    def __init__(self, hdl: _core.ObjPtr, topology: _TopoRef) -> None:
        assert hdl
        self._hdl = hdl
        self._topo_ref = topology

    @property
    def native_handle(self) -> _core.ObjPtr:
        """Get the raw object pointer."""
        if not self._topo_ref or not self._topo_ref().is_loaded:  # type: ignore
            raise RuntimeError("Topology is invalid")
        return self._hdl

    @property
    def type(self) -> ObjType:
        """Type of object."""
        return ObjType(self.native_handle.contents.type)

    @property
    def subtype(self) -> str | None:
        """Subtype string to better describe the type field."""
        if self.native_handle.contents.subtype:
            return self.native_handle.contents.subtype.decode("utf-8")
        return None

    @property
    def os_index(self) -> int:
        """OS-provided physical index number."""
        return self.native_handle.contents.os_index

    @property
    def name(self) -> str | None:
        """Object-specific name if any."""
        if self.native_handle.contents.name:
            return self.native_handle.contents.name.decode("utf-8")
        return None

    @property
    def total_memory(self) -> int:
        """Total memory (in bytes) in NUMA nodes below this object."""
        return self.native_handle.contents.total_memory

    # - Begin accessors for attr
    def is_numa_node(self) -> bool:
        """Whether this object is a :py:class:`NumaNode`."""
        return self.type == ObjType.NUMANODE

    def is_group(self) -> bool:
        """Whether this object is a :py:class:`Group`."""
        return self.type == ObjType.GROUP

    def is_pci_device(self) -> bool:
        """Whether this object is a :py:class:`PciDevice`."""
        return self.type == ObjType.PCI_DEVICE

    def is_bridge(self) -> bool:
        """Whether this object is a :py:class:`Bridge`."""
        return self.type == ObjType.BRIDGE

    def is_os_device(self) -> bool:
        """Whether this object is a :py:class:`OsDevice`."""
        return self.type == ObjType.OS_DEVICE

    def is_package(self) -> bool:
        return self.type == ObjType.PACKAGE

    def is_machine(self) -> bool:
        return self.type == ObjType.MACHINE

    # Kinds of object Type
    @_reuse_doc(_core.obj_type_is_normal)
    def is_normal(self) -> bool:
        return _core.obj_type_is_normal(self.type)

    @_reuse_doc(_core.obj_type_is_io)
    def is_io(self) -> bool:
        return _core.obj_type_is_io(self.type)

    @_reuse_doc(_core.obj_type_is_memory)
    def is_memory(self) -> bool:
        return _core.obj_type_is_memory(self.type)

    @_reuse_doc(_core.obj_type_is_cache)
    def is_cache(self) -> bool:
        return _core.obj_type_is_cache(self.type)

    @_reuse_doc(_core.obj_type_is_dcache)
    def is_dcache(self) -> bool:
        return _core.obj_type_is_dcache(self.type)

    @_reuse_doc(_core.obj_type_is_icache)
    def is_icache(self) -> bool:
        return _core.obj_type_is_icache(self.type)

    # fixme: We might want to create a class hierarchy insetad
    @property
    def attr(self) -> ctypes.Structure | None:
        """Get attributes of this object. The return type depends on the type of this
        object as the underlying type is a C union :c:union:`hwloc_obj_attr_u`. We have
        a number of methods for commonly used attributes like the :py:meth:`is_normal`,
        but don't have a proper wrapper for the entire union yet.

        All pyhwloc structs can be properly printed in Python. To get an overview of the
        object attributes, you can print the result from this method, or use the
        :py:meth:`format_attr`.

        """
        attr = self.native_handle.contents.attr
        if not attr:
            return None
        # FIXME: Am I getting this right? I looked into the `hwloc_obj_attr_snprintf`
        # implementation, but it doesn't use the group. Also, if the bridge upstream is
        # PCI, this union can be converted to PCIe?
        if self.is_cache():
            return attr.contents.cache

        typ = self.type
        match typ:
            case ObjType.NUMANODE:
                return attr.contents.numanode
            # cache has been handled
            case ObjType.GROUP:
                return attr.contents.group
            case ObjType.PCI_DEVICE:
                return attr.contents.pcidev
            case ObjType.BRIDGE:
                return attr.contents.bridge
            case ObjType.OS_DEVICE:
                return attr.contents.osdev
            case _:
                return None

    def format_attr(
        self,
        sep: str = ", ",
        flags: _Flags[ObjSnprintfFlag] = ObjSnprintfFlag.OLD_VERBOSE,
    ) -> str | None:
        """Print the attributes."""
        n_bytes = 1024
        buf = ctypes.create_string_buffer(n_bytes)
        _core.obj_attr_snprintf(buf, n_bytes, self.native_handle, sep, _or_flags(flags))
        if not buf.value:
            return None
        return buf.value.decode("utf-8")

    # - End accessors for attr

    @property
    def depth(self) -> int:
        """Vertical index in the hierarchy."""
        return self.native_handle.contents.depth

    @property
    def logical_index(self) -> int:
        """Horizontal index in the whole list of similar objects."""
        return self.native_handle.contents.logical_index

    @property
    def next_cousin(self) -> Object | None:
        """Next object of same type and depth."""
        if self.native_handle.contents.next_cousin:
            return _object(self.native_handle.contents.next_cousin, self._topo_ref)
        return None

    @property
    def prev_cousin(self) -> Object | None:
        """Previous object of same type and depth."""
        if self.native_handle.contents.prev_cousin:
            return _object(self.native_handle.contents.prev_cousin, self._topo_ref)
        return None

    @property
    def parent(self) -> Object | None:
        """Parent object, None if root (Machine object)."""
        if self.native_handle.contents.parent:
            return _object(self.native_handle.contents.parent, self._topo_ref)
        return None

    @property
    def sibling_rank(self) -> int:
        """Index in parent's children array."""
        return self.native_handle.contents.sibling_rank

    @property
    def next_sibling(self) -> Object | None:
        """Next object below the same parent."""
        if self.native_handle.contents.next_sibling:
            return _object(self.native_handle.contents.next_sibling, self._topo_ref)
        return None

    @property
    def prev_sibling(self) -> Object | None:
        """Previous object below the same parent."""
        if self.native_handle.contents.prev_sibling:
            return _object(self.native_handle.contents.prev_sibling, self._topo_ref)
        return None

    @property
    def arity(self) -> int:
        """Number of normal children."""
        return self.native_handle.contents.arity

    @property
    def children(self) -> list[Object]:
        """Normal children. Memory, Misc and I/O children are not listed here."""
        ptr_children = self.native_handle.contents.children
        results = []
        for i in range(self.arity):
            obj = _object(ptr_children[i], self._topo_ref)
            results.append(obj)
        return results

    @property
    def first_child(self) -> Object | None:
        """First normal child."""
        if self.native_handle.contents.first_child:
            return _object(self.native_handle.contents.first_child, self._topo_ref)
        return None

    @property
    def last_child(self) -> Object | None:
        """Last normal child."""
        if self.native_handle.contents.last_child:
            return _object(self.native_handle.contents.last_child, self._topo_ref)
        return None

    @property
    def symmetric_subtree(self) -> bool:
        """Set if the subtree of normal objects below this object is symmetric."""
        return bool(self.native_handle.contents.symmetric_subtree)

    @property
    def memory_arity(self) -> int:
        """Number of Memory children."""
        return self.native_handle.contents.memory_arity

    @property
    def memory_first_child(self) -> Object | None:
        """First Memory child."""
        if self.native_handle.contents.memory_first_child:
            return _object(
                self.native_handle.contents.memory_first_child, self._topo_ref
            )
        return None

    @property
    def io_arity(self) -> int:
        """Number of I/O children."""
        return self.native_handle.contents.io_arity

    @property
    def io_first_child(self) -> Object | None:
        """First I/O child."""
        if self.native_handle.contents.io_first_child:
            return _object(self.native_handle.contents.io_first_child, self._topo_ref)
        return None

    @property
    def misc_arity(self) -> int:
        """Number of Misc children."""
        return self.native_handle.contents.misc_arity

    @property
    def misc_first_child(self) -> Object | None:
        """First Misc child."""
        if self.native_handle.contents.misc_first_child:
            return _object(self.native_handle.contents.misc_first_child, self._topo_ref)
        return None

    @property
    def cpuset(self) -> Bitmap | None:
        """CPUs covered by this object."""
        cpuset = self.native_handle.contents.cpuset
        return copy(Bitmap.from_native_handle(cpuset, own=False)) if cpuset else None

    @property
    def complete_cpuset(self) -> Bitmap | None:
        """The complete CPU set of processors of this object."""
        complete_cpuset = self.native_handle.contents.complete_cpuset
        return (
            copy(Bitmap.from_native_handle(complete_cpuset, own=False))
            if complete_cpuset
            else None
        )

    @property
    def nodeset(self) -> Bitmap | None:
        """NUMA nodes covered by this object or containing this object."""
        nodeset = self.native_handle.contents.nodeset
        return copy(Bitmap.from_native_handle(nodeset, own=False)) if nodeset else None

    @property
    def complete_nodeset(self) -> Bitmap | None:
        """The complete NUMA node set of this object."""
        complete_nodeset = self.native_handle.contents.complete_nodeset
        return (
            copy(Bitmap.from_native_handle(complete_nodeset, own=False))
            if complete_nodeset
            else None
        )

    @property
    def info(self) -> dict[str, str]:
        """Get the object info."""
        infos = self.native_handle.contents.infos
        infos_d = _get_info(infos)

        return infos_d

    @_reuse_doc(_core.obj_add_info)
    def add_info(self, name: str, value: str) -> None:
        _core.obj_add_info(self.native_handle, name, value)

    # void *userdata

    @property
    def gp_index(self) -> int:
        "Global persistent index."
        return int(self.native_handle.contents.gp_index)

    @property
    def pci_id(self) -> PciId:
        if not self.is_pci_device():
            raise ValueError(
                f"Invalid object type. Expecting PCI device, got {self.type}"
            )
        attr = self.attr
        assert attr is not None and isinstance(attr, _core.PcidevAttr)
        return PciId(attr.domain, attr.bus, attr.dev)

    def iter_children(self) -> Iterator[Object]:
        """Iterate over all children of this object."""
        child = self.first_child
        while child:
            yield child
            # fixme: Should we use `get_next_child` instead?
            child = child.next_sibling

    def iter_memory_children(self) -> Iterator[Object]:
        """Iterate over all memory children of this object."""
        child = self.memory_first_child
        while child:
            yield child
            child = child.next_sibling

    def iter_io_children(self) -> Iterator[Object]:
        """Iterate over all I/O children of this object."""
        child = self.io_first_child
        while child:
            yield child
            child = child.next_sibling

    def iter_misc_children(self) -> Iterator[Object]:
        """Iterate over all misc children of this object."""
        child = self.misc_first_child
        while child:
            yield child
            child = child.next_sibling

    def iter_siblings(self) -> Iterator[Object]:
        """Iterate over all siblings of this object (including self)."""
        # Go to first sibling
        current: Object | None = self
        assert current is not None

        while current.prev_sibling is not None:
            current = current.prev_sibling

        # Iterate through all siblings
        while current is not None:
            yield current
            current = current.next_sibling

    @_reuse_doc(_core.obj_get_info_by_name)
    def get_info_by_name(self, name: str) -> str | None:
        return _core.obj_get_info_by_name(self.native_handle, name)

    # Looking at Ancestor and Child Objects

    @_reuse_doc(_core.get_common_ancestor_obj)
    def common_ancestor_obj(self, other: Object) -> Object:
        if self.depth < 0 or other.depth < 0:
            raise ValueError("This function only works with objects in the main tree.")
        return _object(
            _core.get_common_ancestor_obj(
                self._topo.native_handle, self.native_handle, other.native_handle
            ),
            self._topo_ref,
        )

    @_reuse_doc(_core.get_ancestor_obj_by_depth)
    def get_ancestor_obj_by_depth(self, depth: int) -> Object | None:
        obj = _core.get_ancestor_obj_by_depth(
            self._topo.native_handle, depth, self.native_handle
        )
        if obj is None:
            return None
        return _object(
            obj,
            self._topo_ref,
        )

    @_reuse_doc(_core.get_ancestor_obj_by_type)
    def get_ancestor_obj_by_type(self, obj_type: ObjType) -> Object | None:
        obj = _core.get_ancestor_obj_by_type(
            self._topo.native_handle, obj_type, self.native_handle
        )
        if obj is None:
            return None
        return _object(
            obj,
            self._topo_ref,
        )

    @_reuse_doc(_core.obj_is_in_subtree)
    def is_in_subtree(self, subtree_root: Object) -> bool:
        return _core.obj_is_in_subtree(
            self._topo.native_handle, self.native_handle, subtree_root.native_handle
        )

    # End -- Looking at Ancestor and Child Objects

    def __str__(self) -> str:
        type_name = self.type.name
        parts = [f"{type_name}#{self.logical_index}"]

        if self.name:
            parts.append(f"({self.name})")
        if self.subtype:
            parts.append(f"[{self.subtype}]")

        return " ".join(parts)

    def __repr__(self) -> str:
        return (
            f"Object(type={self.type.name}, "
            f"logical_index={self.logical_index}, "
            f"depth={self.depth})"
        )

    def __eq__(self, other: object) -> bool:
        """Check equality based on pointer address."""
        if not isinstance(other, Object):
            return False
        return _core.is_same_obj(self.native_handle, other.native_handle)

    def __hash__(self) -> int:
        """Hash based on pointer address."""
        return hash(ctypes.addressof(self.native_handle.contents))


class NumaNode(Object):
    """NUMA node object."""

    @property
    def attr(self) -> _core.NumanodeAttr:
        """Return numa node attributes."""
        return cast(_core.NumanodeAttr, super().attr)

    @property
    def local_memory(self) -> int:
        """Local memory (in bytes)."""
        return self.attr.local_memory

    @dataclass
    class PageType:
        size: int
        count: int

    @property
    def page_types(self) -> list[PageType]:
        """List of local memory page types."""
        if _IS_V3:
            raise TypeError("page types has been removed in v3.")
        prop = []
        for i in range(self.attr.page_types_len):
            prop.append(
                self.PageType(
                    size=self.attr.page_types[i].size,
                    count=self.attr.page_types[i].count,
                )
            )
        return prop


class Cache(Object):
    """Cache :py:class:`Object`."""

    @property
    def attr(self) -> _core.CacheAttr:
        """Return cache attributes."""
        return cast(_core.CacheAttr, super().attr)

    @property
    def size(self) -> int:
        """Size of cache in bytes."""
        return self.attr.size

    @property
    def cache_depth(self) -> int:
        """Depth of cache (e.g., L1, L2, ...etc.)."""
        return self.attr.depth

    @property
    def linesize(self) -> int:
        """Cache-line size in bytes. 0 if unknown."""
        return self.attr.linesize

    @property
    def associativity(self) -> int:
        """Ways of associativity, -1 if fully associative, 0 if unknown."""
        return self.attr.associativity

    @property
    def cache_type(self) -> int:
        """Cache type."""
        return _core.ObjCacheType(self.attr.type)


class Group(Object):
    """:py:class:`Object` with type == `GROUP`."""

    @property
    def attr(self) -> _core.GroupAttr:
        """Return group attributes."""
        return cast(_core.GroupAttr, super().attr)

    @property
    def group_depth(self) -> int:
        """Depth of group object."""
        return self.attr.depth

    # fixme: expose `alloc_group_object` and `free_group_object.`


class PciDevice(Object, _PciDevAttr):
    """:py:class:`Object` with type == `PCI_DEVICE`."""

    def __init__(self, hdl: _core.ObjPtr, topology: _TopoRef) -> None:
        super().__init__(hdl, topology)

    @property
    def attr(self) -> _core.PcidevAttr:
        """Return PCI device attributes."""
        return cast(_core.PcidevAttr, super().attr)


class Bridge(Object):
    """:py:class:`Object` with type == `BRIDGE`."""

    @property
    def attr(self) -> _core.BridgeAttr:
        """Return bridge attributes."""
        return cast(_core.BridgeAttr, super().attr)

    @property
    def upstream_pci(self) -> PciDevAttr:
        """PCI attribute of the upstream part as a PCI device."""
        return PciDevAttr(self.attr.upstream.pci)

    @property
    def upstream_type(self) -> ObjBridgeType:
        """Upstream Bridge type."""
        return self.attr.upstream_type

    @property
    def downstream_pci(self) -> _core.BridgeDownstreamPci:
        """PCI attribute of the downstream part as a PCI device."""
        return self.attr.downstream.pci

    def downstream_type(self) -> ObjBridgeType:
        """Downstream Bridge type"""
        return self.attr.downstream_type


class OsDevice(Object):
    """:py:class:`Object` with type == `OS_DEVICE`."""

    @property
    def attr(self) -> _core.OsdevAttr:
        """Return OS device attributes."""
        return cast(_core.OsdevAttr, super().attr)

    def is_osdev_type(self, typ: int) -> bool:
        """Check type of the OS device."""
        if not self.is_os_device():
            return False

        attr = self.attr
        if attr is None:
            return False
        osdev_types = attr.types
        return bool(osdev_types & typ)

    def is_gpu(self) -> bool:
        """Types include the `ObjOsdevType.GPU`."""
        return self.is_osdev_type(ObjOsdevType.GPU)

    def is_coproc(self) -> bool:
        """Types include the `ObjOsdevType.COPROC`."""
        return self.is_osdev_type(ObjOsdevType.COPROC)

    def is_storage(self) -> bool:
        """Types include the `ObjOsdevType.STORAGE`."""
        return self.is_osdev_type(ObjOsdevType.STORAGE)


class ObjTypeCmp(IntEnum):
    """Result from :py:func:`~pyhwloc.hwobject.compare_types`."""

    UNORDERED = _core.HWLOC_TYPE_UNORDERED
    INCLUDE = -1
    EQUAL = 0
    INCLUDED_BY = 1


def compare_types(type1: ObjType | Object, type2: ObjType | Object) -> ObjTypeCmp:
    """See the relationship between two object types. If the returned enum is
    ``INCLUDE``, it implies that `type1` objects **usually** include `type2`
    objects. The reverse is indicated by the ``INCLUDED_BY``.

    """
    if isinstance(type1, Object):
        type1 = type1.type
    if isinstance(type2, Object):
        type2 = type2.type
    r = _core.compare_types(type1, type2)
    if r == _core.HWLOC_TYPE_UNORDERED:
        return ObjTypeCmp.UNORDERED
    if r < 0:
        return ObjTypeCmp.INCLUDE
    if r > 0:
        return ObjTypeCmp.INCLUDED_BY
    return ObjTypeCmp.EQUAL


def _object(hdl: _core.ObjPtr, topology: _TopoRef) -> Object:
    assert hdl
    attr = hdl.contents.attr
    if not attr:
        return Object(hdl, topology)

    typ = ObjType(hdl.contents.type)
    is_cache = _core.obj_type_is_cache(typ)
    if is_cache:
        return Cache(hdl, topology)

    match typ:
        case ObjType.NUMANODE:
            return NumaNode(hdl, topology)
        # cache has been handled
        case ObjType.GROUP:
            return Group(hdl, topology)
        case ObjType.PCI_DEVICE:
            return PciDevice(hdl, topology)
        case ObjType.BRIDGE:
            return Bridge(hdl, topology)
        case ObjType.OS_DEVICE:
            return OsDevice(hdl, topology)
        case _:
            return Object(hdl, topology)

# Copyright (c) 2025-2026, NVIDIA CORPORATION.
# SPDX-License-Identifier: BSD-3-Clause
"""
The Topology Interface
======================

"""

from __future__ import annotations

import ctypes
import logging
import os
import weakref
from collections import namedtuple
from copy import copy
from types import TracebackType
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Iterator,
    Type,
    TypeAlias,
    cast,
)

from . import hwobject as _hwobject
from .bitmap import Bitmap as _Bitmap
from .cpukinds import CpuKinds
from .hwloc import core as _core
from .hwloc import lib as _lib
from .hwobject import Object as _Object
from .hwobject import ObjType as _ObjType
from .hwobject import _object
from .utils import _Flags, _get_info, _memview_to_mem, _or_flags, _reuse_doc

if TYPE_CHECKING or _lib._IS_DOC_BUILD:
    from . import distances as _distances
    from .memattrs import MemAttrs as _MemAttrs

__all__ = [
    "Topology",
    "ExportXmlFlags",
    "ExportSyntheticFlags",
    "TypeFilter",
    "DistancesKind",
    "MemBindPolicy",
    "MemBindFlags",
    "CpuBindFlags",
    "AllowFlags",
    "RestrictFlags",
]


def _from_impl(fn: Callable[[_core.topology_t], None], load: bool) -> _core.topology_t:
    hdl = _core.topology_t(0)
    try:
        _core.topology_init(hdl)
        fn(hdl)
        if load is True:
            _core.topology_load(hdl)
    except Exception:
        if hdl:
            _core.topology_destroy(hdl)
        raise
    return hdl


def _from_xml_buffer(xml_buffer: str, load: bool) -> _core.topology_t:
    return _from_impl(lambda hdl: _core.topology_set_xmlbuffer(hdl, xml_buffer), load)


def _not_nodeset(flags: int) -> bool:
    return not bool(flags & MemBindFlags.BYNODESET)


def _to_bitmap(target: _BindTarget, is_cpuset: bool) -> _Bitmap:
    if isinstance(target, set):
        bitmap = _Bitmap.from_sched_set(target)
    elif isinstance(target, _Object):
        if is_cpuset:
            ns = target.cpuset
            if ns is None:
                raise ValueError("Object has no associated CPUs.")
        else:
            ns = target.nodeset
            if ns is None:
                raise ValueError("Object has no associated NUMA nodes")
        bitmap = ns
    else:
        bitmap = target
    return bitmap


TopologyFlags: TypeAlias = _core.TopologyFlags
ObjPtr = _core.ObjPtr
ExportXmlFlags: TypeAlias = _core.ExportXmlFlags
ExportSyntheticFlags: TypeAlias = _core.ExportSyntheticFlags
TypeFilter: TypeAlias = _core.TypeFilter
DistancesKind: TypeAlias = _core.DistancesKind
# Memory bind type aliases
MemBindPolicy: TypeAlias = _core.MemBindPolicy
MemBindFlags: TypeAlias = _core.MemBindFlags
CpuBindFlags: TypeAlias = _core.CpuBindFlags
# Modifying a loaded topology
AllowFlags: TypeAlias = _core.AllowFlags
RestrictFlags: TypeAlias = _core.RestrictFlags
# internal
_BindTarget: TypeAlias = _Bitmap | set[int] | _Object


class Topology:
    """High-level interface for the hwloc topology.

    This class provides a context manager interface for working with hardware
    topology information. It automatically handles topology initialization,
    loading, and cleanup.

    The default `Topology` constructor initializes a topology object based on the
    current system. For alternative topology sources, use the class methods:

    - :meth:`from_this_system`
    - :meth:`from_pid`
    - :meth:`from_synthetic`
    - :meth:`from_xml_file`
    - :meth:`from_xml_buffer`

    .. code-block::

        # Context manager usage (recommended)
        with Topology.from_this_system() as topo:  # Current system
            print(f"Topology depth: {topo.depth}")

        # Synthetic topology
        with Topology.from_synthetic("node:2 core:2 pu:2") as topo:
            print(f"Topology depth: {topo.depth}")

        # Load from XML file
        with Topology.from_xml_file("/path/to/topology.xml") as topo:
            print(f"Topology depth: {topo.depth}")

        # Direct usage,  cleanup is recommended but not required.
        try:
            topo = Topology()
            print(f"Topology depth: {topo.depth}")
        finally:
            topo.destroy()

        # Uses automatic cleanup in the `__del__` method instead. This depends on the gc
        # and doesn't propagate exceptions raised inside the destroy method.
        topo = Topology()

    To use a filter or set a component, users need to call the :meth:`load` explicitly
    when **not** using the context manager:

    .. code-block::

        with Topology.from_this_system().set_all_types_filter(
            TypeFilter.KEEP_IMPORTANT
        ) as topo:
            # auto load when using a context manager
            pass

        topo = Topology.from_this_system().set_all_types_filter(
            TypeFilter.KEEP_IMPORTANT
        ).load() # Load the topology

    Lastly, there's a short hand for using the current system if you don't need to apply
    filter or set component/flags:

    .. code-block::

        with Topology() as topo:
            print(f"Topology depth: {topo.depth}")

    """

    def __init__(self) -> None:
        """Short hand for the :py:meth:`from_this_system`. Use the class method if you
        need to delay the load process for customization.

        """

        def _(hdl: _core.topology_t) -> None:
            pass

        hdl = _from_impl(_, True)

        self._hdl = hdl
        self._loaded = True
        # See the distance release method for more info.
        self._cleanup: list[weakref.ReferenceType[_distances.Distances]] = []

    @classmethod
    def from_native_handle(cls, hdl: _core.topology_t, is_loaded: bool) -> Topology:
        topo = cls.__new__(cls)
        topo._hdl = hdl
        topo._loaded = is_loaded
        topo._cleanup = []
        return topo

    @classmethod
    def from_this_system(cls, *, load: bool = False) -> Topology:
        """Create a topology from this system.

        Parameters
        ----------
        load :
            Whether the object should load the topology from the system. Set to False if
            you want to apply additional filters.

        Returns
        -------
        New Topology instance for the specified process.
        """

        def _(hdl: _core.topology_t) -> None:
            pass

        hdl = _from_impl(_, load)
        return cls.from_native_handle(hdl, load)

    @classmethod
    def from_pid(cls, pid: int, *, load: bool = False) -> Topology:
        """Create a topology from a specific process ID.

        Parameters
        ----------
        pid
            Process ID to get topology from
        load :
            Whether the object should load the topology from the system. Set to False if
            you want to apply additional filters.

        Returns
        -------
        New Topology instance for the specified process.
        """
        hdl = _from_impl(lambda hdl: _core.topology_set_pid(hdl, pid), load)
        return cls.from_native_handle(hdl, load)

    @classmethod
    def from_synthetic(cls, description: str, *, load: bool = False) -> Topology:
        """Create a topology from a synthetic description.

        Parameters
        ----------
        description
            Synthetic topology description (e.g., "node:2 core:2 pu:2")
        load :
            Whether the object should load the topology from the system. Set to False if
            you want to apply additional filters.

        Returns
        -------
        New Topology instance from the synthetic description.
        """
        hdl = _from_impl(
            lambda hdl: _core.topology_set_synthetic(hdl, description), load
        )
        return cls.from_native_handle(hdl, load)

    @classmethod
    def from_xml_file(
        cls, xml_path: os.PathLike | str, *, load: bool = False
    ) -> Topology:
        """Create a topology from a XML file.

        Parameters
        ----------
        xml_path
            Path to XML file containing topology
        load :
            Whether the object should load the topology from the system. Set to False if
            you want to apply additional filters.

        Returns
        -------
        New Topology instance loaded from XML file.
        """
        path = os.fspath(os.path.expanduser(xml_path))
        hdl = _from_impl(lambda hdl: _core.topology_set_xml(hdl, path), load)
        return cls.from_native_handle(hdl, load)

    @classmethod
    def from_xml_buffer(cls, xml_buffer: str, *, load: bool = False) -> Topology:
        """Create a topology from a XML string.

        Parameters
        ----------
        xml_buffer
            XML string containing topology
        load :
            Whether the object should load the topology from the system. Set to False if
            you want to apply additional filters.

        Returns
        -------
        New Topology instance loaded from XML string.
        """
        hdl = _from_xml_buffer(xml_buffer, load)
        return cls.from_native_handle(hdl, load)

    @_reuse_doc(_core.topology_check)
    def check(self) -> None:
        _core.topology_check(self._hdl)

    def load(self) -> Topology:
        """Load the topology. No-op if it's already loaded"""
        if not self.is_loaded:
            _core.topology_load(self._hdl)
            self._loaded = True
        return self

    @property
    def native_handle(self) -> _core.topology_t:
        """Get the native hwloc topology handle."""
        if not hasattr(self, "_hdl"):
            raise RuntimeError("Topology has been destroyed")
        if not self.is_loaded:
            raise RuntimeError(
                "Topology is not loaded, please call the `load` method or use "
                "the context manager"
            )
        return self._hdl

    @_reuse_doc(_core.topology_export_xmlbuffer)
    def export_xml_buffer(self, flags: _Flags[ExportXmlFlags] = 0) -> str:
        return _core.topology_export_xmlbuffer(self.native_handle, _or_flags(flags))

    @_reuse_doc(_core.topology_export_xml)
    def export_xml_file(
        self, path: os.PathLike | str, flags: _Flags[ExportXmlFlags] = 0
    ) -> None:
        path = os.fspath(os.path.expanduser(path))
        _core.topology_export_xml(self.native_handle, path, _or_flags(flags))

    @_reuse_doc(_core.topology_export_synthetic)
    def export_synthetic(self, flags: _Flags[ExportSyntheticFlags]) -> str:
        n_bytes = 1024
        buf = ctypes.create_string_buffer(n_bytes)
        n_written = _core.topology_export_synthetic(
            self.native_handle, buf, n_bytes, _or_flags(flags)
        )
        while n_written == n_bytes - 1:
            n_bytes = n_bytes * 2
            buf = ctypes.create_string_buffer(n_bytes)
            n_written = _core.topology_export_synthetic(
                self.native_handle, buf, n_bytes, _or_flags(flags)
            )
            if n_bytes >= 8192:
                raise RuntimeError("Failed to export synthetic.")
        assert buf.value is not None
        return buf.value.decode("utf-8")

    @property
    def is_loaded(self) -> bool:
        """Check if topology is loaded and ready for use."""
        return hasattr(self, "_hdl") and self._loaded

    def is_this_system(self) -> bool:
        """Check if topology represents the current system."""
        if not self.is_loaded:
            return False
        return _core.topology_is_thissystem(self.native_handle)

    def get_support(self) -> Any:
        """See :py:func:`pyhwloc.hwloc.core.topology_get_support`.

        Returns
        -------
        A namedtuple with the same structure as :c:struct:`hwloc_topology_support`.
        """
        support = _core.topology_get_support(self.native_handle).contents
        result: dict[str, dict[str, bool]] = {}
        for k, v in support._fields_:  # type: ignore
            result[k] = {}
            v0 = getattr(support, k)
            if v0:
                for k1, _ in v0.contents._fields_:
                    v1 = getattr(v0.contents, k1)
                    assert v1 in (0, 1)
                    result[k][k1] = bool(v1)

        TS = namedtuple("TopologySupport", list(result.keys()))  # type: ignore

        def create_child(name: str, d: dict) -> Any:
            Typ = namedtuple(name.capitalize() + "Support", d.keys())  # type: ignore
            v = Typ(**d)
            return v

        tran = {k: create_child(k, v) for k, v in result.items()}

        sup = TS(**tran)
        return sup

    @property
    @_reuse_doc(_core.topology_get_depth)
    def depth(self) -> int:
        return _core.topology_get_depth(self.native_handle)

    def destroy(self) -> None:
        """Explicitly destroy the topology and free resources."""
        while self._cleanup:
            dist_ref = self._cleanup.pop()
            dist = dist_ref()
            if dist:
                dist.release()

        if hasattr(self, "_hdl"):
            _core.topology_destroy(self.native_handle)
            self._loaded = False
            del self._hdl

    def __enter__(self) -> Topology:
        if not self.is_loaded:
            self.load()
        return self

    def __exit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.destroy()

    def __del__(self) -> None:
        try:
            self.destroy()
        except Exception as e:
            logging.warning(str(e))

    def __copy__(self) -> Topology:
        new = _core.topology_dup(self.native_handle)
        return Topology.from_native_handle(new, True)

    def __deepcopy__(self, memo: dict) -> Topology:
        return self.__copy__()

    def __getstate__(self) -> dict:
        """Serialize topology state for pickling using XML export."""
        # Export topology to XML for serialization
        xml_buffer = self.export_xml_buffer(0)  # Use default flags
        return {"xml_buffer": xml_buffer}

    def __setstate__(self, state: dict) -> None:
        """Restore topology state from pickle using XML import."""
        xml_buffer = state["xml_buffer"]
        assert not hasattr(self, "_hdl") and not hasattr(self, "_loaded")

        hdl = _from_xml_buffer(xml_buffer, True)
        self._hdl = hdl
        self._loaded = True
        self._cleanup = []

    def _checked_apply(self, fn: Callable, values: int) -> Topology:
        # If we don't raise here, hwloc returns EBUSY: Device or resource busy, which is
        # not really helpful.
        if self.is_loaded:
            raise RuntimeError("Cannot set filter after topology is loaded")
        # Unchecked access to handle as we haven't loaded the topo yet.
        fn(self._hdl, values)
        return self

    @_reuse_doc(_core.topology_set_flags)
    def set_flags(self, flags: _Flags[TopologyFlags]) -> Topology:
        # This is not a property because we want continuous
        # setters: Topology.set_flags(flags).set_io_types_filter(f) ...
        return self._checked_apply(_core.topology_set_flags, _or_flags(flags))

    @_reuse_doc(_core.topology_get_flags)
    def get_flags(self) -> int:
        # fixme: Create a better way to return composite flags
        flags = _core.topology_get_flags(self.native_handle)
        return flags

    @_reuse_doc(_core.topology_set_io_types_filter)
    def set_io_types_filter(self, type_filter: TypeFilter) -> Topology:
        return self._checked_apply(_core.topology_set_io_types_filter, type_filter)

    @_reuse_doc(_core.topology_set_all_types_filter)
    def set_all_types_filter(self, type_filter: TypeFilter) -> Topology:
        return self._checked_apply(_core.topology_set_all_types_filter, type_filter)

    @_reuse_doc(_core.topology_set_cache_types_filter)
    def set_cache_types_filter(self, type_filter: TypeFilter) -> Topology:
        return self._checked_apply(_core.topology_set_cache_types_filter, type_filter)

    @_reuse_doc(_core.topology_set_icache_types_filter)
    def set_icache_types_filter(self, type_filter: TypeFilter) -> Topology:
        return self._checked_apply(_core.topology_set_icache_types_filter, type_filter)

    @_reuse_doc(_core.topology_set_components)
    def set_components(
        self,
        name: str,
        flags: _Flags[
            _core.TopologyComponentsFlag
        ] = _core.TopologyComponentsFlag.BLACKLIST,
    ) -> Topology:
        # switched order between name and flags, as flags usually come at last.
        _core.topology_set_components(self._hdl, _or_flags(flags), name)
        return self

    # Modifying a Loaded Topology

    @_reuse_doc(_core.topology_restrict)
    def restrict(self, cpuset: _Bitmap, flags: _Flags[RestrictFlags]) -> None:
        _core.topology_restrict(
            self.native_handle, cpuset.native_handle, _or_flags(flags)
        )

    @_reuse_doc(_core.topology_allow)
    def allow(
        self,
        cpuset: _Bitmap | None,
        nodeset: _Bitmap | None,
        flags: _Flags[AllowFlags],
    ) -> None:
        cpuset_hdl = cpuset.native_handle if cpuset else None
        nodeset_hdl = nodeset.native_handle if nodeset else None
        _core.topology_allow(
            self.native_handle, cpuset_hdl, nodeset_hdl, _or_flags(flags)
        )

    @_reuse_doc(_core.topology_refresh)
    def refresh(self) -> None:
        _core.topology_refresh(self.native_handle)

    def get_obj_by_depth(self, depth: int, idx: int) -> _Object | None:
        """Get object at specific depth and index.

        Parameters
        ----------
        depth
            Depth level in topology tree
        idx
            Index of object at that depth

        Returns
        -------
        Object instance or None if not found
        """
        ptr = _core.get_obj_by_depth(self.native_handle, depth, idx)
        return _object(ptr, weakref.ref(self)) if ptr else None

    @_reuse_doc(_core.get_root_obj)
    def get_root_obj(self) -> _Object:
        return _object(_core.get_root_obj(self.native_handle), weakref.ref(self))

    @_reuse_doc(_core.get_obj_by_type)
    def get_obj_by_type(self, obj_type: _ObjType, idx: int) -> _Object | None:
        ptr = _core.get_obj_by_type(self.native_handle, obj_type, idx)
        return _object(ptr, weakref.ref(self)) if ptr else None

    @_reuse_doc(_core.get_pu_obj_by_os_index)
    def get_pu_obj_by_os_index(self, os_index: int) -> _Object | None:
        ptr = _core.get_pu_obj_by_os_index(self.native_handle, os_index)
        return _object(ptr, weakref.ref(self)) if ptr else None

    @_reuse_doc(_core.get_numanode_obj_by_os_index)
    def get_numanode_obj_by_os_index(self, os_index: int) -> _Object | None:
        ptr = _core.get_numanode_obj_by_os_index(self.native_handle, os_index)
        return _object(ptr, weakref.ref(self)) if ptr else None

    @property
    @_reuse_doc(_core.topology_get_topology_cpuset)
    def cpuset(self) -> _Bitmap:
        # Same as get_root_obj().cpuset
        bitmap = _core.topology_get_topology_cpuset(self.native_handle)
        return copy(_Bitmap.from_native_handle(bitmap, own=False))

    @property
    @_reuse_doc(_core.topology_get_allowed_cpuset)
    def allowed_cpuset(self) -> _Bitmap:
        bitmap = _core.topology_get_allowed_cpuset(self.native_handle)
        return copy(_Bitmap.from_native_handle(bitmap, own=False))

    @property
    @_reuse_doc(_core.topology_get_allowed_nodeset)
    def allowed_nodeset(self) -> _Bitmap:
        bitmap = _core.topology_get_allowed_nodeset(self.native_handle)
        return copy(_Bitmap.from_native_handle(bitmap, own=False))

    @_reuse_doc(_core.get_nbobjs_by_depth)
    def get_nbobjs_by_depth(self, depth: int) -> int:
        return _core.get_nbobjs_by_depth(self.native_handle, depth)

    @_reuse_doc(_core.get_nbobjs_by_type)
    def get_nbobjs_by_type(self, obj_type: _ObjType) -> int:
        return _core.get_nbobjs_by_type(self.native_handle, obj_type)

    def iter_objs_by_depth(self, depth: int) -> Iterator[_Object]:
        """Iterate over all objects at specific depth.

        Parameters
        ----------
        depth
            Depth level in topology tree

        Yields
        ------
        Object instances at that depth

        """
        prev = None
        while True:
            ptr = _core.get_next_obj_by_depth(self.native_handle, depth, prev)
            if ptr is None:
                break
            obj = _object(ptr, weakref.ref(self))
            yield obj
            prev = ptr

    def n_cores(self) -> int:
        """Get the total number of cores.

        Returns
        -------
        Number of core objects in the topology
        """
        return self.get_nbobjs_by_type(_ObjType.CORE)

    def iter_objs_by_type(self, obj_type: _ObjType) -> Iterator[_Object]:
        """Iterate over all objects of specific type.

        Parameters
        ----------
        obj_type
            Type of object to iterate

        Yields
        ------
        Object instances of that type
        """
        prev = None
        while True:
            ptr = _core.get_next_obj_by_type(self.native_handle, obj_type, prev)
            if ptr is None:
                break
            obj = _object(ptr, weakref.ref(self))
            yield obj
            prev = ptr

    def iter_all_breadth_first(self) -> Iterator[_Object]:
        """Iterate over all objects in the topology.

        Yields
        ------
        All object instances in breadth first order.
        """
        for depth in range(self.depth):
            for obj in self.iter_objs_by_depth(depth):
                yield obj

    # We can implement pre/in/post-order traversal if needed.

    def get_depth_type(self, depth: int) -> _ObjType:
        """Get the object type at specific depth.

        Parameters
        ----------
        depth
            Depth level in topology tree

        Returns
        -------
        Object type at that depth
        """
        return _core.get_depth_type(self.native_handle, depth)

    def iter_cpus(self) -> Iterator[_Object]:
        """Iterate over all processing units (CPUs).

        Yields
        ------
        All PU (processing unit) object instances
        """
        return self.iter_objs_by_type(_ObjType.PU)

    def iter_cores(self) -> Iterator[_Object]:
        """Iterate over all cores.

        Yields
        ------
        All core object instances
        """
        return self.iter_objs_by_type(_ObjType.CORE)

    def iter_numa_nodes(self) -> Iterator[_hwobject.NumaNode]:
        """Iterate over all NUMA nodes.

        Yields
        ------
        All NUMA node object instances
        """
        return cast(
            Iterator[_hwobject.NumaNode], self.iter_objs_by_type(_ObjType.NUMANODE)
        )

    def iter_packages(self) -> Iterator[_Object]:
        """Iterate over all packages (sockets).

        Yields
        ------
        All package object instances
        """
        return self.iter_objs_by_type(_ObjType.PACKAGE)

    # Finding I/O objects
    def _iter_io_devices(
        self, fn: Callable[[_core.topology_t, ObjPtr | None], ObjPtr | None]
    ) -> Iterator[_Object]:
        prev = None
        while True:
            ptr = fn(self.native_handle, prev)
            if ptr is None:
                break
            yield _object(ptr, weakref.ref(self))
            prev = ptr

    def iter_os_devices(self) -> Iterator[_hwobject.OsDevice]:
        """Iterate over all OS devices.

        Yields
        ------
        All OS devices instances.
        """
        return cast(
            Iterator[_hwobject.OsDevice], self._iter_io_devices(_core.get_next_osdev)
        )

    def iter_bridges(self) -> Iterator[_hwobject.Bridge]:
        """Iterate over all bridges.

        Yields
        ------
        All bridge instances.
        """
        return cast(
            Iterator[_hwobject.Bridge], self._iter_io_devices(_core.get_next_bridge)
        )

    def iter_pci_devices(self) -> Iterator[_hwobject.PciDevice]:
        """Iterate over all PCI devices.

        Yields
        ------
        All PCI device instances.
        """
        return cast(
            Iterator[_hwobject.PciDevice], self._iter_io_devices(_core.get_next_pcidev)
        )

    def n_cpus(self) -> int:
        """Get the total number of processing units (CPUs).

        Returns
        -------
        Number of PU objects in the topology
        """
        return self.get_nbobjs_by_type(_ObjType.PU)

    def n_numa_nodes(self) -> int:
        """Get the total number of NUMA nodes.

        Returns
        -------
        Number of NUMA node objects in the topology
        """
        return self.get_nbobjs_by_type(_ObjType.NUMANODE)

    def n_packages(self) -> int:
        """Get the total number of packages (sockets).

        Returns
        -------
        Number of package objects in the topology
        """
        return self.get_nbobjs_by_type(_ObjType.PACKAGE)

    def n_pci_devices(self) -> int:
        """Get the total number of PCI devices.

        Returns
        -------
        Number of PCI device objects in the topology
        """
        return self.get_nbobjs_by_type(_ObjType.PCI_DEVICE)

    def n_os_devices(self) -> int:
        """Get the total number of OS devices.

        Returns
        -------
        Number of OS device objects in the topology
        """
        return self.get_nbobjs_by_type(_ObjType.OS_DEVICE)

    # Distance Methods
    @_reuse_doc(_core.distances_get)
    def get_distances(
        self, kind: _Flags[DistancesKind] = 0
    ) -> list[_distances.Distances]:
        from .distances import Distances

        # Get count first
        nr = ctypes.c_uint(0)
        result: list[Distances] = []

        _core.distances_get(
            self.native_handle,
            ctypes.byref(nr),
            None,
            _or_flags(kind),
        )
        distances_ptr_ptr = (ctypes.POINTER(_core.Distances) * nr.value)()
        if nr.value == 0:
            return result

        _core.distances_get(
            self.native_handle,
            ctypes.byref(nr),
            distances_ptr_ptr,
            _or_flags(kind),
        )

        # Create Distance objects
        for i in range(nr.value):
            dist_handle = distances_ptr_ptr[i]
            result.append(Distances(dist_handle, weakref.ref(self)))

        # Push into the cleanup queue. We also perform some cleanups here to avoid
        # having too many references.
        still_valid = []
        for ref in self._cleanup:
            if ref() is not None:
                still_valid.append(ref)
        self._cleanup = still_valid
        self._cleanup.extend([weakref.ref(dist) for dist in result])

        return result

    def get_memattrs(self) -> _MemAttrs:
        """Get a proxy object for the memory attributes."""
        from .memattrs import MemAttrs

        return MemAttrs(weakref.ref(self))

    # Memory Binding Methods
    def set_membind(
        self,
        target: _BindTarget,
        policy: MemBindPolicy,
        flags: _Flags[MemBindFlags] = 0,
    ) -> None:
        """Bind the current process memory to specified NUMA nodes. The current process
        is assumed to be single-threaded.

        Parameters
        ----------
        target
            NUMA nodes to bind memory to. This can be an
            :py:class:`~pyhwloc.hwobject.Object`, a :py:class:`~pyhwloc.bitmap.Bitmap`,
            or a CPU set used by the `os.sched_*` routines (:py:class:`set` [int]).
        policy
            Memory binding policy to use
        flags
            Additional flags for memory binding.

        """
        flags = _or_flags(flags)
        bitmap = _to_bitmap(target, _not_nodeset(flags))
        _core.set_membind(self.native_handle, bitmap.native_handle, policy, flags)

    def get_membind(
        self, flags: _Flags[MemBindFlags] = 0
    ) -> tuple[_Bitmap, MemBindPolicy]:
        """Get current process memory binding.

        Parameters
        ----------
        flags
            Flags for getting memory binding

        Returns
        -------
        Tuple of (bitmap, policy) for current memory binding
        """
        bitmap = _Bitmap()
        policy = _core.get_membind(
            self.native_handle, bitmap.native_handle, _or_flags(flags)
        )
        return bitmap, policy

    def set_proc_membind(
        self,
        pid: int,
        target: _BindTarget,
        policy: MemBindPolicy,
        flags: _Flags[MemBindFlags] = 0,
    ) -> None:
        """Bind specific process memory to NUMA nodes.

        Parameters
        ----------
        pid
            Process ID to bind.
        target
            NUMA nodes to bind memory to. This can be an
            :py:class:`~pyhwloc.hwobject.Object`, a :py:class:`~pyhwloc.bitmap.Bitmap`,
            or a CPU set used by the `os.sched_*` routines (:py:class:`set` [int]).
        policy
            Memory binding policy to use
        flags
            Additional flags for memory binding
        """
        flags = _or_flags(flags)
        bitmap = _to_bitmap(target, _not_nodeset(flags))
        hdl = None
        try:
            hdl = _core._open_proc_handle(pid, read_only=False)
            _core.set_proc_membind(
                self.native_handle, hdl, bitmap.native_handle, policy, flags
            )
        finally:
            if hdl:
                _core._close_proc_handle(hdl)

    def get_proc_membind(
        self, pid: int, flags: _Flags[MemBindFlags] = 0
    ) -> tuple[_Bitmap, MemBindPolicy]:
        """Get process memory binding.

        Parameters
        ----------
        pid
            Process ID to query.
        flags
            Flags for getting memory binding.

        Returns
        -------
        Tuple of (nodeset, policy) for process memory binding
        """
        nodeset = _Bitmap()
        hdl = None
        try:
            hdl = _core._open_proc_handle(pid)
            policy = _core.get_proc_membind(
                self.native_handle, hdl, nodeset.native_handle, _or_flags(flags)
            )
            return nodeset, policy
        finally:
            if hdl:
                _core._close_proc_handle(hdl)

    def set_area_membind(
        self,
        mem: memoryview,
        target: _BindTarget,
        policy: MemBindPolicy,
        flags: _Flags[MemBindFlags] = 0,
    ) -> None:
        """Bind memory area to NUMA nodes.

        Parameters
        ----------
        mem
            Memory area. Use :py:func:`~pyhwloc.utils.memoryview_from_memory` to
            construct a :py:class:`memoryview` if you have pointers.
        target
            NUMA nodes to bind memory to. This can be an
            :py:class:`~pyhwloc.hwobject.Object`, a :py:class:`~pyhwloc.bitmap.Bitmap`,
            or a CPU set used by the `os.sched_*` routines (:py:class:`set` [int]).
        policy
            Memory binding policy to use.
        flags
            Additional flags for memory binding.
        """
        flags = _or_flags(flags)
        bitmap = _to_bitmap(target, _not_nodeset(flags))
        addr, size = _memview_to_mem(mem)

        _core.set_area_membind(
            self.native_handle,
            addr,
            size,
            bitmap.native_handle,
            policy,
            flags,
        )

    def get_area_membind(
        self,
        mem: memoryview,
        flags: _Flags[MemBindFlags] = 0,
    ) -> tuple[_Bitmap, MemBindPolicy]:
        """Get memory area binding.

        Parameters
        ----------
        mem
            Memory area. Use :py:func:`~pyhwloc.utils.memoryview_from_memory` to
            construct a :py:class:`memoryview` if you have pointers.
        flags
            Flags for getting memory binding.

        Returns
        -------
        Tuple of (bitmap, policy) for memory area binding
        """
        bitmap = _Bitmap()
        addr, size = _memview_to_mem(mem)

        policy = _core.get_area_membind(
            self.native_handle, addr, size, bitmap.native_handle, _or_flags(flags)
        )
        return bitmap, policy

    # Allocator interface is not exposed. I checked popular libraries like torch, none
    # of them supports setting custom allocator in Python. We can come back to this if
    # someone asks for it.

    # CPU Binding Methods
    def set_cpubind(self, target: _BindTarget, flags: _Flags[CpuBindFlags] = 0) -> None:
        """Bind current process to specified CPUs.

        Parameters
        ----------
        target
            CPUs to bind the current process to. This can be an
            :py:class:`~pyhwloc.hwobject.Object`, a :py:class:`~pyhwloc.bitmap.Bitmap`,
            or a CPU set used by the `os.sched_*` routines (:py:class:`set` [int]).
        flags
            Additional flags for CPU binding
        """
        bitmap = _to_bitmap(target, is_cpuset=True)
        _core.set_cpubind(self.native_handle, bitmap.native_handle, _or_flags(flags))

    def get_cpubind(self, flags: _Flags[CpuBindFlags] = 0) -> _Bitmap:
        """Get current process CPU binding.

        Parameters
        ----------
        flags
            Flags for getting CPU binding

        Returns
        -------
        Bitmap representing current CPU binding
        """
        cpuset = _Bitmap()
        _core.get_cpubind(self.native_handle, cpuset.native_handle, _or_flags(flags))
        return cpuset

    def set_proc_cpubind(
        self, pid: int, target: _BindTarget, flags: _Flags[CpuBindFlags] = 0
    ) -> None:
        """Bind specific process to CPUs.

        Parameters
        ----------
        pid
            Process ID to bind
        target
            CPUs to bind the current process to. This can be an
            :py:class:`~pyhwloc.hwobject.Object`, a :py:class:`~pyhwloc.bitmap.Bitmap`,
            or a CPU set used by the `os.sched_*` routines (:py:class:`set` [int]).
        flags
            Additional flags for CPU binding
        """
        bitmap = _to_bitmap(target, is_cpuset=True)
        hdl = None
        try:
            hdl = _core._open_proc_handle(pid, read_only=False)
            _core.set_proc_cpubind(
                self.native_handle,
                hdl,
                bitmap.native_handle,
                _or_flags(flags),
            )
        finally:
            if hdl:
                _core._close_proc_handle(hdl)

    def get_proc_cpubind(self, pid: int, flags: _Flags[CpuBindFlags] = 0) -> _Bitmap:
        """Get process CPU binding.

        Parameters
        ----------
        pid
            Process ID to query
        flags
            Flags for getting CPU binding

        Returns
        -------
        Bitmap representing process CPU binding
        """
        cpuset = _Bitmap()
        hdl = None
        try:
            hdl = _core._open_proc_handle(pid)
            _core.get_proc_cpubind(
                self.native_handle,
                hdl,
                cpuset.native_handle,
                _or_flags(flags),
            )
            return cpuset
        finally:
            if hdl:
                _core._close_proc_handle(hdl)

    def set_thread_cpubind(
        self, thread_id: int, target: _BindTarget, flags: _Flags[CpuBindFlags] = 0
    ) -> None:
        """Bind specific thread to CPUs.

        Parameters
        ----------
        thread_id
            Thread ID to bind
        target
            CPUs to bind the current process to. This can be an
            :py:class:`~pyhwloc.hwobject.Object`, a :py:class:`~pyhwloc.bitmap.Bitmap`,
            or a CPU set used by the `os.sched_*` routines (:py:class:`set` [int]).
        flags
            Additional flags for CPU binding
        """
        bitmap = _to_bitmap(target, is_cpuset=True)
        hdl = None
        try:
            hdl = _core._open_thread_handle(thread_id, read_only=False)
            _core.set_thread_cpubind(
                self.native_handle,
                hdl,
                bitmap.native_handle,
                _or_flags(flags),
            )
        finally:
            if hdl:
                _core._close_thread_handle(hdl)

    def get_thread_cpubind(
        self, thread_id: int, flags: _Flags[CpuBindFlags] = 0
    ) -> _Bitmap:
        """Get thread CPU binding.

        Parameters
        ----------
        thread_id
            Thread ID to query
        flags
            Flags for getting CPU binding

        Returns
        -------
        Bitmap representing thread CPU binding
        """
        cpuset = _Bitmap()
        hdl = None
        try:
            hdl = _core._open_thread_handle(thread_id)
            _core.get_thread_cpubind(
                self.native_handle,
                hdl,
                cpuset.native_handle,
                _or_flags(flags),
            )
            return cpuset
        finally:
            if hdl:
                _core._close_thread_handle(hdl)

    def get_last_cpu_location(self, flags: _Flags[CpuBindFlags] = 0) -> _Bitmap:
        """Get where current process last ran.

        Parameters
        ----------
        flags
            Flags for getting CPU location

        Returns
        -------
        Bitmap representing the cpuset where the process last ran.
        """
        cpuset = _Bitmap()
        _core.get_last_cpu_location(
            self.native_handle, cpuset.native_handle, _or_flags(flags)
        )
        return cpuset

    def get_proc_last_cpu_location(
        self, pid: int, flags: _Flags[CpuBindFlags] = 0
    ) -> _Bitmap:
        """Get where specific process last ran.

        Parameters
        ----------
        pid
            Process ID to query. On Linux, pid can also be a thread ID if the flag is
            set to THREAD.
        flags
            Flags for getting CPU location

        Returns
        -------
        Bitmap representing the cpuset where process last ran

        """
        cpuset = _Bitmap()
        hdl = None
        try:
            hdl = _core._open_proc_handle(pid)
            _core.get_proc_last_cpu_location(
                self.native_handle,
                hdl,
                cpuset.native_handle,
                _or_flags(flags),
            )
            return cpuset
        finally:
            if hdl:
                _core._close_proc_handle(hdl)

    def get_cpukinds(self) -> CpuKinds:
        """Get a proxy object for the CPU kinds."""
        return CpuKinds(weakref.ref(self))

    @property
    @_reuse_doc(_core.topology_get_infos)
    def info(self) -> dict[str, str]:
        infos_ptr = _core.topology_get_infos(self.native_handle)
        infos_d = {}
        if infos_ptr:
            infos_d = _get_info(infos_ptr.contents)
        return infos_d


@_reuse_doc(_core.get_api_version)
def get_api_version() -> tuple[int, int, int]:
    return _core.get_api_version()


if not _lib._IS_DOC_BUILD:
    _major, _minor, _rev = get_api_version()
    if not ((_major == 3 and _minor == 0 and _rev == 0) or _major == 2):
        raise RuntimeError(
            "Invalid API version. You have installed a different version of hwloc. "
            f"Expecting API version: 3.0.0, got {_major}.{_minor}.{_rev}) ."
        )


# Shorthands

from_this_system = Topology.from_this_system

from_pid = Topology.from_pid

from_synthetic = Topology.from_synthetic

from_xml_file = Topology.from_xml_file

from_xml_buffer = Topology.from_xml_buffer

# Copyright (c) 2025, NVIDIA CORPORATION.
# SPDX-License-Identifier: BSD-3-Clause
"""
Utilities
=========
"""

from __future__ import annotations

import ctypes
from collections.abc import Sequence
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Callable,
    ParamSpec,
    Protocol,
    TypeAlias,
    TypeVar,
    Union,
)

__all__ = ["PciId", "memoryview_from_memory"]

_P = ParamSpec("_P")
_R = TypeVar("_R")


if TYPE_CHECKING:
    import weakref

    from .hwloc import core as _core
    from .topology import Topology

    _TopoRef: TypeAlias = weakref.ReferenceType[Topology]


def _reuse_doc(orig: Callable) -> Callable[[Callable[_P, _R]], Callable[_P, _R]]:
    def fn(fobj: Callable[_P, _R]) -> Callable[_P, _R]:
        fobj.__doc__ = orig.__doc__
        return fobj

    return fn


_Flag = TypeVar("_Flag")
_Flags = Union[int, _Flag, Sequence[_Flag]]


def _or_flags(flags: _Flags) -> int:
    if isinstance(flags, Sequence):
        r = 0
        for f in flags:
            r |= f
        flags = r
    return flags


ctypes.pythonapi.PyMemoryView_FromMemory.argtypes = (
    ctypes.c_void_p,
    ctypes.c_ssize_t,  # size: size of the memory block
    ctypes.c_int,  # flags: 0x100 for read-only, 0x200 for read/write
)
ctypes.pythonapi.PyMemoryView_FromMemory.restype = ctypes.py_object  # Python memoryview


def memoryview_from_memory(
    ptr: ctypes.c_void_p, size: int, read_only: bool
) -> memoryview:
    """Create a Python memoryview from a ctypes pointer.

    Parameters
    ----------
    ptr :
        A ctypes Pointer.
    size :
        Size in bytes.
    read_only :
        Do we need write access to the memory view?

    Returns
    -------
    A Python :py:class:`memoryview` object.

    """
    PyBUF_READ = 0x100
    PyBUF_WRITE = 0x200
    flags = PyBUF_READ if read_only else PyBUF_WRITE
    mv = ctypes.pythonapi.PyMemoryView_FromMemory(ptr, size, flags)
    return mv


def _memview_to_mem(mem: memoryview) -> tuple[ctypes.c_void_p, int]:
    if not isinstance(mem, memoryview):
        raise TypeError(f"Expecting a memoryview, got: {type(mem)}")

    size = len(mem)
    Buffer = ctypes.c_char * size
    buf = Buffer.from_buffer(mem)
    addr = ctypes.cast(buf, ctypes.c_void_p)
    return addr, size


class _HasTopoRef(Protocol):
    @property
    def _topo_ref(self) -> _TopoRef: ...


class _TopoRefMixin:
    """A mixin class for accessing a reference to the topology."""

    @property
    def _topo(self: _HasTopoRef) -> Topology:
        if not self._topo_ref or not self._topo_ref().is_loaded:  # type: ignore
            raise RuntimeError("Topology is invalid")
        v = self._topo_ref()
        assert v is not None
        return v


if TYPE_CHECKING:
    _InfoPtr: TypeAlias = ctypes._Pointer[_core.Info]
else:
    _InfoPtr: TypeAlias = ctypes._Pointer


def _get_info_v2(infos: _InfoPtr, cnt: int) -> dict[str, str]:
    infos_d = {}
    for i in range(cnt):
        info = infos[i]
        name = info.name.decode("utf-8") if info.name else ""
        value = info.value.decode("utf-8") if info.value else ""
        infos_d[name] = value
    return infos_d


def _get_info(infos: _core.Infos) -> dict[str, str]:
    return _get_info_v2(infos.array, infos.count)


@dataclass
class PciId:
    domain: int  # domain id
    bus: int  # bus id
    dev: int  # device id

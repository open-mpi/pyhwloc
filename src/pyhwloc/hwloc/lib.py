# Copyright (c) 2025, NVIDIA CORPORATION.
# SPDX-License-Identifier: BSD-3-Clause
from __future__ import annotations

import ctypes
import errno
import os
import sys
from ctypes.util import find_library
from typing import Any, Callable, ParamSpec, Type, TypeVar

from .libc import strerror as cstrerror


def normpath(path: str) -> str:
    return os.path.normpath(os.path.abspath(path))


_file_path = normpath(__file__)

_IS_WINDOWS = sys.platform == "win32"

_IS_DOC_BUILD = bool(os.environ.get("PYHWLOC_SPHINX", False))

_lib_path = normpath(
    os.path.join(
        os.path.dirname(_file_path),
        os.path.pardir,
        "_lib",
    )
)


def _get_libname(name: str) -> str:
    if _IS_WINDOWS:
        return f"{name}.dll"
    return f"lib{name}.so"


if _IS_WINDOWS:
    _search_name = os.path.join(_lib_path, "bin", _get_libname("hwloc"))
else:
    _search_name = os.path.join(_lib_path, "lib", _get_libname("hwloc"))

if os.path.exists(_search_name):
    # The hwloc is bundled with pyhwloc
    os.environ["HWLOC_PLUGINS_PATH"] = os.path.join(_lib_path, "lib", "hwloc")
    _hwloc_lib_name = _search_name
else:
    # Dynamically find hwloc library at runtime
    found = find_library(_get_libname("hwloc"))
    if found is None:
        raise ImportError("hwloc library not found.")

    _hwloc_lib_name = found

if _IS_WINDOWS:
    _LIB = ctypes.CDLL(
        _hwloc_lib_name, use_errno=True, mode=ctypes.RTLD_GLOBAL, use_last_error=True
    )
else:
    _LIB = ctypes.CDLL(_hwloc_lib_name, mode=ctypes.RTLD_GLOBAL, use_errno=True)


_pyhwloc_lib = ctypes.cdll.LoadLibrary(os.path.join(_lib_path, _get_libname("pyhwloc")))


class HwLocError(RuntimeError):
    """Generic catch-all runtime error reported by pyhwloc."""

    def __init__(self, status: int, err: int, msg: bytes | str | None) -> None:
        self.status = status
        self.errno = err
        if isinstance(msg, bytes):
            self.msg: str | None = msg.decode("utf-8")
        else:
            self.msg = msg

        super().__init__(
            f"status: {self.status}, errno: {self.errno}, error: {self.msg}"
        )


def _checkc(status: int, expected: int = 0) -> None:
    """Raise errors for hwloc functions."""
    if status == expected:
        return

    err = ctypes.get_errno()
    msg = cstrerror(err)
    match err:
        case errno.EPERM:
            raise PermissionError(msg)
        case errno.ENOSYS:
            raise NotImplementedError(msg)
        case errno.EINVAL:
            raise ValueError(msg)
        case errno.ENOMEM:
            raise MemoryError(msg)
        case errno.ENOENT:
            raise FileNotFoundError(msg)
        case 0:
            if _IS_WINDOWS:
                werr = ctypes.get_last_error()  # type: ignore[attr-defined]
                if werr != 0:
                    raise ctypes.WinError(werr)  # type: ignore[attr-defined]
            raise HwLocError(status, err, msg)
        case _:
            raise HwLocError(status, err, msg)


def _hwloc_error(name: str) -> HwLocError:
    """Alternative constructor for the :py:class:`HwLocError` for functions that don't
    have status code as return value.

    """
    err = ctypes.get_errno()
    msg = f"`{name}` failed"
    c_msg = cstrerror(err)
    if c_msg is not None:
        msg += ":\n"
        msg + c_msg
    else:
        msg += "."
    return HwLocError(-1, err, msg)


_P = ParamSpec("_P")
_R = TypeVar("_R")


def _cfndoc(fn: Callable[_P, _R]) -> Callable[_P, _R]:
    doc = f"See :c:func:`hwloc_{fn.__name__}`"
    fn.__doc__ = doc
    return fn


def _c_prefix_fndoc(prefix: str) -> Callable[[Callable[_P, _R]], Callable[_P, _R]]:
    def _decorator(fn: Callable[_P, _R]) -> Callable[_P, _R]:
        doc = f"See :c:func:`hwloc_{prefix}_{fn.__name__}`"
        fn.__doc__ = doc
        return fn

    return _decorator


def _cenumdoc(name: str) -> Callable[[Type], Type]:
    def _decorator(enum: Type) -> Type:
        doc = f"""See :c:enum:`{name}`."""
        enum.__doc__ = doc
        return enum

    return _decorator


def _cstructdoc(name: str, *, parent: str | None = None) -> Callable[[Type], Type]:
    def _decorator(struct: Type) -> Type:
        assert issubclass(struct, ctypes.Structure), struct
        if parent is not None:
            doc = f"""See :c:struct:`{parent}.{name}`"""
        else:
            doc = f"""See :c:struct:`{name}`"""
        struct.__doc__ = doc
        return struct

    return _decorator


def _cuniondoc(name: str, *, parent: str | None = None) -> Callable[[Type], Type]:
    def _decorator(union: Type) -> Type:
        assert issubclass(union, ctypes.Union)
        if parent is not None:
            doc = f"""See :c:union:`{parent}.name`"""
        else:
            doc = f"""See :c:union:`{name}`"""
        union.__doc__ = doc
        return union

    return _decorator


class _PrintableStruct(ctypes.Structure):
    def __str__(self) -> str:
        name = type(self).__name__
        result = f"{name}("
        names = [f[0] for f in self._fields_]
        for i, k in enumerate(names):
            v = getattr(self, k)
            if isinstance(v, ctypes._Pointer):
                if v:
                    result += f"Pointer[{k}]({v.contents})"
                else:
                    result += f"{k}={v}"
            else:
                result += f"{k}={v}"
            if i != len(names) - 1:
                result += ", "

        result += ")"
        return result


def libinfo() -> dict[str, Any]:
    """Internal debug use."""
    info: dict[str, Any] = {"hwloc": _hwloc_lib_name}
    plugins_path = os.path.join(os.path.dirname(_hwloc_lib_name), "hwloc")
    if os.path.exists(plugins_path):
        plugins = os.listdir(plugins_path)
        info["plugins"] = plugins
    return info

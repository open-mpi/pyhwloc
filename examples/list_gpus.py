# Copyright (c) 2025, NVIDIA CORPORATION.
# SPDX-License-Identifier: BSD-3-Clause
"""
Simple script for listing GPU devices
=====================================
"""

import cuda.bindings.driver as cuda
import cuda.bindings.runtime as cudart

from pyhwloc import from_this_system
from pyhwloc.hwobject import GetTypeDepth, ObjType, OsDevice
from pyhwloc.topology import TypeFilter


def list_with_nvml() -> None:
    import pynvml

    from pyhwloc.nvml import get_cpu_affinity, get_device

    try:
        pynvml.nvmlInit()

        with from_this_system().set_io_types_filter(TypeFilter.KEEP_ALL) as topo:
            status, cnt = cudart.cudaGetDeviceCount()
            assert status == cudart.cudaError_t.cudaSuccess
            for i in range(cnt):
                # Create a NVML device
                dev = get_device(topo, i)
                # Get the hwloc native device type
                osdev = dev.get_osdev()
                assert osdev is not None
                print(osdev, ":", osdev.format_attr())
                print("cpuset:", dev.get_affinity().to_sched_set())
                print("cpuset from nvml:", get_cpu_affinity(i).to_sched_set())
    finally:
        pynvml.nvmlShutdown()


def list_with_cudart() -> None:
    from pyhwloc.cuda_runtime import get_device

    with from_this_system().set_io_types_filter(TypeFilter.KEEP_ALL) as topo:
        status, cnt = cudart.cudaGetDeviceCount()
        assert status == cudart.cudaError_t.cudaSuccess
        for i in range(cnt):
            # Create a CUDA runtime device
            dev = get_device(topo, i)
            # Get the hwloc native device type
            osdev = dev.get_osdev()
            assert osdev is not None
            print(osdev, ":", osdev.format_attr())
            print("cpuset:", dev.get_affinity().to_sched_set())


def list_with_cuda() -> None:
    from pyhwloc.cuda_driver import get_device

    with from_this_system().set_io_types_filter(TypeFilter.KEEP_ALL) as topo:
        status, cnt = cuda.cuDeviceGetCount()
        assert status == cuda.CUresult.CUDA_SUCCESS
        for i in range(cnt):
            # Create a CUDA driver device
            dev = get_device(topo, i)
            # Get the hwloc native device type
            osdev = dev.get_osdev()
            assert osdev is not None
            print(osdev, ":", osdev.format_attr())
            print("cpuset:", dev.get_affinity().to_sched_set())


def list_with_osdev() -> None:
    # GPU is categorized as IO device.
    # Hwloc lists devices from both NVML and CUDA.
    with from_this_system().set_io_types_filter(TypeFilter.KEEP_ALL) as topo:
        # Look for OS devices (which include GPUs)
        for obj in topo.iter_objs_by_type(ObjType.OS_DEVICE):
            # Check if it's a GPU device
            if isinstance(obj, OsDevice) and obj.is_gpu():
                assert obj.depth == GetTypeDepth.OS_DEVICE
                print(obj, ":", obj.format_attr())


if __name__ == "__main__":
    print("List by hwloc OS device\n")
    list_with_osdev()
    print("\nList by CUDA runtime\n")
    list_with_cudart()
    print("\nList by CUDA driver\n")
    list_with_cuda()
    print("\nList by NVML\n")
    list_with_nvml()

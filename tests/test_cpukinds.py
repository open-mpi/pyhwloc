# Copyright (c) 2025-2026, NVIDIA CORPORATION.
# SPDX-License-Identifier: BSD-3-Clause
from __future__ import annotations

import pytest

from pyhwloc.bitmap import Bitmap
from pyhwloc.hwloc.lib import _IS_V3
from pyhwloc.topology import Topology


@pytest.mark.skipif(condition=not _IS_V3, reason="Not implemented for V2.")
def test_cpukinds() -> None:
    desc = (
        "Package:1 [NUMANode(memory=134228295680)] Die:2 L3Cache:1(size=100663296) "
        "L2Cache:6(size=1048576) L1dCache:1(size=32768) Core:1 PU:2(indexes=2*12:1*2)"
    )
    with Topology.from_synthetic(desc) as topo:
        kinds = topo.get_cpukinds()
        assert kinds.n_kinds() == 0
        cpuset = Bitmap()
        cpuset.set(0)
        infos = {"Foo": "Bar", "Cache": "Huge"}
        kinds.register(cpuset, 1, infos=infos)
        assert kinds.n_kinds() == 1

        retrieved_cpuset, efficiency, infos = kinds.get_info(0)
        assert isinstance(retrieved_cpuset, Bitmap)
        assert isinstance(efficiency, int)
        assert isinstance(infos, dict)
        assert retrieved_cpuset.weight() == 1

        cpuset = Bitmap()
        cpuset.set(0)
        cpuset.set(1)
        kinds.register(cpuset, 42, infos=infos)

        assert kinds.n_kinds() == 2
        retrieved_cpuset, efficiency, infos = kinds.get_info(0)

        assert retrieved_cpuset.weight() == 1
        assert len(infos) == 2

        for k, v in infos.items():
            assert k in ("Foo", "Cache")
            assert v in ("Bar", "Huge")

        with pytest.raises(RuntimeError, match="partially"):
            kinds.get_kind_by_cpuset(cpuset)

        kind_idx = kinds.get_kind_by_cpuset(retrieved_cpuset)
        assert kind_idx == 0

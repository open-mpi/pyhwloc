#!/usr/bin/env bash

cd /ws/
git clone https://github.com/open-mpi/hwloc.git
if [[ $HWLOC_MAJOR == "2" ]]; then
    echo "Build V2"
    cd hwloc && git checkout $(cat /ws/hwloc_version_v2) && cd -
else
    echo "Build V3"
    cd hwloc && git checkout $(cat /ws/hwloc_version) && cd -
fi

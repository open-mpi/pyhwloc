#!/usr/bin/env bash

set -euo pipefail

if [[ "$HWLOC_MAJOR" != "2" && "$HWLOC_MAJOR" != "3" ]]; then
    echo "Error: HWLOC_MAJOR must be either 2 or 3, got: '$HWLOC_MAJOR'" >&2
    exit 1
fi

cd /ws/
git clone https://github.com/open-mpi/hwloc.git
if [[ $HWLOC_MAJOR == "2" ]]; then
    echo "Build V2"
    cd hwloc && git checkout $(cat /ws/hwloc_version_v2) && cd -
else
    echo "Build V3"
    cd hwloc && git checkout $(cat /ws/hwloc_version) && cd -
fi

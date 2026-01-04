#!/usr/bin/env bash

cd /ws/hwloc/doc
HWLOC_DOXYGEN_GENERATE_XML=YES doxygen ./doxygen.cfg
if [[ $HWLOC_MAJOR == "3" ]]; then
    cp -r doxygen-doc/xml /ws/xml
else
    echo "We don't support building XML pages for V2."
    mkdir /ws/xml
fi
cd ..                           # hwloc

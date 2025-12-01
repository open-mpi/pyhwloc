#!/usr/bin/env bash
WHEEL_TAG=manylinux_2_34_x86_64

docker run --rm --gpus=all --workdir=/ws --mount type=bind,src=.,dst=/ws cuda-13-manylinux:latest -- python -m pip wheel -v . --config-settings=fetch-hwloc=True --wheel-dir dist/

auditwheel repair --only-plat --plat ${WHEEL_TAG} ./dist/*.whl
python3 -m wheel tags --python-tag py3 --abi-tag none --platform ${WHEEL_TAG} --remove *.whl

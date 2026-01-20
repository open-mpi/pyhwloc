#!/usr/bin/env bash

jinja2 dev/pyhwloc_dev.yml.j2 -D arch=x86_64 > ./dev/pyhwloc_dev.yml
jinja2 dev/pyhwloc_dev.yml.j2 -D arch=aarch64 > ./dev/pyhwloc_aarch_dev.yml

jinja2 dev/pyhwloc_ext_dev.yml.j2 -D arch=x86_64 > ./dev/pyhwloc_ext_dev.yml
jinja2 dev/pyhwloc_ext_dev.yml.j2 -D arch=aarch64 > ./dev/pyhwloc_ext_aarch_dev.yml

#!/usr/bin/env bash

set -e

cd "${BASH_SOURCE%/*}"

set +e
pip download pyxb
set -e

tar -xzvf PyXB-1.2.5.tar.gz
cd PyXB-1.2.5 || exit
export PYXB_ROOT
PYXB_ROOT=$(pwd)
./pyxb/bundles/opengis/scripts/genbind
python setup.py install --user


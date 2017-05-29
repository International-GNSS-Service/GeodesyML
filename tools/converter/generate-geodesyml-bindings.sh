#!/usr/bin/env bash

set -e
PYTHON_PREFIX=${HOME}/.local
PYXBGEN=${PYTHON_PREFIX}/bin/pyxbgen

${PYXBGEN} -u ./modified-schemas/geodesyML.xsd -m eGeodesy --archive-path "${PYTHON_PREFIX}"/lib/python2.7/site-packages/pyxb/bundles/common/raw/:"${PYTHON_PREFIX}"/lib/python2.7/site-packages/pyxb/bundles/opengis/raw/:.:+

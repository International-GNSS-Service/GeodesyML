#!/usr/bin/env bash

set -e
cd $(git rev-parse --show-toplevel)
git subtree pull --prefix tools/xml-schemer https://github.com/GeoscienceAustralia/xml-schemer master --squash

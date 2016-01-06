#!/usr/bin/env bash

steps=(
       './examples/validate.sh'
       './deploy-documentation.sh'
      )

outcome=0

for step in ${steps[@]}; do
    outcome+=eval ${step}
done

exit ${outcome}


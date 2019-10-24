#!/usr/bin/env bash

steps=(
       './run-tests.sh'
       'mvn deploy'
       # './deploy-documentation.sh'
      )

outcome=0

for step in "${steps[@]}"; do
    echo Running: ${step}
    ${step}
    outcome=$?
    if [ $outcome -gt 0 ]; then
        break
    fi
done

exit ${outcome}


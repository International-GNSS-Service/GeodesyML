#!/usr/bin/env bash

if ls ./*.log 1> /dev/null 2>&1; then
    for file in ./*.log; do
        echo $file
        name=${file##*/}
        base=${name%.log}
        xmlFileName=${base%.xml}
        if [ ! -f xmlOutput/${xmlFileName}.xml ]; then 
            printf "\nprocesssing input: ${name} and output ${xmlFileName}.xml\n"    
            python ../log2xml.py -l ${name} -g ../logging.conf -x xmlOutput/${xmlFileName}.xml -v
        fi
    done
fi

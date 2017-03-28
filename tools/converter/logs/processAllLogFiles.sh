#!/usr/bin/env bash

#for file in yar3_20140709.log
for file in ./*.log
do
#    echo "file = " ${file}
    
    name=${file##*/}
#    echo "name = " ${name}

    base=${name%.log}
#    echo "base = " ${base}
    
    xmlFileName=${base%.xml}
#    echo "xmlFileName = " ${xmlFileName}.xml
    
    # check if the file exists    
    if [ ! -f xmlOutput/${xmlFileName}.xml ]; 
        then 
#            printf "\nprocesssing input: ${name} and output ${xmlFileName}.xml\n"    
            python ../log2xml.py -l ${name} -g ../logging.conf -x xmlOutput/${xmlFileName}.xml -v
    fi

done

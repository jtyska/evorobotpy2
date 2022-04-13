#!/bin/bash

listVar="xhopper xant xhalfcheetah xhopperv0 xantv0 xhalfcheetahv0"

for exp in $listVar; do
   cd $exp
   for i in {1..10}; do python3 ~/evorobotpy2/bin/es.py -f $(echo $exp | grep -oP '(?<=x)[^v0]*').ini -g bestgS$i.npy -p; done
   cd ..
done


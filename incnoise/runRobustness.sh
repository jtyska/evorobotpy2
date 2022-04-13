#!/bin/bash

dirList="incnoise0102 incnoise0102-steps incnoise0104 incnoise0106 incnoise-fix01 incnoise-fix02 incnoise-fix03 incnoise-fix04 incnoise-fix05 incnoise-fix06 incnoise-fixed incnoisegen06 incnoisegen08"
taskList="xant xantv0 xhalfcheetah xhalfcheetahv0 xhopper xhopperv0 xwalker xwalkerv0 xhumanoid xhumanoidv0"

for exp in $dirList; do
   for task in $taskList; do
      mv ./$exp/$task ./${exp}_$task
      #rm $exp -rf
   done
done

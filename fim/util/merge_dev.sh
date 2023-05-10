#!/bin/bash

# Merge production graphs
ADS="Network-dev RENC UKY LBNL AL2S"
AD_LOCATION="/Users/ibaldin/workspace-fabric/aggregate-ads/ARMs"
BASE_COMMAND="python ./fim_util.py -m "

for ad in $ADS; do
  # generate command
  BASE_COMMAND+="-f ${AD_LOCATION}/${ad}.graphml "
done
echo $BASE_COMMAND
eval $BASE_COMMAND

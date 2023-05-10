#!/bin/bash

# Merge production graphs
ADS="Network-production EDC NCSA TACC STAR MAX WASH MICH SALT DALL MASS UTAH UCSD CLEM FIU AL2S GPN CERN INDI"
#ADS="Network-production NCSA TACC STAR MAX WASH MICH SALT DALL UTAH MASS FIU UCSD"
#ADS="Network-production NCSA TACC STAR MAX WASH EDC"
#ADS="Network-production NCSA EDC"
AD_LOCATION="/Users/ibaldin/workspace-fabric/aggregate-ads/ARMs"
BASE_COMMAND="python ./fim_util.py -m "

for ad in $ADS; do
  # generate command
  BASE_COMMAND+="-f ${AD_LOCATION}/${ad}.graphml "
done
echo $BASE_COMMAND
eval $BASE_COMMAND

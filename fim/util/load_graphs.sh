#!/bin/bash

graph_files="network-am-ad.graphml site-2-am-1broker-ad.graphml site-3-am-1broker-ad.graphml site-am-2broker-ad.graphml"
#graph_files="network-am-ad.graphml site-am-2broker-ad.graphml"
enum_suffix="-enum.graphml"
FIM_UTIL="python fim_util.py"

for gf in $graph_files; do
	gf_name=`echo $gf | cut -d . -f 1`
	enum_name=$gf_name$enum_suffix
	echo Enumerating $gf into $enum_name
	$FIM_UTIL -e -f $gf -o $enum_name
	echo Load $enum_name
	$FIM_UTIL -l -f $enum_name
done

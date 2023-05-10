#!/bin/bash

source /usr/local/bin/virtualenvwrapper.sh

venv=fbric-infmodel
wss=`workon`

venv_not_exist=true

for ws in $wss; do
	if [ ${venv} == ${ws} ]; then
		venv_not_exist=false
	fi
done

if ! $venv_not_exist; then
	echo Exist
else
	echo Not Exist
fi

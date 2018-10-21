#!/bin/bash

# variables
TIMRC_FILE="$HOME/.timrc"

#
#	$1 -> name of config variable
#	$2 -> value of config variable
#
set_timrc_var () {
	if [ ! -f /tmp/foo.txt ]; then
		touch $TIMRC_FILE
	fi
	if [[ -z "`cat ~/.timrc | grep -E "export[:space:]*" | grep "$1="`" ]]; then
		echo "export $1=\"$2\"" >> $TIMRC_FILE
	else
		value="`echo $2 | sed "s=/=\\\\\/=g"`"
		vim $TIMRC_FILE "+%s/\\s*export\\s\\+$1=\\zs.*\\ze/\"$value\"/g" '+wq'
	fi
}

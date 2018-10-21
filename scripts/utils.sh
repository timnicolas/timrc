#!/bin/bash

# variables
TIMRC_FILE="$HOME/.timrc"

# arguments
# https://stackoverflow.com/questions/192249/how-do-i-parse-command-line-arguments-in-bash
VERBOSE=false

# save args in variable
args="$@"

POSITIONAL=()
while [[ $# -gt 0 ]]
do
	key="$1"

	case $key in
		-v|--verbose)
		VERBOSE=true
		shift # past argument
		;;
		*)    # unknown option
		POSITIONAL+=("$1") # save it in an array for later
		shift # past argument
		;;
	esac
done
set -- "${POSITIONAL[@]}" # restore positional parameters

# color
EOC="\x1B[0m"
RED="\x1B[31m"
GREEN="\x1B[32m"
YELLOW="\x1B[33m"
BLUE="\x1B[34m"
MAGENTA="\x1B[35m"
CYAN="\x1B[36m"
WHITE="\x1B[37m"
BOLD="\033[1m"
LIGHT="\033[2m"
ITALIC="\033[3m"
ULINE="\033[4m"
F_RED="\x1B[41m"
F_GREEN="\x1B[42m"
F_YELLOW="\x1B[43m"
F_BLUE="\x1B[44m"
F_MAGENTA="\x1B[45m"
F_CYAN="\x1B[46m"
F_WHITE="\x1B[47m"
CLEAR="\033[H\033[2J"

TITLE_S="${GREEN}${BOLD}*** "
TITLE_E=" ***${EOC}\n"
ADD_S="${BLUE}${BOLD} -> "
ADD_E="${EOC}\n"

if $VERBOSE; then
	verbose='cat'
else
	verbose='> /dev/null'
fi

init_timrc () {
	if [ ! -f "$HOME/.zshrc" ]; then
		touch "$HOME/.zshrc"
	fi
	if [ ! -f $TIMRC_FILE ]; then
		touch $TIMRC_FILE
	fi
	if [[ -z "`cat $HOME/.zshrc | grep -E "source[:space:]*" | grep "$TIMRC_FILE"`" ]]; then
		printf "${ADD_S}add source \"$TIMRC_FILE\" in $HOME/.zshrc${ADD_E}" | eval $verbose
		echo "source $TIMRC_FILE" >> $HOME/.zshrc
	fi
}

#
#	$1 -> name of config variable
#	$2 -> value of config variable
#
set_timrc_var () {
	if [ ! -f $TIMRC_FILE ]; then
		touch $TIMRC_FILE
	fi
	if [[ -z "`cat $TIMRC_FILE | grep -E "export[:space:]*" | grep "$1="`" ]]; then
		printf "${ADD_S}add env variable $1 -> $2${ADD_E}" | eval $verbose
		echo "export $1=\"$2\"" >> $TIMRC_FILE
	else
		printf "${ADD_S}update env variable $1 -> $2${ADD_E}" | eval $verbose
		value="`echo $2 | sed "s=/=\\\\\/=g"`"
		vim $TIMRC_FILE "+%s/\\s*export\\s\\+$1=\\zs.*\\ze/\"$value\"/g" '+wq'
	fi
	export $1="$2"
}

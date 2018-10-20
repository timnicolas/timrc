#!/bin/bash

# usage
USAGE="./install.sh [-h|--help] [-v|--verbose] [--novim] [--nozsh]
 -> [-h|--help]: print usage
 -> [-v|--verbose]: verbose mode
 -> [--novim]: dont install vim config
 -> [--nozsh]: dont install zsh config
"

# arguments
# https://stackoverflow.com/questions/192249/how-do-i-parse-command-line-arguments-in-bash
ZSH=true
VIM=true
VERBOSE=false

# save args in variable
args="$@"

POSITIONAL=()
while [[ $# -gt 0 ]]
do
	key="$1"

	case $key in
		--novim)
		VIM=false
		shift # past argument
		;;
		--nozsh)
		ZSH=false
		shift # past argument
		;;
		-v|--verbose)
		VERBOSE=true
		shift # past argument
		;;
		-h|--help)
		echo "$USAGE"
		exit 0
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

if $VERBOSE; then
	verbose='cat'
else
	verbose='> /dev/null'
fi


# init submodules
printf "${TITLE_S}init submodules${TITLE_E}"
git submodule init | eval $verbose
git submodule update | eval $verbose


# install zsh
if $ZSH; then
	printf "${TITLE_S}install zsh${TITLE_E}"
	sh zsh/install_zsh.sh $args
fi


# install vim
if $VIM; then
	printf "${TITLE_S}install vim${TITLE_E}"
	sh vim/install_vim.sh $args
fi

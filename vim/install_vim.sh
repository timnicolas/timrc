#!/bin/zsh

# variables
DIR="`git rev-parse --show-toplevel`/vim"
if [ ! -d "$DIR" ]; then
	DIR="`git rev-parse --show-toplevel`"
fi
TIMRC_VIM_FILE="$DIR/timrc.vim"

# usage
USAGE="./install.sh [-h|--help] [-v|--verbose]
 -> [-h|--help]: print usage
 -> [-v|--verbose]: verbose mode
"

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

source $DIR/../scripts/utils.sh $args

if $VERBOSE; then
	verbose='cat'
else
	verbose='> /dev/null'
fi

# init timrc
printf "${TITLE_S}init timrc vim${TITLE_E}"
init_timrc
set_timrc_var "TIMRC_VIM" "$DIR"

# install vim config
if [ ! -f "$HOME/.vimrc" ]; then
	touch "$HOME/.vimrc"
fi
if [[ -z "`cat $HOME/.vimrc | grep -E "source[[:space:]]*" | grep "$TIMRC_VIM_FILE"`" ]]; then
	printf "${ADD_S}add source \"$TIMRC_VIM_FILE\" in $HOME/.vimrc${ADD_E}" | eval $verbose
	echo "source $TIMRC_VIM_FILE" >> $HOME/.vimrc
fi

# install plugin vim
printf "${TITLE_S}install vim plugins${TITLE_E}"
if [ ! -d "$HOME/.vim/bundle/Vundle.vim" ]; then
	git clone https://github.com/gmarik/Vundle.vim.git ~/.vim/bundle/Vundle.vim | eval $verbose
fi

vim '+PluginInstall' '+q' '+q'

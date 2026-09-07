#!/bin/zsh

# usage
USAGE="./install.sh [-h|--help] [-v|--verbose] [--novim] [--nozsh] [--notmux] [--nonvim] [--notodo]
 -> [-h|--help]: print usage
 -> [-v|--verbose]: verbose mode
 -> [--novim]: dont install vim config
 -> [--nozsh]: dont install zsh config
 -> [--notmux]: dont install tmux config
 -> [--nonvim]: dont install nvim config
 -> [--notodo]: dont install todo config
"

# arguments
# https://stackoverflow.com/questions/192249/how-do-i-parse-command-line-arguments-in-bash
ZSH=true
VIM=true
TMUX=true
NVIM=true
TODO=true
LINT=true
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
		--notmux)
		TMUX=false
		shift # past argument
		;;
		--nonvim)
		NVIM=false
		shift # past argument
		;;
		--notodo)
		TODO=false
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

# source utils file
source scripts/utils.sh $args

if $VERBOSE; then
	verbose='cat'
else
	verbose='> /dev/null'
fi

# init timrc
printf "${TITLE_S}init timrc${TITLE_E}"
init_timrc
set_timrc_var "TIMRC" "`git rev-parse --show-toplevel`"

# install zsh
if $ZSH; then
	printf "${TITLE_S}install zsh${TITLE_E}"
	zsh zsh/install_zsh.sh $args
fi

# install vim
if $VIM; then
	printf "${TITLE_S}install vim${TITLE_E}"
	zsh vim/install_vim.sh $args
fi

# install nvim
if $NVIM; then
	printf "${TITLE_S}install nvim${TITLE_E}"
	zsh nvim/install_nvim.sh $args
fi

# install tmux
if $TMUX; then
	printf "${TITLE_S}install tmux${TITLE_E}"
	zsh tmux/install_tmux.sh $args
fi

# install todo
if $TODO; then
	printf "${TITLE_S}install todo${TITLE_E}"
	zsh todo/install_todo.sh $args
fi

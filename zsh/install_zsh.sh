#!/bin/zsh

# variables
DIR="`git rev-parse --show-toplevel`/zsh"
if [ ! -d "$DIR" ]; then
	DIR="`git rev-parse --show-toplevel`"
fi
TIMRC_ZSH_FILE="$DIR/timrc.zsh"

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
printf "${TITLE_S}init timrc zsh${TITLE_E}"
init_timrc
set_timrc_var "TIMRC_ZSH" "$DIR"

# add source to zsh config
if [[ -z "`cat $HOME/.timrc | grep -E "source[[:space:]]*" | grep "$TIMRC_ZSH_FILE"`" ]]; then
	printf "${ADD_S}add source \"$TIMRC_ZSH_FILE\" in $HOME/.timrc${ADD_E}" | eval $verbose
	echo "source $TIMRC_ZSH_FILE" >> $HOME/.timrc
fi

cp $DIR/radare2rc ~/.radare2rc

# install plugin zsh + oh-my-zsh
printf "${TITLE_S}install oh-my-zsh plugins${TITLE_E}"
if ! [ -d "${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/plugins/zsh-autosuggestions" ]; then
	printf "${ADD_S}add plugin zsh-autosuggestions${ADD_E}" | eval $verbose
	git clone https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/plugins/zsh-autosuggestions | eval $verbose
fi

if ! [ -d "${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting" ]; then
	printf "${ADD_S}add plugin zsh-syntax-highlighting${ADD_E}" | eval $verbose
	git clone https://github.com/zsh-users/zsh-syntax-highlighting.git ${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting | eval $verbose
fi

if ! [ -d "${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/plugins/zsh-iterm-touchbar" ]; then
	printf "${ADD_S}add plugin zsh-iterm-touchbar${ADD_E}" | eval $verbose
	git clone https://github.com/iam4x/zsh-iterm-touchbar.git ${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/plugins/zsh-iterm-touchbar | eval $verbose
fi

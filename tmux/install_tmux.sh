#!/bin/zsh

# variables
DIR="`git rev-parse --show-toplevel`/tmux"
if [ ! -d "$DIR" ]; then
	DIR="`git rev-parse --show-toplevel`"
fi
TIMRC_TMUX_FILE="$DIR/tmux.conf"
TMUX_CONF="$HOME/.tmux.conf"
TPM_DIR="$HOME/.tmux/plugins/tpm"

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
printf "${TITLE_S}init timrc tmux${TITLE_E}"
init_timrc
set_timrc_var "TIMRC_TMUX" "$DIR"

# install tmux config
if [ ! -f "$TMUX_CONF" ]; then
	touch "$TMUX_CONF"
fi
if [[ -z "`cat $TMUX_CONF | grep -E "source-file *" | grep "$TIMRC_TMUX_FILE"`" ]]; then
	printf "${ADD_S}add source-file \"$TIMRC_TMUX_FILE\" in $TMUX_CONF${ADD_E}" | eval $verbose
	echo "source-file \"$TIMRC_TMUX_FILE\"" >> $TMUX_CONF
fi

# install tmux plugin manager (TPM) + plugins
printf "${TITLE_S}install tmux plugins${TITLE_E}"
if [ ! -d "$TPM_DIR" ]; then
	git clone https://github.com/tmux-plugins/tpm "$TPM_DIR" | eval $verbose
fi

# headless install, does not need a running tmux server (see tpm/bin/install_plugins)
"$TPM_DIR/bin/install_plugins" | eval $verbose

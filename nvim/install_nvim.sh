#!/bin/zsh

# variables
DIR="`git rev-parse --show-toplevel`/nvim"
if [ ! -d "$DIR" ]; then
	DIR="`git rev-parse --show-toplevel`"
fi
TIMRC_NVIM_FILE="$DIR/init.vim"
NVIM_CONF_DIR="$HOME/.config/nvim"
NVIM_CONF="$NVIM_CONF_DIR/init.vim"

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
printf "${TITLE_S}init timrc nvim${TITLE_E}"
init_timrc
set_timrc_var "TIMRC_NVIM" "$DIR"

# install nvim config (réutilise timrc.vim, cf $TIMRC_VIM_FILE)
if [ ! -d "$NVIM_CONF_DIR" ]; then
	mkdir -p "$NVIM_CONF_DIR"
fi
if [ ! -f "$NVIM_CONF" ]; then
	touch "$NVIM_CONF"
fi
if [[ -z "`cat $NVIM_CONF | grep -E "source *" | grep "$TIMRC_NVIM_FILE"`" ]]; then
	printf "${ADD_S}add source \"$TIMRC_NVIM_FILE\" in $NVIM_CONF${ADD_E}" | eval $verbose
	echo "source $TIMRC_NVIM_FILE" >> $NVIM_CONF
fi

# clone les plugins (lazy.nvim) en headless, via son API lua plutot que la commande interactive
# ":Lazy sync" (bloquante en headless, pas d'UI). La plupart des plugins sont charges sur
# l'evenement VeryLazy (~UIEnter, qui ne se declenche jamais en headless) donc leur config()
# ne tourne pas ici -> c'est attendu, elle tourne normalement au premier vrai lancement interactif.
# Pareil pour les parsers treesitter et les serveurs LSP (mason) : installes automatiquement,
# avec une UI visible, au premier vrai lancement interactif de nvim.
printf "${TITLE_S}install nvim plugins${TITLE_E}"
nvim --headless "+source $NVIM_CONF" -c "lua require('lazy').sync({wait=true, show=false})" -c "qa" | eval $verbose

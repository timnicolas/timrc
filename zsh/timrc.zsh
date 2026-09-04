# source colors
source "$TIMRC_ZSH/color.zsh"

export LC_ALL=en_US.UTF-8
export PATH=$PATH:/usr/local/Cellar/gettext/0.20.1/bin:/opt/homebrew/bin

# theme for zsh
# default theme "robbyrussell"
ZSH_THEME="fino"

# use oh-my-zsh
export ZSH=$HOME/.oh-my-zsh
plugins=(
		git
		zsh-autosuggestions
		z
		colored-man-pages
		zsh-syntax-highlighting # must be the last plugin
	)

DISABLE_UPDATE_PROMPT=true  # auto update ohmyzsh
# DISABLE_AUTO_UPDATE=true  # never update ohmyzsh

source $ZSH/oh-my-zsh.sh

ZSH_AUTOSUGGEST_STRATEGY=(history completion)

# use xterm-256color
export TERM=xterm-256color
# use vim in git (default editor for commit)
export GIT_EDITOR=vim

# alias
if [ ! -z $TIMRC ]; then
	alias timrc="cd $TIMRC"
fi
if [ ! -z $TIMRC_ZSH ]; then
	alias timrc_zsh="cd $TIMRC_ZSH"
fi
if [ ! -z $TIMRC_VIM ]; then
	alias timrc_vim="cd $TIMRC_VIM"
	alias vimrc="vim ~/.vimrc $TIMRC_VIM/timrc.vim $TIMRC_VIM/vimrc/*.vim"
else
	alias vimrc="vim ~/.vimrc"
fi
alias zshrc="vim ~/.zshrc ~/.timrc $TIMRC_ZSH/timrc.zsh && source ~/.zshrc"

# bindkey for use opt+right instead of ctrl+right
bindkey "^[^[[C" forward-word
bindkey "^[^[[D" backward-word

# tabs = 4 spaces
tabs -4

# alias to open vscode -> code <folder>
alias code="/Applications/Visual\ Studio\ Code.app/Contents/Resources/app/bin/code"

# --- custom prompt (fino-based, repainted with timrc palette) ---
autoload -U add-zsh-hook
zmodload zsh/datetime

function _timrc_preexec() {
	_timrc_cmd_start=$EPOCHREALTIME
}

function _timrc_format_duration() {
	local d=$1
	if (( d < 1 )); then
		printf "%dms" $(( d * 1000 ))
	elif (( d < 60 )); then
		printf "%.2fs" $d
	elif (( d < 3600 )); then
		printf "%dm%ds" $(( d / 60 )) $(( d % 60 ))
	else
		printf "%dh%dm" $(( d / 3600 )) $(( (d % 3600) / 60 ))
	fi
}

function _timrc_precmd() {
	if [[ -n $_timrc_cmd_start ]]; then
		local elapsed=$(( EPOCHREALTIME - _timrc_cmd_start ))
		_timrc_cmd_time=$(_timrc_format_duration $elapsed)
		unset _timrc_cmd_start
	else
		_timrc_cmd_time=""
	fi
}

add-zsh-hook preexec _timrc_preexec
add-zsh-hook precmd _timrc_precmd

function _timrc_exec_time() {
	[[ -n $_timrc_cmd_time ]] && printf " %s%s%s" "$_TIMRC_DIM" "$_timrc_cmd_time" "$_TIMRC_RST"
}

function virtualenv_prompt_info() {
	[[ -n ${VIRTUAL_ENV} ]] || return
	echo "${ZSH_THEME_VIRTUALENV_PREFIX:=[}${VIRTUAL_ENV:t}${ZSH_THEME_VIRTUALENV_SUFFIX:=]}"
}

# namespaced color snapshots — some plugins/configs overwrite GREEN/RED/BLUE later
_TIMRC_GREEN=$'\033[38;2;78;186;101m'
_TIMRC_RED=$'\033[38;2;255;107;128m'
_TIMRC_YELLOW=$'\033[38;2;230;180;50m'
_TIMRC_TEAL=$'\033[38;2;177;185;249m'
_TIMRC_SHIMMER=$'\033[38;2;235;159;127m'
_TIMRC_ORANGE=$'\033[38;2;215;119;87m'
_TIMRC_DIM=$'\033[2m'
_TIMRC_BOLD=$'\033[1m'
_TIMRC_RST=$'\033[0m'

function _timrc_git_info() {
	local branch
	branch=$(command git symbolic-ref --short HEAD 2>/dev/null) \
		|| branch=$(command git rev-parse --short HEAD 2>/dev/null) \
		|| return

	printf " %s·%s %s%s%s" "$_TIMRC_DIM" "$_TIMRC_RST" "$_TIMRC_TEAL" "$branch" "$_TIMRC_RST"

	# file counts (porcelain v1)
	local status_out staged=0 unstaged=0 untracked=0
	status_out=$(command git status --porcelain 2>/dev/null)
	if [[ -n $status_out ]]; then
		local line
		while IFS= read -r line; do
			local x=${line[1]} y=${line[2]}
			if [[ $x == '?' && $y == '?' ]]; then
				(( untracked++ ))
			else
				[[ $x != ' ' && $x != '?' ]] && (( staged++ ))
				[[ $y != ' ' && $y != '?' ]] && (( unstaged++ ))
			fi
		done <<< "$status_out"
		(( staged > 0 ))    && printf " %s+%d%s" "$_TIMRC_GREEN" "$staged" "$_TIMRC_RST"
		(( unstaged > 0 ))  && printf " %s!%d%s" "$_TIMRC_YELLOW" "$unstaged" "$_TIMRC_RST"
		(( untracked > 0 )) && printf " %s?%d%s" "$_TIMRC_RED" "$untracked" "$_TIMRC_RST"
	else
		printf " %s✔%s" "$_TIMRC_GREEN" "$_TIMRC_RST"
	fi

	# ahead / behind upstream
	local ab
	ab=$(command git rev-list --left-right --count HEAD...@{upstream} 2>/dev/null)
	if [[ -n $ab ]]; then
		local ahead=${ab%%	*} behind=${ab##*	}
		(( ahead > 0 ))  && printf " %s⇡%d%s" "$_TIMRC_GREEN" "$ahead" "$_TIMRC_RST"
		(( behind > 0 )) && printf " %s⇣%d%s" "$_TIMRC_RED" "$behind" "$_TIMRC_RST"
	fi
}

# exit-code indicator: green ✔ on success, red ✘<code> on failure
_exit_indicator="%(?.%{$_TIMRC_GREEN%}✔%{$_TIMRC_RST%}.%{$_TIMRC_RED%}✘%?%{$_TIMRC_RST%})"

PROMPT=" ${_exit_indicator}\$(_timrc_exec_time)\$(virtualenv_prompt_info) %{$_TIMRC_DIM%}·%{$_TIMRC_RST%} %{$_TIMRC_ORANGE$_TIMRC_BOLD%}%~%{$_TIMRC_RST%}\$(_timrc_git_info)
%{$_TIMRC_ORANGE%}\$%{$_TIMRC_RST%} "

export VIRTUAL_ENV_DISABLE_PROMPT=1
ZSH_THEME_VIRTUALENV_PREFIX=" %{$_TIMRC_DIM%}·%{$_TIMRC_RST%} %{$_TIMRC_TEAL%}"
ZSH_THEME_VIRTUALENV_SUFFIX="%{$_TIMRC_RST%}"

#source "$HOME/.cargo/env"

#!/usr/bin/env bash
# Icône d'état Claude Code pour le pane courant d'une fenêtre tmux (appelé par window-status-format,
# cf tmux.conf). ◐ si le contenu du pane a changé depuis le dernier passage (Claude génère/écrit),
# ✳ sinon (idle/waiting — même glyphe que le titre OSC posé par Claude Code). Rien si le pane
# courant ne ressemble pas à un process Claude Code (version x.y.z, même heuristique que
# automatic-rename-format). Basé sur un diff de contenu (via un cache par pane), pas sur
# window_activity : ce dernier est agrégé par FENÊTRE (toutes les panes confondues), donc un pane
# voisin qui bouge (zsh, nvim, un autre Claude) faisait passer l'icône à "actif" en permanence.
set -euo pipefail

IDLE_AFTER_MISSES=2
CACHE_DIR="${TMPDIR:-/tmp}/tmux-claude-state"
mkdir -p "$CACHE_DIR"

pane_id="$1"

cmd=$(tmux display-message -t "$pane_id" -p '#{pane_current_command}' 2>/dev/null) || exit 0
case "$cmd" in
    [0-9]*.[0-9]*.[0-9]*) ;;
    *) exit 0 ;;
esac

hash_now=$(tmux capture-pane -t "$pane_id" -p 2>/dev/null | md5 -q 2>/dev/null) || exit 0
cache_file="$CACHE_DIR/${pane_id#%}"

if [[ ! -f "$cache_file" ]]; then
    echo "$hash_now 0" > "$cache_file"
    printf '✳'
    exit 0
fi

read -r prev misses < "$cache_file"
if [[ "$hash_now" == "$prev" ]]; then
    misses=$((misses + 1))
else
    misses=0
fi
echo "$hash_now $misses" > "$cache_file"

if (( misses < IDLE_AFTER_MISSES )); then
    printf '◐'
else
    printf '✳'
fi

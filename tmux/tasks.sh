#!/usr/bin/env bash

current_dir="${BASH_SOURCE[0]%/*}"
[ "$current_dir" = "${BASH_SOURCE[0]}" ] && current_dir="."
source "$current_dir/../lib/utils.sh"

tasks_icon=$(get_tmux_option "@tmux2k-tasks-icon" "")
todo_file="${HOME}/todo.txt"

main() {
    local count
    if [[ -f "$todo_file" ]]; then
        # grep gardé (pas "todo list") : ~30ms de python/venv par appel, refresh tmux 5s, et list ne sort rien de comptable brut
        count=$(grep -vcE '^(x |$)' "$todo_file" 2>/dev/null) || count=0
        echo "$tasks_icon $count"
    else
        echo "$tasks_icon "
    fi
}

main

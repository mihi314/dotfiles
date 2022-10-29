# Remove history entries on ctrl-d in the fzf history widget
# 1. fzf will call fzf-remove-history-entry with the selected line as the first argument
# 2. That script will remove the entry from the history file, provide fzf the updated list on stdout and touch ${HISTFILE}_do_reload
# 3. The overwritten fzf-history-widget function below will then reload the shell's history to the updated one

script_dir="${0:a:h}"
export FZF_CTRL_R_OPTS="--bind 'ctrl-d:reload:\"$script_dir/fzf-remove-history-entry\" {}'"
unset script_dir


if ! typeset -f fzf-history-widget_orig > /dev/null; then
  functions[fzf-history-widget_orig]=$functions[fzf-history-widget]
fi

# Original function:
# https://github.com/junegunn/fzf/blob/f931e538903a20d7a63162f0f10f58447f1117c8/shell/key-bindings.zsh#L97-L111
fzf-history-widget() {
  fzf-history-widget_orig "$@"
  local ret=$?

  if [[ -f "${HISTFILE}_do_reload" ]]; then 
    # Reload (by pushing onto stack and loading $HISTFILE again)
    # (Doing this only when really needed, in order to not mess up the arrow-up history on each invocation)
    # https://zsh.sourceforge.io/Doc/Release/Shell-Builtin-Commands.html
    # https://www.zsh.org/mla/workers/2020/msg00687.html
    fc -P
    fc -p "$HISTFILE"
    
    rm "${HISTFILE}_do_reload"
  fi

  return $ret
}

if [[ $SSH_CONNECTION ]]; then SSH="%{$fg[red]%}"; else SSH=""; fi

GIT_CB="git::"
ZSH_THEME_SCM_PROMPT_PREFIX="%{$fg[blue]%}["
ZSH_THEME_GIT_PROMPT_PREFIX=$ZSH_THEME_SCM_PROMPT_PREFIX$GIT_CB
ZSH_THEME_GIT_PROMPT_SUFFIX="]%{$reset_color%} "
ZSH_THEME_GIT_PROMPT_DIRTY=" %{$fg[red]%}*%{$fg[blue]%}"
ZSH_THEME_GIT_PROMPT_CLEAN=""

ZSH_THEME_AWS_PREFIX="%{$fg[blue]%}[aws::"
ZSH_THEME_AWS_SUFFIX="]%{$reset_color%} "


PROMPT=$'%{$fg[green]%}%/%{$reset_color%} $(git_prompt_info)$(aws_prompt_info)%{$fg_bold[black]%}[%n@%{$SSH%}%m%{$fg_bold[black]%}]%{$reset_color%} %{$fg_bold[black]%}[%T]%{$reset_color%}
%{$fg_bold[black]%}>%{$reset_color%} '

PROMPT2="%{$fg_blod[black]%}%_> %{$reset_color%}"

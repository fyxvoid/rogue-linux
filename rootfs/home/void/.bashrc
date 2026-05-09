# Rogue Linux bashrc — void user
[ -z "$PS1" ] && return

export PS1='\[\033[01;32m\]\u@rogue\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '
export HISTSIZE=5000
export HISTFILE="$HOME/.bash_history"
export HISTCONTROL=ignoredups:erasedups

alias ls='ls --color=auto'
alias ll='ls -lah --color=auto'
alias grep='grep --color=auto'
alias df='df -h'
alias free='free -h'
alias ..='cd ..'

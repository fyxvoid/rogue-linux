# Rogue Linux — void user profile

export PATH="/usr/bin:/bin:/usr/sbin:/sbin:/home/void/.local/bin"
export HOME="/home/void"
export XDG_RUNTIME_DIR="/run/user/1000"
export XDG_CONFIG_HOME="$HOME/.config"
export XDG_DATA_HOME="$HOME/.local/share"
export EDITOR="vim"
export PAGER="less"
export TERM="xterm-256color"

# Auto-start X on tty1 (only once, not inside an existing X session)
if [ "$(tty)" = "/dev/tty1" ] && [ -z "$DISPLAY" ]; then
    mkdir -p "$XDG_RUNTIME_DIR"
    chmod 700 "$XDG_RUNTIME_DIR"
    exec startx -- :0 vt1 2>/tmp/xorg.log
fi

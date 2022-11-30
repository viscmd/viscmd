viscmd_autocomplete() {
    if content=$(viscmd "$READLINE_LINE"); then
        READLINE_LINE=$content
        READLINE_POINT=${#READLINE_LINE}
    fi  
}

bind -x '"\e[Z": viscmd_autocomplete' 


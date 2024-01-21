viscmd_autocomplete() {
	local cmd=$(viscmd "$READLINE_LINE")
	if [ -n "$cmd" ]; then
		local pos=$((${#cmd} - (${#READLINE_LINE} - $READLINE_POINT)))
		READLINE_LINE=$cmd
		READLINE_POINT=$pos
	fi
}

bind -x '"\e[Z": viscmd_autocomplete'

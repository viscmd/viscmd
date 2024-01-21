viscmd_autocomplete() {
	local cmd=$(viscmd "$BUFFER")
	if [ -n "$cmd" ]; then
		local pos=$((${#cmd} - (${#BUFFER} - $CURSOR)))
		BUFFER=$cmd
		CURSOR=$pos
	fi
}

zle -N viscmd_autocomplete
bindkey "\e[Z" viscmd_autocomplete

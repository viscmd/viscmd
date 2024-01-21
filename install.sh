#!/bin/bash

if [ $USER != root ]; then
	echo "Run as root."
	exec sudo $0
fi

if pip3 show viscmd &>/dev/null; then
	pip3 uninstall -y viscmd
fi
pip3 install .
echo

/bin/cp viscmd.png /usr/share/icons/
/bin/cp viscmd.desktop /usr/share/applications/
/bin/cp viscmd-completion-*.sh /usr/local/bin
chmod +x /usr/local/bin/viscmd-completion-*.sh

test -d /var/lib/viscmd || (mkdir /var/lib/viscmd && chown $SUDO_USER /var/lib/viscmd)

ok=false
if [ -e /etc/bash_completion.d/ ]; then
	ln -sf /usr/local/bin/viscmd-completion-bash.sh /etc/bash_completion.d/
	echo "bash completion installed to /etc/bash_completion.d/"
	ok=true
else
	echo "WARNING: /etc/bash_completion.d/ not found. Unable to install bash completion script."
fi

zshrc=/etc/zsh/zshrc
if [ -e $zshrc ]; then
	if ! grep -q viscmd-completion-zsh.sh $zshrc; then
		echo 'source /usr/local/bin/viscmd-completion-zsh.sh' >>$zshrc
	fi
	echo "zsh completion installed to $zshrc"
	ok=true
fi

if $ok; then
	echo
	echo "OK. Please re-open the bash/zsh to take effect."
fi

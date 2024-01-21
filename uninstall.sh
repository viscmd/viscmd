#!/bin/bash

if [ $USER != root ]; then
	echo "Run as root."
	exec sudo $0
fi

pip3 uninstall -y viscmd

/bin/rm -f /usr/share/icons/viscmd.png
/bin/rm -f /usr/share/applications/viscmd.desktop
/bin/rm -f /bin/viscmd-completion-*.sh
/bin/rm -fr /var/lib/viscmd
/bin/rm -f /etc/bash_completion.d/viscmd-completion-bash.sh

zshrc=/etc/zsh/zshrc
if [ -e $zshrc ]; then
	if grep -q viscmd-completion-zsh.sh $zshrc; then
		sed -i '/viscmd-completion-zsh.sh/d' $zshrc
	fi
fi



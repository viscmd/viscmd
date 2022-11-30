#!/bin/bash

if [ $USER != root ]; then
  echo "Please run as root."
  exit 1
fi

pip3 install .

/bin/cp viscmd-completion.sh /etc/bash_completion.d/
/bin/cp viscmd.png /usr/share/icons/
/bin/cp viscmd.desktop /usr/share/applications/

test -d /var/lib/viscmd || mkdir /var/lib/viscmd

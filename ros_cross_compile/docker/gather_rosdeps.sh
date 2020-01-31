#!/bin/bash

set -euxo pipefail

[ "${PACKAGE}" ] || (echo "PACKAGE var unset" && exit 1)
[ "${ROSDISTRO}" ] || (echo "ROSDISTRO var unset" && exit 1)

if [ ! -d ./src ]; then
  echo "No src directory found at /root/ws, did you remember to mount your workspace?"
  exit 1
fi

# rosdep update
package_paths=$(colcon list --packages-up-to ${PACKAGE} -p)

rosdep update
rosdep install \
--from-paths ${package_paths} \
--ignore-src \
--simulate \
--rosdistro ${ROSDISTRO} \
> /tmp/rosdep_install_commands

# Collect apt-get install commands into one big command to speed it up a bit
mkdir -p cc_artifacts
echo "apt-get install -y \\" > cc_artifacts/rosdep_apt.sh
chmod +x cc_artifacts/rosdep_apt.sh
# Breaking down this line pipe by pipe:
## get all lines that start with apt-get install
## get the third column (the package name because [apt-get, install, PACKAGE])
## sort them for readability
## append a backslash at the end of all lines except the last
cat /tmp/rosdep_install_commands \
  | sed -n '/^  apt-get install/p' \
  | awk '{ print $3; }' \
  | sort \
  | awk 'NR > 1{print "  "line" \\"}{line=$0;}END{print "  "$0" "}' \
  >> cc_artifacts/rosdep_apt.sh

# Collect the rest of the installation commands into a second script
cat /tmp/rosdep_install_commands \
  | sed -n '/^  apt-get install/!p' \
  > cc_artifacts/rosdep_other.sh
chmod +x cc_artifacts/rosdep_other.sh

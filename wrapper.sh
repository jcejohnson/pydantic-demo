#!/bin/bash

# "all-in-one" wrapper scripts around our CLI (and tox)

self=$(basename $0)

for python in python3.8 python3.9
do
  which ${python} && break
done

if [ ! -d venv ] ; then
  (
    set -x
    ${python} -m venv venv
    venv/bin/pip install --upgrade pip
    venv/bin/pip install pip-tools
  )
  # Force the `if` below to _not_ recomplie requirements*txt so that we
  #   use what the develop has explicitly requested in them.
  # Recompiling them is handy sometimes but a bit obnoxious for a 
  #   reusable library.
  touch requirements.txt dev-requirements.in
fi

[ requirements.in -nt requirements.txt ] && venv/bin/pip-compile requirements.in
[ dev-requirements.in -nt dev-requirements.txt ] && venv/bin/pip-compile dev-requirements.in

[ -x venv/bin/aktorz ] || (set -x ; venv/bin/pip install -e .)

case ${self} in

  bumpversion.sh)
    exec venv/bin/bumpversion "$@"
    ;;

  tox.sh)
    [ -x venv/bin/tox ] || (set -x ; venv/bin/pip install -r dev-requirements.txt)
    exec venv/bin/tox "$@"
    ;;

  wrapper.sh)
    for thing in aktorz tox bumpversion ; do ln -vf ${self} ${thing}.sh ; done
    exit 0
    ;;
esac

if [[ "$1" =~ --* ]] ; then
  exec venv/bin/aktorz "$@"
fi

exec venv/bin/aktorz "${self/.sh}" "$@"

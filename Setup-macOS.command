#!/bin/sh
cd "$(dirname "$0")" || exit 1
sh ./setup.sh "$@"
result=$?
printf '\nPress Enter to close.'
read -r answer
exit "$result"

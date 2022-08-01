#!/bin/bash

set -e

phelp() {
	echo "USAGE: $0 <commit-hash|'root'> <username> <email>"
}

unset() {
	git config --local --unset-all user.name || echo "NOTE: Previous Local Username was not set."
	git config --local --unset-all user.email || echo "NOTE: Previous Local Email was not set."
}

[[ $1 == "" ]] && echo "ERROR: Param commit hash not given. Is required." && phelp && exit 1
[[ $1 == "root" ]] && echo "Param Commmit-hash value root. Changing all commits." && root="--root"

env=0 && [[ $2 == "" && $3 == "" ]] && echo "No user params given. Trying .env file" && env=1

[ $env -eq 0 ] && [[ $2 == "" ]] && echo "ERROR: Param Username not given." && phelp && exit 1
[ $env -eq 0 ] && [[ $3 == "" ]] && echo "ERROR: Param Email not given." && phelp && exit 1

[ $env -eq 1 ] && [ ! -f ./.env ] && echo "ERROR: File .env does not exist." && exit 1
[ $env -eq 1 ] && source ./.env && user=${USER_NAME} && mail=${USER_EMAIL}

unset

git config --local user.name "${user:-$2}"
git config --local user.email "${mail:-$3}"

git stash -a -u

git checkout pub || git checkout -b pub

git reset --hard main

git rebase ${root:-$1} --exec 'git commit --amend --no-edit --reset-author'

git push -u publish pub:main -f

git checkout main

git stash apply && git stash drop || echo "ERROR: Failed to restore stash. Did not drop."

unset

echo "Commit fixing done."

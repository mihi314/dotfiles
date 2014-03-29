#!/bin/bash

# Installs my dotfiles to a new system
# Author: Michael Engelhard

usage="Usage: -f to overwrite existing files."

if [[ $1 = "-f" ]]; then
    overwrite=1
elif [[ $1 ]]; then
    echo "Invalid option '$1'"
    echo "$usage"
    exit 1
fi

bashrc="${HOME}/.bashrc"

if [[ -e $bashrc && ! $overwrite ]]; then
    echo "Did not overwrite existing $bashrc."
else
    echo '. ~/bin/dotfiles/bashrc' > $bashrc
fi

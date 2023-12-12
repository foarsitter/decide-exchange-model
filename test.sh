#!/usr/bin/env bash

set -o errexit
set -o pipefail
set -o nounset

wget https://repo.anaconda.com/miniconda/Miniconda3-py39_23.10.0-1-Linux-x86_64.sh -O miniconda.sh;
bash miniconda.sh -b -p $HOME/miniconda
$HOME/miniconda/bin/conda install -n base --yes conda-build conda-libmamba-solver conda-verify
$HOME/miniconda/bin/conda config --set solver libmamba
$HOME/miniconda/bin/conda create decide
$HOME/miniconda/bin/conda build --numpy 1.23.4 --python 3.9 .
$HOME/miniconda/bin/conda env export > environment.yml
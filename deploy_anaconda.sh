#!/bin/bash
# https://gist.github.com/yoavram/05a3c04ddcf317a517d5
set -o errexit
set -o pipefail
set -o nounset

echo "Installing conda package..."
conda build meta.yaml --no-include-recipe
conda install --use-local decide-exchange-model

echo "Converting conda package..."
conda convert --platform all $HOME/miniconda/conda-bld/linux-64/decide-exchange-model-*.tar.bz2 --output-dir $HOME/miniconda/conda-bld/

echo "Deploying to Anaconda.org..."
anaconda -t $ANACONDA_TOKEN upload $HOME/miniconda/conda-bld/**/decide-exchange-model-*.tar.bz2

echo "Successfully deployed to Anaconda.org."

#!/bin/bash
# https://gist.github.com/yoavram/05a3c04ddcf317a517d5
set -e

echo "Converting conda package..."
conda convert --platform all $HOME/miniconda/conda-bld/linux-64/decide-exchange-model-*.tar.bz2 --output-dir conda-bld/

echo "Deploying to Anaconda.org..."
anaconda -t $ANACONDA_TOKEN upload conda-bld/**/decide-exchange-model-*.tar.bz2

echo "Successfully deployed to Anaconda.org."
exit 0
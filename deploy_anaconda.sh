#!/bin/bash
# https://gist.github.com/yoavram/05a3c04ddcf317a517d5
set -o errexit
set -o pipefail
set -o nounset

echo "Installing conda package..."
conda install -q python=$TRAVIS_PYTHON_VERSION \
    anaconda-client==1.7.2 \
    brotlipy==0.7.0 \
    ca-certificates==2020.12.5 \
    certifi==2020.12.5 \
    cffi==1.14.5 \
    conda-build==3.21.4 \
    conda==4.10.0 \
    cryptography==3.4.7 \
    cython==0.29.17 \
    jinja2==2.11.3 \
    ncurses==6.2 \
    peewee==3.14.4 \
    pip==21.0.1 \
    pyopenssl==20.0.1 \
    pyparsing==2.4.7 \
    pytest==4.6.3 \
    pytz==2021.1 \
    readline==8.1 \
    requests==2.25.1 \
    setuptools==49.6.0 \
    urllib3==1.26.4 \
    wheel==0.36.2

echo "Build conda package..."
conda build meta.yaml --no-include-recipe
conda install --use-local decide-exchange-model
echo "Converting conda package..."
conda convert --platform all $HOME/miniconda/conda-bld/linux-64/decide-exchange-model-*.tar.bz2 --output-dir $HOME/miniconda/conda-bld/

echo "Deploying to Anaconda.org..."
anaconda -t $ANACONDA_TOKEN upload $HOME/miniconda/conda-bld/**/decide-exchange-model-*.tar.bz2

echo "Successfully deployed to Anaconda.org."

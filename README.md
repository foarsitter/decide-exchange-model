[![Build Status](https://travis-ci.org/foarsitter/decide-exchange-model.svg?branch=master)](https://travis-ci.org/foarsitter/decide-exchange-model)
[![Code Climate](https://codeclimate.com/github/foarsitter/decide-exchange-model/badges/gpa.svg)](https://codeclimate.com/github/foarsitter/decide-exchange-model)
[![Test Coverage](https://codeclimate.com/github/foarsitter/decide-exchange-model/badges/coverage.svg)](https://codeclimate.com/github/foarsitter/decide-exchange-model/coverage)
[![Issue Count](https://codeclimate.com/github/foarsitter/decide-exchange-model/badges/issue_count.svg)](https://codeclimate.com/github/foarsitter/decide-exchange-model)

[![Issue Count](https://anaconda.org/jelmert/decide-exchange-model/badges/version.svg)](https://codeclimate.com/github/foarsitter/decide-exchange-model)


# Decide Exchange Model
Equal Gain Model implementation in Python. 

# Installation
The recommend way for un-experienced Python users is to use Anaconda for downloading and installation.

## Anaconda
First, download and install Anaconda: https://docs.anaconda.com/anaconda/, then open the Anaconda navigator and add ```decide``` and ```conda-forge``` to your channels. 
Explanation to manage your channels through the anaconda-navigator can be found here: https://conda.io/docs/user-guide/tutorials/build-apps.html#configuring-navigator
 
The urls for the channels are

```bash
https://anaconda.org/decide
https://anaconda.org/conda-forge
```

The 'decide-exchange-model' is now avaiable for installation on your Home screen of the Anaconda Navigator.

## PyPi
There is also an package available on pypi.org: https://pypi.org/project/decide-exchange-model/
```
pip install decide-exchange-model
```
After installation ```decide-gui``` and `decide-cli` are available on your path. Type `decide-cil --help` for instructions for usage of the commandline tool. 
# Build cycles
Guide to release a new build
## On PyPI
```
python setup.py sdist
twine upload dist/*
```

## On Anaconda Cloud
The current build cycle uses git as source. So make sure the latest changes are present on master.
```
conda build meta.yaml -c conda-forge --prefix-length 128 # prefix-length cannot be 255 on systems with full disk encryption (fde)

cd ~/anaconda3/conda-bld

conda convert --platform all <path_to_file> -o .

anaconda upload win-64/* 
```



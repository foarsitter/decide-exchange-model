[![Build Status](https://travis-ci.org/foarsitter/decide-exchange-model.svg?branch=master)](https://travis-ci.org/foarsitter/decide-exchange-model)
[![Code Climate](https://codeclimate.com/github/foarsitter/decide-exchange-model/badges/gpa.svg)](https://codeclimate.com/github/foarsitter/decide-exchange-model)
[![Test Coverage](https://codeclimate.com/github/foarsitter/decide-exchange-model/badges/coverage.svg)](https://codeclimate.com/github/foarsitter/decide-exchange-model/coverage)
[![Issue Count](https://codeclimate.com/github/foarsitter/decide-exchange-model/badges/issue_count.svg)](https://codeclimate.com/github/foarsitter/decide-exchange-model)

# decide-exchange-model
Equal Gain Model implementation in Python

There are no external packages needed to run this project but the project is only compatible with python3

Run 'python model.py --help' for instructions
  
# Documentation 
The documentation can be found on https://foarsitter.github.io/decide-exchange-model/build/html/

# Installation
Make sure you have Python (3.5 or higher) installed.

Windows users need to add the python executable to their PATH variable. 

Open a console and type `python --version`. If this gives a not found error python is not correctly installed or not available on the path

If you are on Windows, the executable needs to be added to the PATH variable. In python 3.6 this is an option of the installation.

If you know the installation directory of Python you can also use the full path of the executable. In my case on windows: `C:\python-3.6.0\python`. On Ubuntu 16.04: `/usr/bin/python3`.

Run `python model.py --help` for the optional arguments.

This displays the following message:
```shell
usage: model.py [-h] [--model MODEL] [--rounds ROUNDS] [--input INPUT]
                [--output OUTPUT]

This program accepts input with a dot (.) as decimal separator. Parameters: #A
is for defining an actor, #P for an issue, #D for actor values for each issue.
We expect for #D the following order in values: actor, issue, position,
salience, power

optional arguments:
  -h, --help       show this help message and exit
  --model MODEL    The type of the model. The options are "equal" for the
                   Equal Gain model and "random" for the RandomRate model
  --rounds ROUNDS  The number of round the model needs to be executed
  --input INPUT    The location of the csv input file.
  --output OUTPUT  Output directory
```
You are up to go! 

# Example 
python model.py --rounds 2 --input --output

There are a view input data files where you can play with. The unit tests are based on `data/input/data_short.csv`. But since the model is not full deterministic the results may vary a little bit.

# Readings
Some papers to read about this type of model.


# Build cycles
Guide to release a new build
## On PyPI
```
python setup.py sdist
twine upload dist/*
```

## For Anaconda
The current build cycle uses git as source. So make sure the latest changes are present on master.
```
conda build meta.yaml -c conda-forge --prefix-length 128 # prefix-length cannot be 255 on systems with full disk encryption (fde)
```


# Installation 

## PyPI
```bash
pip install decide-exchange-model
```
After installation,```decide-gui``` and ```decide-cli``` are available on the commandline 

## anaconda
Add ```decide``` and ```conda-forge``` to your channels. Explanation to manage your channels through the anaconda-navigator can be found here: https://conda.io/docs/user-guide/tutorials/build-apps.html#configuring-navigator
 
The urls for the channels are

```bash
https://anaconda.org/decide
https://anaconda.org/conda-forge
```
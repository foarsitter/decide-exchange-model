[![Build Status](https://travis-ci.org/foarsitter/equal-gain-python.svg?branch=master)](https://travis-ci.org/foarsitter/equal-gain-python)
[![Code Climate](https://codeclimate.com/github/foarsitter/equal-gain-python/badges/gpa.svg)](https://codeclimate.com/github/mrJelmert/equal-gain-python)
[![Test Coverage](https://codeclimate.com/github/foarsitter/equal-gain-python/badges/coverage.svg)](https://codeclimate.com/github/mrJelmert/equal-gain-python/coverage)
[![Issue Count](https://codeclimate.com/github/foarsitter/equal-gain-python/badges/issue_count.svg)](https://codeclimate.com/github/mrJelmert/equal-gain-python)

# equal-gain-python
Equal Gain Model implementation in Python

There are no external packages needed. 

This program is build with the latest python version: 3.6.0 and uses
type hinting: https://docs.python.org/3/library/typing.html, 
therefore, it wil require python 3.5 or higher. 

Run 'python model.py --help' for instructions 
  
# Documentation 
The documentation can be found on https://foarsitter.github.io/equal-gain-python/build/html/

# Installation
Make sure you have Python 3.5 or higher installed. 

Windows users need to add the python executable to their PATH variable. 

Open a console and type `python --version`. If this gives an error python is not correctly installed. 

If you are on Windows, the executable needs to be added to the PATH variable. 

If you know the installation directory of Python you can also use the full path of the executable. In my case: `C:\python-3.6.0\python model.py --help`. This displays the following message: 
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
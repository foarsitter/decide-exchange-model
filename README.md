[![Build Status](https://travis-ci.org/foarsitter/decide-exchange-model.svg?branch=master)](https://travis-ci.org/foarsitter/decide-exchange-model)
[![Code Climate](https://codeclimate.com/github/foarsitter/decide-exchange-model/badges/gpa.svg)](https://codeclimate.com/github/foarsitter/decide-exchange-model)
[![Test Coverage](https://codeclimate.com/github/foarsitter/decide-exchange-model/badges/coverage.svg)](https://codeclimate.com/github/foarsitter/decide-exchange-model/coverage)
[![Issue Count](https://codeclimate.com/github/foarsitter/decide-exchange-model/badges/issue_count.svg)](https://codeclimate.com/github/foarsitter/decide-exchange-model)

[![Anaconda-Server Badge](https://anaconda.org/jelmert/decide-exchange-model/badges/version.svg)](https://anaconda.org/jelmert/decide-exchange-model)


# Decide Exchange Model
Equal Gain Model implementation in the Python programming language. 

# Installation
The recommend way for un-experienced Python users is to use Anaconda for downloading and installation. For more experienced users there is a PyPi packages available.

## Anaconda 
[![Anaconda-Server Badge](https://anaconda.org/jelmert/decide-exchange-model/badges/installer/conda.svg)](https://conda.anaconda.org/jelmert)

Anaconda is a platform for managing your environment through a nice graphical interface. It makes the process of software distribution a lot easier.   

- First, download and install Anaconda: https://docs.anaconda.com/anaconda/
- Then open the Anaconda navigator https://docs.anaconda.com/anaconda/user-guide/getting-started#open-navigator
- Add ```decide``` and ```conda-forge``` to your channels. An explanation to manage your channels through the anaconda-navigator can be found here: https://conda.io/docs/user-guide/tutorials/build-apps.html#configuring-navigator
     
    The urls for the channels are

    ```bash
    https://anaconda.org/jelmert
    https://anaconda.org/conda-forge
    ```

The 'decide-exchange-model' is now available for installation on your Home screen of the Anaconda Navigator and can be launched.

### Update through the Anaconda navigator

- Go to 'environments', and click the ```update packages```
- After completion, go back to the home screen
- The version information is now blue with an upward arrow if there is an update available. 
- Click the ```cog``` icon at the top right of the tile and click `update`

## PyPi
There is also an package available on pypi.org: https://pypi.org/project/decide-exchange-model/
```
pip install decide-exchange-model
```
After installation ```decide-gui``` and `decide-cli` are available on your path. Type `decide-cli --help` for instructions for usage of the commandline tool. 
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
conda build meta.yaml --no-include-recipe -c conda-forge --prefix-length 128 # prefix-length cannot be 255 on systems with full disk encryption (fde)

cd ~/anaconda3/conda-bld

conda convert --platform all <path_to_file> -o .

anaconda upload win-64/* 
```



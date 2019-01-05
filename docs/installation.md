# Installation
The recommend way for un-experienced Python users is to use Anaconda for downloading and installation. For more experienced users there is a PyPi packages available.

## Anaconda 
[![Anaconda-Server Badge](https://anaconda.org/jelmert/decide-exchange-model/badges/installer/conda.svg)](https://conda.anaconda.org/jelmert)

Installation tutorial of ASONAM 2018 [Installation instructions Decide exchange model](http://stokman.org/artikel/2018%20Augustus%20Installation%20instructions%20Decide%20exchange%20model.pdf)

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
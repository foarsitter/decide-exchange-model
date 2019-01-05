import logging
import os
import subprocess
import sys

__version__ = "2019.1.2"


def log_settings():
    """
    Reads the settings file into a string and logs it as info
    """

    settings_file = open("decide-settings.xml")

    settings_content = settings_file.read()

    logging.info(settings_content)


log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'decide.log')


def open_file(path):

    if sys.platform.startswith("darwin"):
        subprocess.call(("open", path))
    elif os.name == "nt":
        os.startfile(path)
    elif os.name == "posix":
        subprocess.call(("xdg-open", path))


def exception_hook(exctype, value, traceback):
    logging.exception(value)
    log_settings()
    open_file(log_file)

    sys._excepthook(exctype, value, traceback)
    sys.exit(1)

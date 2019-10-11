import logging
import os
import subprocess
import sys
import traceback

from PyQt5 import QtWidgets

from decide.qt import app


def open_file_natively(path):
    if sys.platform.startswith("darwin"):
        subprocess.call(("open", path))
    elif os.name == "nt":
        os.startfile(path)
    elif os.name == "posix":
        subprocess.call(("xdg-open", path))


def exception_hook(exctype, ex, _traceback):
    """
    Setting the system exception hook so the exception will be logged and the log file displayed
    """

    tb_text = exception_to_string(ex)
    logging.exception(tb_text)

    from decide.qt.mainwindow.errordialog import ErrorDialog

    error_dialog = ErrorDialog(tb_text, parent=app)
    sys.exit(error_dialog.exec_())


def exception_to_string(ex):
    tb_lines = traceback.format_exception(ex.__class__, ex, ex.__traceback__)
    tb_text = "".join(tb_lines)
    return tb_text


def show_user_error(self, message: str):
    QtWidgets.QMessageBox.about(self, "Input data invalid", str(message))

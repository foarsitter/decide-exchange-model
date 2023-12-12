from PyQt5 import QtCore

from decide.qt.inputwindow.gui import InputWindow, register_app


def test_actor_widget_add_button(qtbot):
    x = InputWindow()
    register_app(x)

    assert x.actor_widget._row_pointer == 1, 'Only the heading is shown'
    assert x.actor_widget.grid_layout.rowCount() == 1

    qtbot.mouseClick(x.actor_widget.add_button, QtCore.Qt.LeftButton)

    assert x.actor_widget.grid_layout.rowCount() == 2, 'The heading and an empty row is shown'

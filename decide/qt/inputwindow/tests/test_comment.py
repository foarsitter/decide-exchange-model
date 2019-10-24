from PyQt5 import QtCore

from decide.qt.inputwindow.gui import InputWindow, register_app


def test_actor_widget_add_button(qtbot):
    x = InputWindow()
    register_app(x)

    assert x.actor_widget._row_pointer == 1, 'Only the heading is shown'
    assert x.actor_widget.grid_layout.rowCount() == 1

    qtbot.mouseClick(x.actor_widget.add_button, QtCore.Qt.LeftButton)

    assert x.actor_widget.grid_layout.rowCount() == 2, 'The heading and an empty row is shown'

# FIX killing the window
# def test_comment_button(qtbot):
#     x = ActorWidget()
#
#     x.add_actor('PyTest', 1)
#
#     assert x._row_pointer == 2, "Only the heading and an actor"
#
#     comment_button = x.grid_layout.itemAtPosition(1, 2).widget()
#
#     qtbot.mouseClick(comment_button, QtCore.Qt.LeftButton)
#
#     assert comment_button
#
#
# def test_load_comment(qtbot):
#     x = InputWindow()
#     register_app(x)
#
#     x.load_sample_data()
#
#     comment_button = x.actor_widget.grid_layout.itemAtPosition(1, 2).widget()
#
#     qtbot.mouseClick(comment_button, QtCore.Qt.LeftButton)
#
#     assert True, 'Will fail on the mouse click'

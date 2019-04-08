from decimal import Decimal

from PyQt5 import QtWidgets


def clear_layout(layout):
    """
    Clear al the widgets recursively
    :param layout:
    :return:
    """
    if layout is not None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                clear_layout(item.layout())


class DoubleInput(QtWidgets.QLineEdit):
    def __init__(self):
        super(DoubleInput, self).__init__()

        self.setFixedWidth(75)

    def setValue(self, value: Decimal):
        if isinstance(value, Decimal):
            value = str(float(value.normalize()))

        self.setText(value)

    @property
    def valueChanged(self):
        return self.textChanged


def esc(value):
    return "'{}'".format(value)


def normalize(value):

    if isinstance(value, Decimal):
        # float converts exponential values to readable values
        return str(float(value.normalize()))

    if isinstance(value, float):
        return str(value)

    return str(value)

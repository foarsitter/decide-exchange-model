from decimal import Decimal

from PyQt6 import QtWidgets
from PyQt6.QtCore import pyqtBoundSignal


def clear_layout(layout) -> None:
    """Clear al the widgets recursively."""
    if layout is not None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                clear_layout(item.layout())


class DoubleInput(QtWidgets.QLineEdit):
    """Helper for double inputs."""

    def __init__(self) -> None:
        super().__init__()

        self.setFixedWidth(75)

    def setValue(self, value: Decimal) -> None:
        if isinstance(value, Decimal):
            value = str(float(value.normalize()))
        if isinstance(value, int):
            value = str(value)
        if isinstance(value, float):
            value = str(value)

        self.setText(value)

    @property
    def valueChanged(self) -> pyqtBoundSignal:
        return self.textChanged


def esc(value) -> str:
    """Escape function used for writing csv files with strings."""
    return f"'{value}'"


def normalize(value) -> str:
    """Normalize a decimal or float to string, used for writing csv files and the input window."""
    if isinstance(value, Decimal):
        # float converts exponential values to readable values
        return str(float(value.normalize()))

    if isinstance(value, float):
        return str(value)

    return str(value)

from decide.qt.mainwindow.gui import DecideMainWindow
from decide.qt.mainwindow.settings import SettingsFormWidget, ProgramSettings


def test_load_settings(qtbot):
    """
    Load settings from ProgramSettings
    """

    program_settings = ProgramSettings()

    main_window = DecideMainWindow()

    salience_weight = 0.99

    program_settings.salience_weight = salience_weight

    assert program_settings.salience_weight == salience_weight

    widget = SettingsFormWidget(program_settings, main_window)
    widget.load()

    assert widget.salience_weight.value() == salience_weight

# def test_save_settings(qtbot):
#     """
#     Can we save settings from the widget to ProgramSettings
#     """
#
#     settings = SettingsFormWidget(None, None)
#     settings.load()
#
#     pytest.fail()

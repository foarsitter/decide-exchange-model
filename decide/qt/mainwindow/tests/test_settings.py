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


def test_model_variations(qtbot):
    program_settings = ProgramSettings()

    program_settings.start = 0.0
    program_settings.stop = 0.0

    assert program_settings.model_variations == ['0.00']

    program_settings.start = 0.0
    program_settings.step = 0.05
    program_settings.stop = 0.10

    assert program_settings.model_variations == ['0.00', '0.05', '0.10']

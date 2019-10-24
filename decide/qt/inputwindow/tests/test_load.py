from decide.qt.inputwindow.gui import InputWindow


def test_load_copenhagen(qtbot):
    """
    Load settings from ProgramSettings
    """

    x = InputWindow()

    x.load_copenhagen()

    assert len(x.actor_issue_widget.actors) == 11
    assert len(x.actor_issue_widget.issues) == 7
    assert len(x.actor_issue_widget.actor_issues.values()) == 11, "are store nested"

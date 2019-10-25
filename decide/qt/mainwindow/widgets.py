from typing import List

from PyQt5 import QtWidgets, QtCore
from decide.data import types
from decide.qt import utils


class InputFilGrid:
    pass


class DynamicFormLayout(QtWidgets.QGridLayout):
    def __init__(self, main_window, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.main_window = main_window
        self.checkboxes = []
        self.objects = []
        self.row_pointer = 0

        self.setAlignment(QtCore.Qt.AlignTop)

    def clear(self):
        """
        Set the parent of all child widgets to None so they will be deleted
        """
        for i in reversed(range(self.count())):
            self.itemAt(i).widget().setParent(None)

    def add_row(self, *widgets):

        for index, widget in enumerate(widgets):
            self.addWidget(widget, self.row_pointer, index)

        self.row_pointer += 1

    def set_values(self, objects):
        self.objects = objects
        self.objects.sort()
        self.clear()

    def get_selected(self):

        selected = []

        for checkbox in self.checkboxes:  # type: QtWidgets.QCheckBox
            if checkbox.isChecked():
                selected.append(checkbox.objectName())

        return selected


class IssueWidget(DynamicFormLayout):
    """
    Form layout for customizing the Issue selection
    """

    def set_issues(self, issues: List[types.PartialIssue]):
        self.set_values(issues)
        self.add_row(QtWidgets.QLabel('Issue'), QtWidgets.QLabel('Lower'), QtWidgets.QLabel('Upper'))
        for issue in issues:
            checkbox = QtWidgets.QCheckBox(issue.name)

            lower = QtWidgets.QLabel(str(round(issue.lower, 2)))
            upper = QtWidgets.QLabel(str(round(issue.upper, 2)))

            checkbox.setObjectName(issue.name)
            checkbox.stateChanged.connect(self.state_changed)

            if (
                    issue in self.main_window.settings.selected_issues
                    or len(self.main_window.settings.selected_issues) == 0
            ):
                checkbox.setChecked(True)

            self.checkboxes.append(checkbox)

            self.add_row(checkbox, lower, upper)

    def state_changed(self):
        self.main_window.overview_widget.update_widget()

    def save(self):
        self.main_window.settings.selected_issues = self.get_selected()


class ActorWidget(DynamicFormLayout):
    """
    Form layout for customizing the Actor selection
    """

    def set_actors(self, actors: List[types.PartialActor]):
        self.set_values(actors)

        for actor in actors:
            checkbox = QtWidgets.QCheckBox(str(actor.fullname))
            checkbox.setObjectName(actor.id)

            if (
                    actor in self.main_window.settings.selected_actors
                    or len(self.main_window.settings.selected_actors) == 0
            ):
                checkbox.setChecked(True)

            checkbox.stateChanged.connect(self.state_changed)

            self.checkboxes.append(checkbox)
            self.add_row(checkbox)

    def state_changed(self):
        self.main_window.overview_widget.update_widget()

    def save(self):
        self.main_window.settings.selected_actors = self.get_selected()


class ActorIssueWidget(DynamicFormLayout):

    def __init__(self, *args, **kwargs):
        super(ActorIssueWidget, self).__init__(*args, **kwargs)

    def set_actor_issues(self, actor_issues=List[types.ActorIssue]):
        self.set_values(actor_issues)

        heading = ["Issue", "Actor", "Position", "Salience", "Power"]

        self.add_row(*[QtWidgets.QLabel(x) for x in heading])

        for actor_issue in actor_issues:
            issue = QtWidgets.QLabel(str(actor_issue.issue))
            actor = QtWidgets.QLabel(str(actor_issue.actor))
            position = QtWidgets.QLabel(str(round(actor_issue.position, 2)))
            salience = QtWidgets.QLabel(str(actor_issue.salience))
            power = QtWidgets.QLabel(str(actor_issue.power))

            self.add_row(issue, actor, position, salience, power)


class SummaryWidget(DynamicFormLayout):
    def __init__(
            self, main_window, settings, data, actor_widget, issue_widget, *args, **kwargs
    ):
        """
        :type settings: decide.qt.mainwindow.settings.ProgramSettings
        :type data: decide.qt.mainwindow.gui.ProgramData
        :type actor_widget: decide.qt.mainwindow.widgets.ActorWidget
        :type issue_widget: decide.qt.mainwindow.widgets.IssueWidget
        """
        super(SummaryWidget, self).__init__(main_window, *args, **kwargs)

        self.settings = settings
        self.data = data
        self.actor_widget = actor_widget
        self.issue_widget = issue_widget

    def update_widget(self):

        self.clear()

        self.add_text_row("Input", self.settings.input_filename, self.test_callback)
        self.add_text_row("Output directory", self.settings.output_directory, self.test_callback)

        settings = self.main_window.settings  # type: ProgramSettings

        self.add_text_row("p-values", ", ".join(settings.model_variations))

        output_selection = []

        if settings.issue_development_csv:
            output_selection.append("Issue development values [.csv]")

        if settings.summary_only:
            output_selection.append("Summary only [.csv]")

        if settings.output_sqlite:
            output_selection.append("Sqlite [database]")

        if settings.exchanges_csv:
            output_selection.append("Exchange values [.csv]")

        if settings.externalities_csv:
            output_selection.append("Externalities [.csv]")

        if settings.voting_positions:
            output_selection.append("Show Voting positions [.csv]")

        # self.add_text_row("Output settings", output_selection[0])
        #
        # for setting in output_selection[-1:]:
        #     self.add_text_row("", setting)

        self.main_window.set_start_button_state()

    def add_text_row(self, label, value, callback=None):

        if callback:
            value_label = QtWidgets.QLabel(
                '<a href="{}">...{}/</a>'.format(value, value[-50:])
            )
            value_label.linkActivated.connect(callback)
        else:
            value_label = QtWidgets.QLabel(value)

        self.add_row(QtWidgets.QLabel(label), value_label)

    def test_callback(self, link):
        utils.open_file_natively(link)


class MenuBar(QtWidgets.QMenuBar):
    def __init__(self, main_window, *args, **kwargs):
        """
        :type main_window: decide.qt.mainwindow.gui.DecideMainWindow
        """
        super().__init__(*args, **kwargs)

        self.main_window = main_window
        self.settings = main_window.settings

        file_menu = self.addMenu("&File")
        # output_menu = self.addMenu("&Output")

        self.output_sqlite = QtWidgets.QAction("&sqlite", self)
        self.output_sqlite.setCheckable(True)
        self.output_sqlite.setChecked(True)

        self.issue_development_csv = QtWidgets.QAction("Issue development (.csv)", self)
        self.issue_development_csv.setCheckable(True)
        self.issue_development_csv.setChecked(True)

        self.externalities_csv = QtWidgets.QAction("Externalities (.csv)", self)
        self.externalities_csv.setCheckable(True)
        self.externalities_csv.setChecked(True)

        self.exchanges_csv = QtWidgets.QAction("Exchanges (.csv)", self)
        self.exchanges_csv.setCheckable(True)
        self.exchanges_csv.setChecked(True)

        self.voting_positions = QtWidgets.QAction("Show voting positions", self)
        self.voting_positions.setCheckable(True)
        self.voting_positions.setChecked(True)

        self.summary_only = QtWidgets.QAction("Summary only (.csv)", self)
        self.summary_only.setCheckable(True)
        self.summary_only.setChecked(True)

        self.open_data_view = QtWidgets.QAction("New data file", self)
        self.open_data_view.triggered.connect(self.main_window.open_data_view)

        open_action = QtWidgets.QAction("&Open data file", self)
        open_action.triggered.connect(self.main_window.open_input_data)

        edit_action = QtWidgets.QAction("&Edit data file", self)
        edit_action.triggered.connect(self.main_window.open_current_input_window_with_current_data)

        save_settings = QtWidgets.QAction("&Save settings", self)
        save_settings.triggered.connect(self.main_window.save_settings)

        output_dir_action = QtWidgets.QAction("&Set output directory", self)
        output_dir_action.triggered.connect(self.main_window.select_output_dir)

        # output_menu.addAction(self.issue_development_csv)
        # output_menu.addAction(self.externalities_csv)
        # output_menu.addAction(self.exchanges_csv)
        # output_menu.addSeparator()
        # output_menu.addAction(self.summary_only)
        # output_menu.addAction(self.output_sqlite)
        # output_menu.addAction(self.voting_positions)
        # output_menu.addSeparator()
        # output_menu.addAction(output_dir_action)

        # debug = self.addMenu("Debug")
        log_action = QtWidgets.QAction("Show log window", self)
        log_action.triggered.connect(self.main_window.show_debug_dialog)

        file_menu.addAction(open_action)
        self.recently_opened_menu(file_menu)
        file_menu.addAction(self.open_data_view)
        file_menu.addSeparator()
        file_menu.addAction(edit_action)
        file_menu.addSeparator()
        file_menu.addAction(save_settings)
        file_menu.addAction(output_dir_action)
        file_menu.addSeparator()
        file_menu.addAction(log_action)
        # debug.addAction(log_action)

        # error_report = QtWidgets.QAction("Send error report", self)
        # error_report.triggered.connect(self.main_window.show_error_report_dialog)
        # debug.addAction(error_report)

        # error_report_2 = QtWidgets.QAction("Trigger error", self)
        # error_report_2.triggered.connect(self.trigger_error)
        # debug.addAction(error_report_2)

    def recently_opened_menu(self, menu: QtWidgets.QMenu):
        sub_menu = QtWidgets.QMenu("Recently opened", menu)
        menu.addMenu(sub_menu)

        for item in self.settings.recently_opened:
            action = QtWidgets.QAction(item, self)
            action.triggered.connect(self.open_input_data)
            sub_menu.addAction(action)

    def open_input_data(self):
        sender = self.sender()  # type: QtWidgets.QAction

        self.main_window.init_ui_data(sender.text())

    def trigger_error(self):
        raise Exception("Error triggered")

    def load(self):
        """
        Copy the values from the ProgramSettings object
        """

        settings = self.settings.__dict__.items()

        for key, value in settings:
            if hasattr(self, key):
                attr = getattr(self, key)

                if isinstance(value, bool):  # type: QtWidgets.QAction
                    attr.setChecked(value)
                else:
                    attr.setValue(value)

    def save(self):
        """
        Set the attributes to the ProgramSettings object
        """
        settings = self.__dict__.items()

        for key, value in settings:
            if hasattr(self.settings, key):
                attr = getattr(self, key)

                if isinstance(attr, QtWidgets.QAction):
                    setattr(self.settings, key, value.isChecked())
                else:
                    setattr(self.settings, key, value.value())

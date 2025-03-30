from pathlib import Path
from typing import NoReturn

from PyQt6 import QtCore
from PyQt6 import QtWidgets
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMenu

from decide.data import types
from decide.data.database import ActorIssue
from decide.data.types import ActorIssue
from decide.model.base import ActorIssue
from decide.qt import utils


class InputFilGrid:
    pass


class DynamicFormLayout(QtWidgets.QGridLayout):
    def __init__(self, main_window, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.main_window = main_window
        self.checkboxes = []
        self.objects = []
        self.row_pointer = 0

        self.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)

    def clear(self) -> None:
        """Set the parent of all child widgets to None so they will be deleted."""
        for i in reversed(range(self.count())):
            self.itemAt(i).widget().setParent(None)

    def add_row(self, *widgets) -> None:
        for index, widget in enumerate(widgets):
            self.addWidget(widget, self.row_pointer, index)

        self.row_pointer += 1

    def set_values(self, objects) -> None:
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
    """Form layout for customizing the Issue selection."""

    def set_issues(self, issues: list[types.PartialIssue]) -> None:
        self.set_values(issues)
        self.add_row(
            QtWidgets.QLabel("Issue"),
            QtWidgets.QLabel("Lower"),
            QtWidgets.QLabel("Upper"),
        )
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

    def state_changed(self) -> None:
        self.main_window.overview_widget.update_widget()

    def save(self) -> None:
        self.main_window.settings.selected_issues = self.get_selected()


class ActorWidget(DynamicFormLayout):
    """Form layout for customizing the Actor selection."""

    def set_actors(self, actors: list[types.PartialActor]) -> None:
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

    def state_changed(self) -> None:
        self.main_window.overview_widget.update_widget()

    def save(self) -> None:
        self.main_window.settings.selected_actors = self.get_selected()


class ActorIssueWidget(DynamicFormLayout):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def set_actor_issues(
        self, actor_issues: type[list[ActorIssue]] = list[types.ActorIssue]
    ) -> None:
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
        self,
        main_window,
        settings,
        data,
        actor_widget,
        issue_widget,
        *args,
        **kwargs,
    ) -> None:
        """:type settings: decide.qt.mainwindow.settings.ProgramSettings
        :type data: decide.qt.mainwindow.gui.ProgramData
        :type actor_widget: decide.qt.mainwindow.widgets.ActorWidget
        :type issue_widget: decide.qt.mainwindow.widgets.IssueWidget
        """
        super().__init__(main_window, *args, **kwargs)

        self.settings = settings
        self.data = data
        self.actor_widget = actor_widget
        self.issue_widget = issue_widget
        self.run_name = QtWidgets.QLineEdit()
        self.run_name.setText(self.settings.run_name)
        self.run_name.textChanged.connect(self.update_run_name)

    def update_run_name(self, value) -> None:
        self.settings.run_name = value

    def update_widget(self) -> None:
        self.clear()

        self.add_text_row("Input", str(self.settings.input_filename), self.test_callback)

        if self.settings.output_directory is None or self.settings.output_directory == "None":
            self.add_text_row(
                "Output directory",
                "set output directory",
                self.main_window.select_output_dir,
            )
        else:
            self.add_text_row(
                "Output directory",
                str(self.settings.output_directory),
                self.test_callback,
            )

        self.add_row(QtWidgets.QLabel("Run name"), self.run_name)

        self.add_text_row(
            "",
            "You can make use of the variable {rounds} and {repetitions} in run name",
        )

        settings = self.main_window.settings

        self.add_text_row("p-values", ", ".join(settings.model_variations()))

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

        self.main_window.set_start_button_state()

    def add_text_row(self, label: str, value: str, callback=None) -> None:
        if callback:
            value_x = "..." + value[-50:] if len(value) > 50 else value

            value_label = QtWidgets.QLabel(f'<a href="{value}">{value_x}</a>')
            value_label.linkActivated.connect(callback)
        else:
            value_label = QtWidgets.QLabel(value)

        self.add_row(QtWidgets.QLabel(label), value_label)

    def test_callback(self, link) -> None:
        utils.open_file_natively(link)


class MenuBar(QtWidgets.QMenuBar):
    def __init__(self, main_window, *args, **kwargs) -> None:
        """:type main_window: decide.qt.mainwindow.gui.DecideMainWindow"""
        super().__init__(*args, **kwargs)

        self.main_window = main_window
        self.settings = main_window.settings

        file_menu = self.addMenu("&File")

        self.output_sqlite = QAction("&sqlite", self)
        self.output_sqlite.setCheckable(True)
        self.output_sqlite.setChecked(True)

        self.issue_development_csv = QAction("Issue development (.csv)", self)
        self.issue_development_csv.setCheckable(True)
        self.issue_development_csv.setChecked(True)

        self.externalities_csv = QAction("Externalities (.csv)", self)
        self.externalities_csv.setCheckable(True)
        self.externalities_csv.setChecked(True)

        self.exchanges_csv = QAction("Exchanges (.csv)", self)
        self.exchanges_csv.setCheckable(True)
        self.exchanges_csv.setChecked(True)

        self.voting_positions = QAction("Show voting positions", self)
        self.voting_positions.setCheckable(True)
        self.voting_positions.setChecked(True)

        self.summary_only = QAction("Summary only (.csv)", self)
        self.summary_only.setCheckable(True)
        self.summary_only.setChecked(True)

        self.open_data_view = QAction("New data file", self)
        self.open_data_view.triggered.connect(self.main_window.open_data_view)

        open_action = QAction("&Open data file", self)
        open_action.triggered.connect(self.main_window.open_input_data)

        edit_action = QAction("&Edit data file", self)
        edit_action.triggered.connect(
            self.main_window.open_current_input_window_with_current_data,
        )

        save_settings = QAction("&Save settings", self)
        save_settings.triggered.connect(self.main_window.save_settings)

        output_dir_action = QAction("&Set output directory", self)
        output_dir_action.triggered.connect(self.main_window.select_output_dir)

        log_action = QAction("Show log window", self)
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

        error_report = QAction("Send error report", self)
        error_report.triggered.connect(self.main_window.show_error_report_dialog)
        file_menu.addAction(error_report)

        error_report_2 = QAction("Trigger error", self)
        error_report_2.triggered.connect(self.trigger_error)
        file_menu.addAction(error_report_2)

    def recently_opened_menu(self, menu: QMenu) -> None:
        sub_menu = QMenu("Recently opened", menu)
        menu.addMenu(sub_menu)

        for item in self.settings.recently_opened:
            action = QAction(item, self)
            action.triggered.connect(self.open_input_data)
            sub_menu.addAction(action)

    def open_input_data(self) -> None:
        sender = self.sender()

        self.main_window.init_ui_data(Path(sender.text()))

    def trigger_error(self) -> NoReturn:
        msg = "Error triggered"
        raise Exception(msg)

    def load(self) -> None:
        """Copy the values from the ProgramSettings object."""
        settings = self.settings.__dict__.items()

        for key, value in settings:
            if hasattr(self, key):
                attr = getattr(self, key)

                if isinstance(value, bool):  # type: QtWidgets.QAction
                    attr.setChecked(value)
                else:
                    attr.setValue(value)

    def save(self) -> None:
        """Set the attributes to the ProgramSettings object."""
        settings = self.__dict__.items()

        for key, value in settings:
            if hasattr(self.settings, key):
                attr = getattr(self, key)

                if isinstance(attr, QAction):
                    setattr(self.settings, key, value.isChecked())
                else:
                    setattr(self.settings, key, value.value())

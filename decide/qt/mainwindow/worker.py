import copy
import logging
import time

from PyQt5 import QtCore

from decide.cli import init_model, init_output_directory, float_range
from decide.model.utils import ModelLoop
from decide.qt.mainwindow.settings import ProgramSettings


class Worker(QtCore.QObject):
    finished = QtCore.pyqtSignal(str, int)
    update = QtCore.pyqtSignal(int, int, float)

    def __init__(self, settings: ProgramSettings):
        super(Worker, self).__init__()

        self.settings = settings
        self.break_loop = False

    @QtCore.pyqtSlot()
    def run_model(self):
        settings = self.settings

        print("start")
        print(settings.start)

        if settings.start == settings.stop:
            p_values = [settings.start]
        else:
            p_values = [
                str(round(p, 2))
                for p in float_range(
                    start=settings.start, step=settings.step, stop=settings.stop
                )
            ]

        print("P values")
        print(p_values)

        selected_actors = settings.selected_actors
        selected_issues = settings.selected_issues

        repetitions = settings.repetitions
        iterations = settings.iterations

        input_filename = settings.input_filename

        for p in p_values:
            model = init_model("equal", settings.input_filename, p=p)

            csv_parser = csvparser.CsvParser(model)
            csv_parser.read(
                input_filename,
                actor_whitelist=selected_actors,
                issue_whitelist=selected_issues,
            )

            output_directory = init_output_directory(
                model=model,
                output_dir=settings.output_directory,
                selected_actors=settings.selected_actors,
            )

            actor_issues = copy.deepcopy(model.actor_issues)

            from decide.qt.mainwindow.gui import init_event_handlers

            event_handler = init_event_handlers(model, output_directory, settings)
            event_handler.before_repetitions(
                repetitions=repetitions, iterations=iterations
            )

            start_time = time.time()

            for repetition in range(repetitions):

                model.actor_issues = copy.deepcopy(actor_issues)

                model_loop = ModelLoop(model, event_handler, repetition)

                event_handler.before_iterations(repetition)

                for iteration_number in range(iterations):

                    if self.break_loop:
                        break

                    logging.info("round {0}.{1}".format(repetition, iteration_number))
                    self.update.emit(repetition, iteration_number, start_time)

                    model_loop.loop()

                event_handler.after_iterations(repetition)

                if self.break_loop:
                    break

            event_handler.after_repetitions()

            self.finished.emit(output_directory, model.tie_count)

    def stop(self):
        self.break_loop = True

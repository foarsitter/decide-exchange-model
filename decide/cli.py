from __future__ import annotations

import shutil
from datetime import UTC
from datetime import datetime
from pathlib import Path
from typing import Annotated
from typing import Literal

import typer

from decide import input_folder
from decide.data.modelfactory import ModelFactory
from decide.data.reader import InputDataFile
from decide.log import logger
from decide.model import base
from decide.model import equalgain
from decide.model import randomrate
from decide.model.observers.exchanges_writer import ExchangesWriter
from decide.model.observers.externalities import Externalities
from decide.model.observers.issue_development import IssueDevelopment
from decide.model.observers.logger import Logger
from decide.model.observers.observer import Observable
from decide.model.observers.observer import Observer
from decide.model.observers.sqliteobserver import SQLiteObserver
from decide.model.utils import ModelLoop


class ProgressObserver(Observer):
    def __init__(self, observable: Observable, repetitions: int, iterations: int) -> None:
        super().__init__(observable)
        self.repetitions = repetitions
        self.iterations = iterations

    def after_loop(
        self,
        _realized: list[base.AbstractExchange],
        iteration: int,
        repetition: int,
    ) -> None:
        total = self.repetitions * self.iterations

        p = repetition * self.iterations + iteration + 1

        logger.info("Progress", progress=p, total=total)


def init_event_handlers(
    model,
    output_directory: Path,
    database_file: Path | None,
    *,
    write_csv=True,
) -> Observable:
    event_handler = Observable(model_ref=model, output_directory=output_directory)

    SQLiteObserver(event_handler, str(database_file or output_directory))

    Logger(event_handler)
    Logger.LOG_LEVEL = 99

    if write_csv:
        # csv handlers
        Externalities(event_handler, summary_only=True)
        ExchangesWriter(event_handler, summary_only=True)
        IssueDevelopment(event_handler, write_voting_position=True, summary_only=True)

    return event_handler


def init_output_directory(*args: str):
    output_directory = Path().joinpath(*args)

    if not output_directory.is_dir():
        if output_directory.is_fifo():
            output_directory += "_output"

        if not output_directory.is_dir():
            output_directory.mkdir(parents=True)

    return output_directory


def float_range(start: float = 0.0, stop: float = 1.0, step: float = 0.05):
    # when the step size is 0, return
    if step == 0:
        yield 0
    else:
        # prevent locking yourself out
        max_steps = 256
        if (stop - start) / step > max_steps:
            msg = f"Maximum steps exceeded with step={step} ({max_steps})"
            raise RuntimeError(msg)

        i = start
        # add a 10th step to stop for floating point rounding differences 0.500001 vs 0.499999
        while i < (stop + step / 10):
            yield i
            i += step


def actors_param(args: str) -> list[str]:
    actors = None
    if args:
        actors = args.split(";")

    return actors


def issues_param(args: str) -> list[str]:
    issues = None

    if args:
        issues = args.split(";")

    return issues


def p_values_param(p: str, start: str, step: str, stop: str) -> list[float]:
    p_values = []

    if start and step and stop:
        p_values = [
            str(round(p, 2))
            for p in float_range(
                start=float(start),
                step=float(step),
                stop=float(stop),
            )
        ]

    elif p:
        if ";" in p:
            p_values += p.split(";")
        else:
            p_values.append(p)

    return p_values


app = typer.Typer()


@app.command()
def main(  # noqa: PLR0913
    input_file: Annotated[
        Path,
        typer.Option(
            "--input-file",
            "--input_file",
            help="The location of the csv input file. ",
        ),
    ] = input_folder / "rechts.csv",
    model: Annotated[
        Literal["equal", "random"],
        typer.Option(
            "--model",
            "-m",
            help='The type of the model. The options are "equal" for the Equal Gain model and "random" for the RandomRate model ',  # noqa: E501
        ),
    ] = "equal",
    repetitions: Annotated[
        int,
        typer.Option("--repetitions", "-r", help="How many times it has te be repeated?"),
    ] = 1,
    iterations: Annotated[
        int,
        typer.Option(
            "--iterations",
            "-i",
            help="The number of round the model needs to be executed",
        ),
    ] = 10,
    p: Annotated[str | None, typer.Option("--p", "-p", help="Randomized Equal Gain")] = None,
    start: Annotated[str, typer.Option("--start")] = "0.0",
    step: Annotated[str, typer.Option("--step")] = "0.00",
    stop: Annotated[str, typer.Option("--stop")] = "0.00",
    issues: Annotated[str | None, typer.Option("--issues")] = None,
    actors: Annotated[str | None, typer.Option("--actors")] = None,
    output_dir: Annotated[
        Path,
        typer.Option("--output-dir", "--output_dir", help="Output directory "),
    ] = Path("../data/output/"),
    name: Annotated[str | None, typer.Option("--name")] = None,
    database: Annotated[
        str | None,
        typer.Option("--database", help="The SQLite database"),
    ] = None,
) -> None:
    p_values = p_values_param(p, start, step, stop)

    data_file = InputDataFile.open(input_file)

    data_set_name = Path(name or input_file).stem

    factory = ModelFactory(
        data_file,
        actor_whitelist=actors_param(actors),
        issue_whitelist=issues_param(issues),
    )

    # Initial the right model from the given arguments
    model_klass = equalgain.EqualGainModel if model == "equal" else randomrate.RandomRateModel

    model = factory(model_klass=model_klass, randomized_value=p_values[0])

    # The event handlers for logging and writing the results to the disk.

    output_directory = output_dir / data_set_name
    output_directory.mkdir(parents=True, exist_ok=True)
    # store the input file among the output files
    shutil.copy(input_file, output_directory / "input.csv")

    event_handler = init_event_handlers(
        model=model,
        output_directory=output_directory,
        database_file=database,
        write_csv=True,
    )

    event_handler.before_model()

    ProgressObserver(event_handler, repetitions=repetitions, iterations=iterations)

    # in therms of REX, 0.0 is EqualGain and 1.0 the maximum variation
    for randomized_value in p_values:
        start_time = datetime.now(UTC)

        run_output_dir = output_dir / data_set_name / str(randomized_value)
        run_output_dir.mkdir(parents=True, exist_ok=True)

        event_handler.update_output_directory(run_output_dir)

        event_handler.log(message=f"Start calculation at {start_time}")
        event_handler.log(message="Parsed file")

        event_handler.before_repetitions(
            repetitions=repetitions,
            iterations=iterations,
            randomized_value=randomized_value,
        )

        for repetition in range(repetitions):
            model = factory(model_klass=model_klass, randomized_value=randomized_value)

            event_handler.update_model_ref(model)

            model_loop = ModelLoop(model, event_handler, repetition)

            event_handler.before_iterations(repetition)

            for iteration_number in range(iterations):
                logger.info(
                    "Round completed",
                    repetition=repetition,
                    iteration_number=iteration_number,
                )
                model_loop.loop()

            event_handler.after_iterations(repetition)

        event_handler.after_repetitions()

        event_handler.log(message=f"Finished in {datetime.now(UTC) - start_time}")

    event_handler.after_model()
    logger.info("Done")


if __name__ == "__main__":
    app()

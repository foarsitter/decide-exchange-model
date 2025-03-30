from decide.data.utils import write_exchanges
from decide.model import base
from decide.model.observers import observer


class ExchangesWriter(observer.Observer):
    """There are three stages of externalities
    By exchange, by issue set and by actor.
    """

    def __init__(
        self,
        observable: observer.Observable,
        summary_only: bool = False,
        before: bool = False,
    ) -> None:
        super().__init__(observable)
        self.summary_only = summary_only
        self.before = before

    def _create_directory(self, repetition: int) -> None:
        (self.output_directory / "exchanges" / f"{repetition}" / "initial").mkdir(
            parents=True,
            exist_ok=True,
        )

    def before_iterations(self, repetition) -> None:
        self._create_directory(repetition)

    def before_loop(self, iteration: int, repetition: int | None = None) -> None:
        """Writes all the possible exchanges to the filesystem
        :param iteration:
        :param repetition:`.
        """
        if not self.before:
            return

        self.model_ref.sort_exchanges()

        write_exchanges(
            f"{self.output_directory}/exchanges/{repetition}/initial/before.{iteration}.{repetition}.csv",
            self.model_ref.exchanges,
        )

    def after_loop(
        self,
        realized: list[base.AbstractExchange],
        iteration: int,
        repetition: int,
    ) -> None:
        """Writes al the executed exchanges to the filesystem
        :param repetition:
        :param realized:
        :param iteration:
        """
        salt = self._get_salt

        filename = (
            self.output_directory
            / "exchanges"
            / f"{repetition}"
            / f"round.{iteration + 1}.{salt}.csv"
        )

        write_exchanges(
            filename=filename,
            realized=realized,
        )

    @property
    def _get_salt(self) -> str:
        model_name = "random"
        from decide.model.equalgain import EqualGainModel

        if isinstance(self.model_ref, EqualGainModel):
            model_name = "equal"
            if self.model_ref.randomized_value is not None:
                model_name += "-" + str(round(self.model_ref.randomized_value, 2))

        return model_name

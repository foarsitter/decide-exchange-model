from typer.testing import CliRunner

from decide.cli import app

runner = CliRunner()


def test_app():
    result = runner.invoke(app, ["--iterations", 10, "--repetitions", 2, "--p", "0.00", "--p", "1.00"])
    assert result.exit_code == 0, result.output

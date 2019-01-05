import os

from decide.model.helpers.helpers import example_data_file_path


def test_example_data_file_path():

    assert example_data_file_path("kopenhagen").endswith(
        os.path.join("..", "..", "..", "data", "input", "kopenhagen.csv")
    )

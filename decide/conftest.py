import os

import pytest

from decide import input_folder
from decide.data.modelfactory import ModelFactory
from decide.data.reader import InputDataFile
from decide.model.equalgain import EqualGainModel


@pytest.fixture
def model():
    date_file = InputDataFile.open(os.path.join(input_folder, 'sample_data.txt'))

    factory = ModelFactory(date_file=date_file)

    return factory(EqualGainModel)


@pytest.fixture
def sample_model():
    date_file = InputDataFile.open(os.path.join(input_folder, 'sample_data.txt'))

    factory = ModelFactory(date_file=date_file)

    return factory(EqualGainModel)

from decide.data.reader import InputDataFile
from decide.model.base import AbstractModel


def create_model(date_file: InputDataFile, model_klass=AbstractModel):
    model_klass()

    return model_klass

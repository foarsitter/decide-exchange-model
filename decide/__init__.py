import os

__version__ = "2020.1.2"

decide_base_path = os.path.dirname(os.path.abspath(__file__))

log_filename = os.path.join(decide_base_path, "decide.log")

data_folder = os.path.join(decide_base_path, "..", "data")
input_folder = os.path.join(data_folder, "input")

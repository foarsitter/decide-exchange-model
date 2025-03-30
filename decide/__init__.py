from pathlib import Path

decide_base_path = Path(__file__).parent

log_filename = decide_base_path / "decide.log"

data_folder = decide_base_path.parent / "data"
input_folder = data_folder / "input"

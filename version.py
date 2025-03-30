from datetime import datetime
from datetime import UTC
import re
import sys
from pathlib import Path

import toml


def update_version(file_path: Path, release: str) -> str:
    """Update template version in pyproject.toml."""
    old_content = file_path.read_text()
    updated_content = re.sub(
        r'\nversion = "\d+\.\d+\.\d+"\n',
        f'\nversion = "{release}"\n',
        old_content,
    )
    file_path.write_text(updated_content)

    return release


path = Path(__file__).parent / "pyproject.toml"


def current_version() -> str:
    """Get current version from pyproject.toml."""

    return toml.load(path)["project"]["version"]


def increase_patch(version: str) -> str:
    year_month, patch = version.rsplit(".", 1)
    patch = str(int(patch) + 1)
    return f"{year_month}.{patch}"


if __name__ == "__main__":
    x = sys.argv[1]

    version = current_version()

    if x == "patch":
        print(update_version(path, increase_patch(version)))  # noqa: T201
    elif x == "dev":
        # use the timestamp as dev number
        n = datetime.now(UTC).strftime("%H%M%S")
        print(update_version(path, increase_patch(version) + f"-dev{n}"))  # noqa: T201
    else:
        print(current_version())  # noqa: T201

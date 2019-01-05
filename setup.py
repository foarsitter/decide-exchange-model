from setuptools import setup

from decide import __version__

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="decide-exchange-model",
    version=__version__,
    packages=[
        "decide",
        "decide.model",
        "decide.model.test",
        "decide.model.helpers",
        "decide.model.helpers.test",
        "decide.model.observers",
    ],
    url="https://github.com/foarsitter/decide-exchange-model",
    license="GPL-3.0",
    author="jelmert",
    author_email="info@jelmert.nl",
    description="Model of collective decision making",
    long_description=long_description,
    long_description_content_type="text/markdown",
    entry_points={
        "console_scripts": ["decide-cli=decide.cli:main"],
        "gui_scripts": ["decide-gui=decide.qtgui:main"],
    },
    python_requires=">=3.6",
    install_requires=["peewee>=3", "matplotlib"],
)

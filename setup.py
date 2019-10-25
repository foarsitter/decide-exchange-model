from decide import __version__
from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="decide-exchange-model",
    version=__version__,
    packages=find_packages(),
    url="https://github.com/foarsitter/decide-exchange-model",
    license="GPL-3.0",
    author="jelmert",
    author_email="info@jelmert.nl",
    description="Model of collective decision making",
    long_description=long_description,
    long_description_content_type="text/markdown",
    entry_points={
        "console_scripts": ["decide-cli=decide.cli:main"],
        "gui_scripts": ["decide-gui=decide.gui:main"],
    },
    # data_files=[('data/input', ['data/input/kopenhagen.csv', 'data/input/CoP21.csv'])],
    python_requires=">=3.6",
    install_requires=[
        "blinker==1.4",
        "matplotlib==3.0.2",
        "requests==2.21.0",
        "typesystem==0.2.2"
    ],
)

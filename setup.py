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
    install_requires=[
        "blinker==1.4",
        # "coverage==4.5.2",
        "cython==0.29.17",
        "matplotlib==3.0.2",
        "numpy==-1.19.5",
        "pandas==1.1.5",
        "PyQt5==5.15.2",
        # "pytest==4.6.3",
        # "pytest-qt==3.2.2",
        "typesystem==0.2.2",
        # "brotlipy==0.7.0",
        # "certifi==2020.12.5",
        # "cffi==1.14.5",
        # "cryptography==3.4.7",
        "cython==0.29.17",
        # "jinja2==2.11.3",
        "peewee==3.14.4",
        # "pip==21.0.1",
        # "pyopenssl==20.0.1",
        # "pyparsing==2.4.7",
        # "pytest==4.6.3",
        # "pytz==2021.1",
        # "requests==2.25.1",
        # "setuptools==49.6.0",
        # "urllib3==1.26.4",
        # "wheel==0.36.2",
    ],
)

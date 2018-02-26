from setuptools import setup

setup(
    name='decide-exchange-model',
    version='1.0rc8',
    packages=['decide', 'decide.model', 'decide.model.test', 'decide.model.helpers', 'decide.model.helpers.test',
              'decide.model.observers'],
    url='https://github.com/foarsitter/decide-exchange-model',
    license='GPL-3.0',
    author='jelmert',
    author_email='info@jelmert.nl',
    description='Decide exchange model',
    entry_points={
        'console_scripts': [
            'decide-cli=decide.cli:main',
        ],
        'gui_scripts': [
            'decide-gui=decide.gui:main',
        ]
    },
    python_requires='>=3.5',
    install_requires=['peewee==3.0.17', 'matplotlib==2.1.2', 'numpy==1.14.0', 'pandas==0.22.0', 'jupyter==1.0.0']
)

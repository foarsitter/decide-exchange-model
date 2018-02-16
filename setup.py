from setuptools import setup

setup(
    name='decide-exchange-model',
    version='1.0rc5',
    packages=['model', 'model.test', 'model.helpers',
              'model.helpers.test', 'model.observers'],
    url='https://github.com/foarsitter/decide-exchange-model',
    license='GPL-3.0',
    author='jelmert',
    author_email='info@jelmert.nl',
    description='Decide exchange model',
    entry_points={
        'console_scripts': [
            'decide-model=model',
        ],
        'gui_scripts': [
            'decide-gui=gui:main',
        ]
    }
)

from setuptools import setup

setup(
    name='decide-exchange-model',
    version='v1.0RC4',
    packages=['model', 'model.test', 'model.helpers',
              'model.helpers.test', 'model.observers'],
    url='https://github.com/foarsitter/decide-exchange-model',
    license='GPL-3.0',
    author='jelmert',
    author_email='info@jelmert.nl',
    description='Decide exchange model'
)

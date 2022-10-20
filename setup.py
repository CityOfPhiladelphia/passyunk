from setuptools import setup

setup(
    name='passyunk',
    version='1.6.0',
    packages=['passyunk', 'passyunk/pdata'],
    package_data = {
        '': ['*.csv'],
    },
    url='',
    license='',
    author='tom.swanson',
    author_email='',
    description='address parser for City of Philadelphia addresses',
    install_requires=['fuzzywuzzy']
)

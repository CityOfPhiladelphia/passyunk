from setuptools import setup

setup(
    name='passyunk',
    version='1.19.0',
    packages=['passyunk', 'passyunk/pdata'],
    package_data = {
        '': ['*.csv'],
    },
    url='',
    license='',
    author='tom.swanson',
    author_email='',
    description='address parser for City of Philadelphia addresses',
    install_requires=[
        'fuzzywuzzy>=0.11.1,<1.0',
        'Levenshtein>=0.20,<1.0',
        'requests>=2.28,<3.0'
    ], 
    python_requires=">=3.6"
)

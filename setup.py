from setuptools import setup
from setuptools.command.develop import develop
from setuptools.command.install import install

class PostDevelopCommand(develop):
    """Post-installation for development mode."""
    def run(self):
        develop.run(self)
        print('PostDevelopCommand')
        # PUT YOUR POST-INSTALL SCRIPT HERE or CALL A FUNCTION

class PostInstallCommand(install):
    """Post-installation for installation mode."""
    def run(self):
        install.run(self)
        print('PostInstallCommand')
        # PUT YOUR POST-INSTALL SCRIPT HERE or CALL A FUNCTION

setup(
    name='passyunk',
    version='1.14.0',
    packages=['passyunk', 'passyunk/pdata'],
    package_data = {
        '': ['*.csv'],
    },
    url='',
    license='',
    author='tom.swanson',
    author_email='',
    description='address parser for City of Philadelphia addresses',
    install_requires=['fuzzywuzzy'], 
    cmdclass={
        'develop': PostDevelopCommand,
        'install': PostInstallCommand,
    },
)

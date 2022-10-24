from setuptools import setup
from setuptools.command.develop import develop
from setuptools.command.install import install
import os
import subprocess

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
        # print(f'{os.getcwd() = }')
        # s = subprocess.run([
        #     'git', 'clone', 'git@github.com:CityOfPhiladelphia/passyunk_automation.git', 
        #     '--depth', '1', '--filter=blob:none', '--sparse', 'testing'])
        # print(s)
        # PUT YOUR POST-INSTALL SCRIPT HERE or CALL A FUNCTION

setup(
    name='passyunk',
    version='1.15.0',
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
    scripts=['james_testing.py'], 
    cmdclass={
        'develop': PostDevelopCommand,
        'install': PostInstallCommand,
    },
)

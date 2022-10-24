#!python
import os
import subprocess

print(f'{os.getcwd() = }')
s = subprocess.run([
    'git', 'clone', 'git@github.com:CityOfPhiladelphia/passyunk_automation.git', 
    '--depth', '1', '--filter=blob:none', '--sparse', 'james_testing'])
print(s)
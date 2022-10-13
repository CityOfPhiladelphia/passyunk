import re
from version import Version

def update_version(): 
    '''
    Increment the minor version of setup.py - not intended to be run by Passyunk users
    '''
    # Read in the file
    with open('setup.py', 'r') as file :
        filedata = file.read()

    # Replace the target string
    version_text = re.findall(f'(?<=version=\').*?(?=\')', filedata)[0]
    old_version = Version(version_text)
    new_version = old_version.increment_minor()
    print(f'Updating from version {old_version.version} to {new_version}')
    filedata = filedata.replace(f"version='{old_version.version}'", f"version='{new_version}'") 
    
    # Write the file out again
    with open('setup.py', 'w') as file:
        file.write(filedata)
    
    return new_version

if __name__ == '__main__': 
    update_version()
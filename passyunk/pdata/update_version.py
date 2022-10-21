import re
import sys
import click
# CityGeo
from version import Version

@click.command()
@click.option('--file', help='File to update')
@click.option('--get_version', '-g', 'path', flag_value='get_version', help='Get current version version of file, returning text')
@click.option('--no_update', '-n', 'path', flag_value='no_update', help='Increment minor version of file without updating file, returning text')
@click.option('--update', '-u', 'path', flag_value='update', help='Increment and update the minor version of file')
@click.option('--version', '-v', help='Version to use updating, must be valid SemVer syntax')
def main(file, path, version): 
    '''
    \b
    This module is not intended to be run by Passyunk users; it is used by CityGeo
    to update the module. Enclose filename in single-quotes if it contains whitespace. 
    This module must be called with one of the flags "--get_version", "--no_update", "--update". 
    '''
    if path == None: 
        raise ValueError('One of the flags "--get_version", "--no_update", "--update" must be provided')
    with open(file, 'r') as f:
        filedata = f.read()
    
    version_text = re.findall(f'(?<=version=\').*?(?=\')', filedata)[0]
    old_version = Version(version_text)
    if path == 'get_version': 
        print(old_version.version)
        sys.exit(0)
    
    if path == 'no_update': 
        new_version = old_version.increment_minor()
        print(new_version.version)
        sys.exit(0)
    
    if path == 'update': 
        new_version = Version(version)
        filedata = filedata.replace(
            f"version='{old_version.version}'", f"version='{new_version.version}'") 
        
        with open(file, 'w') as file:
            file.write(filedata)
        sys.exit(0)

if __name__ == '__main__': 
    main()
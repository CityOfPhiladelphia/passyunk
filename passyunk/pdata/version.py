import re
from typing import Union, List
Array = List[str]

class Version: 
    '''
    A class to hold attributes and methods for a software version that follows 
    Symantic Versioning (SemVer) syntax. See https://semver.org/ for syntax details. 
    Class variable SEMVER holds the RegEx used to capture and validate a version. 

    Includes support for the following comparison operators: <, >, <=, >=, ==, !=
    '''    
    SEMVER = '^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$'
    
    def __init__(self, version=None): 
        if version == None: 
            self.version = None
            self.major = None
            self.minor = None
            self.patch = None
            self.prerelease = None
            self.buildmetadata= None
        else:             
            m = self.check(version, return_match=True)
            self.version = version
            self.major = int(m['major'])
            self.minor = int(m['minor'])
            self.patch = int(m['patch'])
            self.prerelease = m['prerelease']
            self.buildmetadata= m['buildmetadata']
    
    def check(self, version: str, return_match: bool) -> re.match: 
        '''
        Raise a ValueError if a version does not use valid SemVer syntax, otherwise 
        return a re.match object that splits the fields.
        '''
        m = re.match(self.SEMVER, version)
        if m == None: 
            raise ValueError(f'Version "{version}" does not match Semantic Version schema - see https://semver.org/')
        if return_match: 
            return m
    
    def create(self, 
        major: Union[int, str], minor: Union[int, str], patch: Union[int, str], 
        prerelease: str, buildmetadata: str) -> 'Version': 
        '''
        Create a Version from components
        '''
        if prerelease == None: 
            prerelease = ''
        else: 
            prerelease = '-' + prerelease
        if buildmetadata == None: 
            buildmetadata = ''
        else: 
            buildmetadata = '+' + buildmetadata
        temp = (str(major) + '.' + str(minor) + '.' + str(patch) + prerelease + 
            buildmetadata)
        self.check(temp, return_match=False)
        return Version(temp)

    def increment_minor(self) -> str: 
        '''
        Increment the minor version by one and return a new Version, resetting 
        patch, prerelease, and buildmetadata. 
        '''
        return self.create(self.major, self.minor + 1, 0, None, None)
    
    def compare(self, other_version: 'Version') -> str: 
        '''
        Compare the major, minor, and patch between two Versions and return "lesser", 
        "greater", or "equal". Does not compare prerelease or buildmetadata.
        '''
        assert type(other_version) == Version, f'Other version must be an object of the Version class, not {type(other_version)}'
        
        if self.major < other_version.major: 
            return 'lesser'
        if self.major > other_version.major: 
            return 'greater'
        if self.minor < other_version.minor: 
            return 'lesser'
        if self.minor > other_version.minor: 
            return 'greater'
        if self.patch < other_version.patch: 
            return 'lesser'
        if self.patch > other_version.patch: 
            return 'greater'
        else: 
            return 'equal'
        
    def __lt__(self, other_version: 'Version'): 
        return self.compare(other_version) == 'lesser'

    def __gt__(self, other_version: 'Version'): 
        return self.compare(other_version) == 'greater'

    def __le__(self, other_version: 'Version'): 
        rv = self.compare(other_version)
        return (rv == 'lesser' or rv == 'equal')

    def __ge__(self, other_version: 'Version'): 
        rv = self.compare(other_version)
        return (rv == 'greater' or rv == 'equal')

    def __eq__(self, other_version: 'Version'): 
        return self.compare(other_version) == 'equal'

    def __ne__(self, other_version: 'Version'): 
        return self.compare(other_version) != 'equal'

    def __repr__(self): 
        return self.version

def find_newest(array: Array) -> 'Version': 
    '''
    Return the newest Version out of an array of elements coercible to Versions, 
    ignoring prerelease and buildmetadata
    '''
    current_max = Version('0.0.0')
    for v in array: 
        v = Version(v)
        if v > current_max: 
            current_max = v
    return current_max
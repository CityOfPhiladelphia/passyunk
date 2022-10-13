import importlib_metadata
import re
import warnings
import subprocess
subprocess.call(["git", "pull"])

SEMVER = '^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$'

class Version: 
    def __init__(self, version: str): 
        m = re.match(SEMVER, version)
        if m == None: 
            raise ValueError(f'Version "{version}" does not match Semantic Version schema - see https://semver.org/')
        self.major = m['major']
        self.minor = m['minor']
        self.patch = m['patch']
        self.prerelease = m['prerelease']
        self.buildmetadata= m['buildmetadata']

text_version = importlib_metadata.metadata('passyunk').json['version']
local_version = Version(text_version)
    
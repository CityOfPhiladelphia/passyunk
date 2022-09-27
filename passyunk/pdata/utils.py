import json
import functools

def get_creds(config_path, path=[]): 
    with open(config_path, 'r') as f:
        file = f.read()
        as_json = json.loads(file)
        creds = functools.reduce(dict.get, path, as_json) # path is the [][]...[] of  dict
    if creds == None: 
        raise(TypeError(f'Invalid db credentials, check config_path "{config_path}"'))
    return creds   
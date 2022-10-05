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

def standardize_nulls(val):
    if type(val) == str:
        return None if val.strip() == '' else val
    else:
        return None if val == 0 else val


class CursorProxy(object):
    def __init__(self, cursor):
        self._cursor = cursor

    def executemany(self, statement, parameters, **kwargs):
        # convert parameters to a list
        parameters = list(parameters)
        # pass through to proxied cursor
        return self._cursor.executemany(statement, parameters, **kwargs)

    def __getattr__(self, item):
        return getattr(self._cursor, item)


def get_cursor(connection):
    return CursorProxy(connection.cursor())
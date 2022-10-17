import requests
import json

class Usps_File(): 
    def __init__(self, content, filename, fulfilled): 
        self.content = content
        self.filename = filename
        self.fulfilled = fulfilled


class Usps_Epf(): 
    '''
    A class for interfacing with the USPS EPF API. See the README of this module for 
    a detailed understanding of how it works. 
    '''
    # The URLs are occasionally subject to change, so update them if needed. 
    # It is unclear why USPS EPF has multiple working URLs, hence the list structure.
    urls = {
        'version': {
            'method': 'GET', 
            'return_type': 'json', 
            'urls': ['https://epfup.usps.gov/up/epfupld//epf/version', 'https://epfws.usps.gov/ws/resources//epf/version']}, 
        'login': {
            'method': 'POST', 
            'return_type': 'json', 
            'urls': ['https://epfup.usps.gov/up/epfupld//epf/login', 'https://epfws.usps.gov/ws/resources//epf/login']}, 
        'logout': {
            'method': 'POST', 
            'return_type': 'json', 
            'urls': ['https://epfup.usps.gov/up/epfupld//epf/logout', 'https://epfws.usps.gov/ws/resources//epf/logout']}, 
        'status': {
            'method': 'POST', 
            'return_type': 'json', 
            'urls': ['https://epfup.usps.gov/up/epfupld//download/status', 'https://epfws.usps.gov/ws/resources//download/status']}, 
        'acslist': {
            'method': 'POST', 
            'return_type': 'json', 
            'urls': ['https://epfup.usps.gov/up/epfupld//download/acslist', 'https://epfws.usps.gov/ws/resources//download/acslist']}, 
        'dnldlist': {
            'method': 'POST', 
            'return_type': 'json', 
            'urls': ['https://epfup.usps.gov/up/epfupld//download/dnldlist', 'https://epfws.usps.gov/ws/resources//download/dnldlist']}, 
        'list': {
            'method': 'POST', 
            'return_type': 'json', 
            'urls': ['https://epfup.usps.gov/up/epfupld//download/list', 'https://epfws.usps.gov/ws/resources//download/list']}, 
        'listplus': {
            'method': 'POST', 
            'return_type': 'json', 
            'urls': ['https://epfup.usps.gov/up/epfupld//download/listplus', 'https://epfws.usps.gov/ws/resources//download/listplus']}, 
        'epf': {
            'method': 'POST', 
            'return_type': 'file', # This is the only method diverted by _read_json()
            'urls': ['https://epfup.usps.gov/up/epfupld//download/epf', 'https://epfws.usps.gov/ws/resources//download/epf']}
        }
    valid_statuses = ('N', 'S', 'X', 'C')
    max_depth = 1

    def __init__(self, username, password): 
        '''
        Entry point for class, requires a valid username and password to be passed
        '''
        self._username = username
        self._password = password
        self.logonkey = None
        self.tokenkey = None
        self.login()

    def __enter__(self): 
        return self
    
    def __exit__(self, type, value, traceback): 
        self.logout()
        return type == None

    def _get(self, url): 
        '''
        For endpoints that use the HTTP GET method
        '''
        return requests.get(url)
    
    def _post(self, url, data): 
        '''
        For endpoints that use the HTTP post method
        '''
        return requests.post(url, data)
    
    def _read_json(self, key: str, url: str, json_str: str, depth: int, r: requests.models.Response): 
        if Usps_Epf.urls[key]['return_type'] == 'json': 
            r_json = r.json()
            if r_json['response'] == 'success': 
                return r_json
            elif r_json['response'] == 'failed': # Refresh security token, try again up to max_depth retries
                print(f'    Request parameters: {json_str}')
                print(f'    Response: {r.json()}\n')
                depth += 1
                if depth > Usps_Epf.max_depth: 
                    return None
                print(f'    Attempting retry {depth}')
                self.login()
                json_str = self._reprep_json(json_str)
                return self._try_method(key, url, json_str, depth)
        else: 
            return r
        
    def _try_method(self, key, url, json_str, depth): 
        method = Usps_Epf.urls[key]['method']
        try: 
            match method: 
                case 'GET': 
                    r = self._get(url)
                case 'POST': 
                    data = {'obj': json_str}
                    r = self._post(url, data)
                case _: 
                    raise NotImplementedError(f'URL method {method} not implemented')
            if not r.ok: # Bad HTTP status
                print(f'    URL: {url}\n\tStatus Code: {r.status_code}\n\tReason: {r.reason}')
                print(f'    Request parameters: {json_str}')
            return self._read_json(key, url, json_str, depth, r)
        except Exception as e: # Error in requests module
            print(f'\tRequests Error:\n{e}\n')
    
    def _try(self, key, json_str=None, depth=0): 
        '''
        Try each of the urls for the given key in order, and only fail if all of them fail
        '''
        for idx, url in enumerate(Usps_Epf.urls[key]['urls']): 
            print(f'    Trying url_{idx} = {url}')
            rv = self._try_method(key, url, json_str, depth)
            if rv != None: 
                return rv
        print('You may have provided incorrect information\n')
        raise Exception(f'\nAll attempts to use "{key}" failed.') # If all urls for a key fail, then raise Exception

    def _refresh_security(self, response, header:bool=False): 
        '''
        Every call to the API must subsequently refresh the security LogonKey and 
        TokenKey, otherwise future calls will fail. For every endpoint except EPF, the new LogonKey and TokenKey will come in the JSON response, while for EPF (which downloads the file) these will come in the header.
        '''
        if header: 
            self.logonkey = response['User-Logonkey']
            self.tokenkey = response['User-Tokenkey']
        else: 
            self.logonkey = response['logonkey']
            self.tokenkey = response['tokenkey']
        print('    Successsfully refreshed Logon Key and Token Key')
    
    def _reprep_json(self, json_str): 
        d = json.loads(json_str)
        return self._prep_data(**d)

    def _prep_data(self, **kwargs): 
        '''
        Prepare the data that must be sent alongside a POST request. This must 
        always include the LogonKey and TokenKey, and may require other arguments 
        (**kwargs) depending upon the endpoint
        '''
        d = {'logonkey': self.logonkey, 'tokenkey': self.tokenkey}
        for key, value in kwargs.items(): 
            if d.get(key) == None: # Don't overwrite the auto-update to the logonkey and tokenkey
                d[key] = value
        return json.dumps(d)

    def version(self): 
        '''
        Get the USPS EPF API software version - used to test functionality
        '''
        print(self._try('version'))
        
    def login(self): 
        '''
        Login to the using the Class username and password. Logging in must be the first 
        step of the module, and logging out should be the last step.
        '''
        print('... Logging in ...')
        json_str = json.dumps({'login': self._username, 'pword':self._password})
        r_json = self._try('login', json_str)
        self._refresh_security(r_json)

    def logout(self): 
        '''
        Logging out should be the last step of the module, and will deactivate the 
        currently associated LogonKey and TokenKey
        '''
        json_str = self._prep_data()
        self._try('logout', json_str)
        print('Successfully logged out and deactivated keys\n')
    
    def get_list(self): 
        '''
        Return a list of files available to download
        '''
        print('... Retrieving list of downloads ...')
        json_str = self._prep_data()
        r_json = self._try('dnldlist', json_str)
        self._refresh_security(r_json)
        return r_json['dnldfileList']
        
    def set_status(self, fileid: int|str, newstatus: str): 
        '''
        Set the status of a file on the USPS EPS API. NewStatus should be one of: 
            - "N" = new file available
            - "S" = download started
            - "X" = download canceled
            - "C" = download completed successfully            
        '''
        print('... Setting status ...')
        if type(fileid) not in (str, int): 
            raise TypeError(f'FileID must be of type "str" or "int" convertible to "str" not "{type(fileid)}"')
        else: 
            fileid = str(fileid)
        if type(newstatus) != str: 
            raise TypeError(f'New Status must be of type "str" not "{type(newstatus)}"')
        else: 
            newstatus = newstatus.upper()
            if newstatus not in Usps_Epf.valid_statuses: 
                raise ValueError(f'New Status "{newstatus}" not one of {Usps_Epf.valid_statuses}')
        json_str = self._prep_data(**{'newstatus':newstatus, 'fileid':fileid})
        r_json = self._try('status', json_str)
        print(f'    Successfuly set fileid "{fileid}" status to "{newstatus}"')
        self._refresh_security(r_json)

    def get_file(self, fileid: int|str) -> Usps_File: 
        '''
        Get a file associated with a particular FileID and return it as bytes. 
        If successful, update the file's status to "C", otherwise leave its status 
        as "S". 
        '''
        print(f'... Attempting to get File ID "{fileid}" ...')
        self.set_status(fileid, "S")

        json_str = self._prep_data(**{'fileid': fileid})
        r = self._try('epf', json_str)
        
        self._refresh_security(r.headers, header=True)
        self.set_status(fileid, "C")
        return r.content

    def get_newest(self) -> bytes:
        '''
        Iterate through the list of available files and get the first file that has 
        a status of "N" (new, not yet downloaded) and exit. '''
        print('... Getting newest file ...')
        get_list = self.get_list()
        for file in get_list: 
            if file['status'] == 'N': 
                fileid = file['fileid']
                content = self.get_file(fileid)
                return Usps_File(content, file['filename'], file['fulfilled'])
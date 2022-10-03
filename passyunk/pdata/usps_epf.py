import requests
import json
import click

class Usps_Epf(): 

    # The URLs are occasionally subject to change, so update them if needed. 
    # It is unclear why USPS EPF has multiple working URLs, hence the list structure.
    urls = {
        'version': {
            'method': 'GET', 
            'urls': ['https://epfup.usps.gov/up/epfupld//epf/version', 'https://epfws.usps.gov/ws/resources//epf/version']}, 
        'login': {
            'method': 'POST', 
            'urls': ['https://epfup.usps.gov/up/epfupld//epf/login', 'https://epfws.usps.gov/ws/resources//epf/login']}, 
        'logout': {
            'method': 'POST', 
            'urls': ['https://epfup.usps.gov/up/epfupld//epf/logout', 'https://epfws.usps.gov/ws/resources//epf/logout']}, 
        'status': {
            'method': 'POST', 
            'urls': ['https://epfup.usps.gov/up/epfupld//download/status', 'https://epfws.usps.gov/ws/resources//download/status']}, 
        'acslist': {
            'method': 'POST', 
            'urls': ['https://epfup.usps.gov/up/epfupld//download/acslist', 'https://epfws.usps.gov/ws/resources//download/acslist']}, 
        'dnldlist': {
            'method': 'POST', 
            'urls': ['https://epfup.usps.gov/up/epfupld//download/dnldlist', 'https://epfws.usps.gov/ws/resources//download/dnldlist']}, 
        'list': {
            'method': 'POST', 
            'urls': ['https://epfup.usps.gov/up/epfupld//download/list', 'https://epfws.usps.gov/ws/resources//download/list']}, 
        'listplus': {
            'method': 'POST', 
            'urls': ['https://epfup.usps.gov/up/epfupld//download/listplus', 'https://epfws.usps.gov/ws/resources//download/listplus']}, 
        'epf': {
            'method': 'POST', 
            'urls': ['https://epfup.usps.gov/up/epfupld//download/epf', 'https://epfws.usps.gov/ws/resources//download/epf']}
        }
    valid_statuses = ('N', 'S', 'X', 'C')
    max_depth = 1
    def __init__(self, username, password): 
        self._username = username
        self._password = password
        self.logonkey = None
        self.tokenkey = None
        self.login()

    def _get(self, url): 
        return requests.get(url)
    
    def _post(self, url, data): 
        return requests.post(url, data)
    
    def _try(self, key, json_str=None, depth=0): 
        '''
        Try each of the urls for the given key in order, and only fail if all of them fail
        '''
        method = Usps_Epf.urls[key]['method']
        for url in Usps_Epf.urls[key]['urls']: 
            try: 
                match method: 
                    case 'GET': 
                        r = self._get(url)
                    case 'POST': 
                        data = {'obj': json_str}
                        r = self._post(url, data)
                    case _: 
                        raise NotImplementedError(f'URL method {method} not implemented')
            except Exception as e: # Error in requests module
                print(f'Requests Error:\n{e}\n')
                continue
            if not r.ok: # Bad HTTP status, but try again with the remaining urls for that key
                print(f'URL: {url}\nStatus Code: {r.status_code}\nReason: {r.reason}')
                print(f'Request parameters: {json_str}')
            try: 
                r_j = r.json()
                if r_j['response'] == 'success': 
                    return r
                elif r_j['messages'] == 'Security token failed.': # Need to refresh security token, try again up to max_depth retries
                    depth += 1
                    print(f'Attempting retry {depth}')
                    if depth > Usps_Epf.max_depth: 
                        break
                    self.login()
                    json_str = self._reprep_json(json_str)
                    return self._try(key, json_str, depth)
                else: # Ok HTTP status, but the API said there was a failure
                    print(f'URL: {url}\nStatus Code: {r.status_code}\nReason: {r.reason}')
                    print(f'Response: {r.json()}\n')
                    continue
            except (KeyError, json.JSONDecodeError) as e: # Response is not part of the json for the key "epf", because the file is being downloaded
                continue
        print('You may have provided incorrect information such as the ID\n')
        raise Exception(f'All attempts to use "{method}" for "{key}" failed.') # If all urls for a key fail, then raise Exception

    def _refresh_security(self, response): 
        '''
        Every call to the API must subsequently refresh the security logonkey and tokenkey
        '''
        r_json = response.json()
        self.logonkey = r_json['logonkey']
        self.tokenkey = r_json['tokenkey']
    
    def _reprep_json(self, json_str): 
        d = json.loads(json_str)
        return self._prep_data(**d)

    def _prep_data(self, **kwargs): 
        d = {'logonkey': self.logonkey, 'tokenkey': self.tokenkey}
        for key, value in kwargs.items(): 
            if d.get(key) == None: # Don't overwrite the auto-update to the logonkey and tokenkey
                d[key] = value
        return json.dumps(d)

    def version(self): 
        print(self._try('version').json())
        
    def login(self): 
        json_str = json.dumps({'login': self._username, 'pword':self._password})
        r = self._try('login', json_str)
        self._refresh_security(r)
        print('Successfully received logonkey and tokenkey')

    def logout(self): 
        json_str = self._prep_data()
        self._try('logout', json_str)
        print('Successfully logged out and deactivated keys')
    
    def get_list(self): 
        json_str = self._prep_data()
        r = self._try('dnldlist', json_str)
        self._refresh_security(r)
        return r.json()['dnldfileList']
        
    def set_status(self, newstatus: str, fileid: int|str): 
        if type(newstatus) != str: 
            raise TypeError(f'New Status must be of type "str" not "{type(newstatus)}"')
        else: 
            newstatus = newstatus.upper()
            if newstatus not in Usps_Epf.valid_statuses: 
                raise ValueError(f'New Status "{newstatus}" not one of {Usps_Epf.valid_statuses}')
        if type(fileid) not in (str, int): 
            raise TypeError(f'FileID must be of type "str" or "int" convertible to "str" not "{type(fileid)}"')
        else: 
            fileid = str(fileid)
        json_str = self._prep_data(**{'newstatus':newstatus, 'fileid':fileid})
        r = self._try('status', json_str)
        self._refresh_security(r)
        print(f'Successfuly set fileid "{fileid}" status to "{newstatus}"')

    def get_file(self, fileid): 
        json_str = self._prep_data(**{'fileid': fileid})
        print(f'... attempting to get File ID "{fileid}" ...')
        r = self._try('epf', json_str)
        print(r)


    def get_new(self): 
        get_list = self.get_list()
        for fileid in get_list: 
            self.set_status("S", fileid)
            self.get_file(self)
            self.set_status("C", fileid)

        pass

@click.command()
@click.option('--url', '-u')
@click.option('--password', '-p')
def main(url, password): 
    epf = Usps_Epf(url, password)
    epf.get_file('7170903')

if __name__ == '__main__': 
    main()

    
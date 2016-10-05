# passyunk

Address parser and standardizer for the City of Philadelphia

## Installation

    pip install git+https://github.com/CityOfPhiladelphia/passyunk

Optionally, copy USPS, centerlines, and elections files to `/path/to/passyunk/passyunk/pdata`. You can find out where Passyunk was installed with:

    python
    import passyunk
    passyunk.__file__

## Usage

### Quickstart

    from passyunk.parser import PassyunkParser
    p = PassyunkParser()
    components = p.parse('1234 MARKET ST')
    standardized_address = components['street_address']

### Parser.parse(address)

Takes an address, standardizes it, and returns a dictionary of address components.

    {'components': {'address': {'addr_suffix': None,
                                'addrnum_type': 'N',
                                'fractional': None,
                                'full': '1234',
                                'high': None,
                                'high_num': None,
                                'high_num_full': None,
                                'isaddr': True,
                                'low': '1234',
                                'low_num': 1234,
                                'parity': 'E'},
                    'base_address': '1234 MARKET ST',
                    'bldgfirm': None,
                    'cl_addr_match': 'A',
                    'election': {'blockid': None, 'precinct': None},
                    'matchdesc': None,
                    'responsibility': 'STATE',
                    'seg_id': '440394',
                    'st_code': '53560',
                    'street': {'full': 'MARKET ST',
                               'is_centerline_match': True,
                               'name': 'MARKET',
                               'parse_method': 'CL1',
                               'postdir': None,
                               'predir': None,
                               'score': None,
                               'suffix': 'ST'},
                    'street_2': {'full': None,
                                 'is_centerline_match': False,
                                 'name': None,
                                 'parse_method': None,
                                 'postdir': None,
                                 'predir': None,
                                 'score': None,
                                 'suffix': None},
                    'street_address': '1234 MARKET ST',
                    'unit': {'unit_num': None, 'unit_type': None},
                    'uspstype': None,
                    'zip4': None,
                    'zipcode': None},
     'input_address': '1234 MARKET ST',
     'type': 'address'}

# passyunk

Address parser and standardizer for the City of Philadelphia

## Installation
```
pip install git+https://github.com/CityOfPhiladelphia/passyunk
```
To find where passyunk is installed, from the command line run
```
python
import passyunk
passyunk.__file__
```
### 
If you have been granted access to the private data files, run 
```
pip install git+ssh://git@github.com/CityOfPhiladelphia/passyunk_automation.git -v --force-reinstall
```
which will move the private data files into the `passyunk/pdata` folder. Note this command must be run from the same environment that passyunk itself was installed in such as a virtual environment.

## Usage

### Quickstart

    from passyunk.parser import PassyunkParser
    p = PassyunkParser()
    parsed = p.parse('1234 MARKET ST')
    standardized_address = parsed['components']['output_address']

### Parser.parse(address)

Takes an address, standardizes it, and returns a dictionary of address components.

    {
      "components": {
        "address": {
          "addr_suffix": null,
          "addrnum_type": "N",
          "fractional": null,
          "full": "1234",
          "high": null,
          "high_num": null,
          "high_num_full": null,
          "isaddr": true,
          "low": "1234",
          "low_num": 1234,
          "parity": "E"
        },
        "address_unit": {
          "unit_num": null,
          "unit_type": null
        },
        "base_address": "1234 MARKET ST",
        "cl_addr_match": "A",
        "cl_responsibility": "STATE",
        "cl_seg_id": "440394",
        "election": {
          "blockid": "24021362",
          "precinct": "0528"
        },
        "mailing": {
          "bldgfirm": "MARKET STREET BLDG",
          "matchdesc": "Multiple Zip4 Matches",
          "uspstype": "H",
          "zip4": "3721",
          "zipcode": "19107"
        },
        "output_address": "1234 MARKET ST",
        "street": {
          "full": "MARKET ST",
          "is_centerline_match": true,
          "name": "MARKET",
          "parse_method": "CL1",
          "postdir": null,
          "predir": null,
          "score": null,
          "street_code": "53560",
          "suffix": "ST"
        },
        "street_2": {
          "full": null,
          "is_centerline_match": false,
          "name": null,
          "parse_method": null,
          "postdir": null,
          "predir": null,
          "score": null,
          "street_code": null,
          "suffix": null
        }
      },
      "input_address": "1234 market street",
      "type": "address"
    }

## Automated Data Updates
### Automating-Centerline
### Automating-Zip
#### USPS_EPF
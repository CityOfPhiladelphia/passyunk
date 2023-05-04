# passyunk

Address parser and standardizer for the City of Philadelphia

## Installation
```
pip install git+https://github.com/CityOfPhiladelphia/passyunk
```
If you have been granted access to the private data files, you can install the `passyunk_automation` package at the same time by running 
```
pip install git+https://github.com/CityOfPhiladelphia/passyunk[private]
```

To find where passyunk is installed, from the command line run
```
python
import passyunk
passyunk.__file__
```
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

## Data Updates
The data in the folder folder `passyunk/pdata` is public; the files `centerline.csv` and `centerline_streets.csv` are refreshed on a continual basis, and each data update will create a new version tag for this repository in the format '1.x.0'. 

The private data is housed in the separate `passyunk_automation` package, where files are updated on a monthly basis. Each private data update will result in a new private version tag for this repository in the format '1.y.0+private'. 

Thus the version 1.4.0 refers solely to the 4th public data update while the version 1.4.0+private refers solely to the 4th private data update. No public data will be updated in a new private data version nor vice-versa, so 1.4.0 and 1.4.0+private have no connection to each other, breaking a rule of SemVer syntax. However, 1.4.0 does contain updated public data compared to 1.3.0, and 1.4.0+private does contain updated private data compared to 1.3.0+private.

When `passyunk` is first imported into a python script, it will warn the user if the module's public data version is less than the latest public data version tag on GitHub. Similarly, if it detects that `passyunk_automation` has been installed, it will perform the same check for the private data version. The module will still work fine even if the data is out-of-date.
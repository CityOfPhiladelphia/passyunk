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
      "input_address": "1234 market st",
      "type": "address"
    }

from passyunk.parser import PassyunkParser
import pytest

@pytest.fixture
def p():
    return PassyunkParser()

# check that passyunk_automation zip4 data is installed before running these tests
@pytest.fixture
def private_installed():
    # Private Data
    try: 
        from passyunk_automation.zip4 import create_zip4_lookup, get_zip_info # usps_zip4s.csv - Private
        from passyunk_automation.election import create_election_lookup, get_election_info # election_block.csv - Private
        return True
    except ModuleNotFoundError as e: 
        return False

def test_zip4_1(p, private_installed):
    test_addr = "1 COMCAST CTR FL 32"
    ac = p.parse(test_addr)['components']
    assert private_installed 
    assert ac['mailing']['zip4'] == '2855' #incorrect base: 2833

def test_zip4_2(p, private_installed):
    test_addr = "1 S BROAD ST FL 11"
    ac = p.parse(test_addr)['components']
    print(ac['mailing']['zip4'])
    assert private_installed
    assert ac['mailing']['zip4'] is None #incorrect base: 3426

def test_zip4_unittype(p, private_installed):
    """Ensure that get_zip_info() returns the proper unit type when floor is NOT involved"""
    test_addr = "1130 SPRUCE ST # 1C"
    ac = p.parse(test_addr)['components']
    assert private_installed
    assert ac['mailing']['zip4'] == '6004'
    assert ac['address_unit']['unit_num'] == '1C'
    assert ac['address_unit']['unit_type'] == 'APT'
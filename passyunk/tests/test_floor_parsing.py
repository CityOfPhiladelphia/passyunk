from passyunk.parser import PassyunkParser
import pytest

@pytest.fixture
def p():
    return PassyunkParser()


@pytest.fixture
def mkt():
    return "1234 MARKET ST "


def test_nonsense(p, mkt):
    test_addr = mkt + "Zebra Octopus Llama Fish Elephant Bird"
    ans = p.parse(test_addr)
    ac = ans['components']
    assert ac['floor']['floor_num'] is None
    assert ac['floor']['floor_type'] is None
    assert ac['address_unit']['unit_num'] is None
    assert ac['address_unit']['unit_type'] is None


def test_just_floor15(p, mkt):
    examples = [
    "Fl 15",
    "Fl.15",
    "Fl#15",
    "Fl.#15",
    "Flr 15",
    "Floor 15",
    "15th Floor",
    # "Floor Fifteen", # doesn't work with number words yet
    ]
    for test_addr in examples:
        ans = p.parse(mkt + test_addr)
        ac = ans['components']
        assert ac['floor']['floor_num'] == '15'
        assert ac['floor']['floor_type'] == 'FL'
        assert ac['address_unit']['unit_num'] == '15'
        assert ac['address_unit']['unit_type'] == 'FL'


def test_floor15_unit6(p, mkt):
    examples = [
        "Floor 15 Unit 6",
        "Unit 6 Floor 15",
        "Floor #15 Unit 6",
        "Unit 6 Floor #15",
        "Floor 15 Unit #6",
        "Unit #6 Floor 15",
        # "Floor #15 Unit #6",
        # "Unit 6 Floor #15",
    ]
    for test_addr in examples:
        ans = p.parse(mkt + test_addr)
        ac = ans['components']
        assert ac['floor']['floor_num'] == '15'
        assert ac['floor']['floor_type'] == 'FL'
        assert ac['address_unit']['unit_num'] == '6'
        assert ac['address_unit']['unit_type'] == 'UNIT'       


def test_floor15_apt6(p, mkt):
    examples = [
        "Floor 15 Apt 6",
        "Apt 6 Floor 15",
    ]
    for test_addr in examples:
        ans = p.parse(mkt + test_addr)
        ac = ans['components']
        assert ac['floor']['floor_num'] == '15'
        assert ac['floor']['floor_type'] == 'FL'
        assert ac['address_unit']['unit_num'] == '6'
        assert ac['address_unit']['unit_type'] == 'APT'  


def test_floor15_office(p, mkt):
    examples = [
    "Floor 15 Office",
    "Office Floor 15",
    "FL 15 OFC",
    "OFC FL 15"      
    ]
    for test_addr in examples:
        ans = p.parse(mkt + test_addr)
        ac = ans['components']
        assert ac['floor']['floor_num'] == '15'
        assert ac['floor']['floor_type'] == 'FL'
        assert ac['address_unit']['unit_num'] is None
        assert ac['address_unit']['unit_type'] == 'OFC'  


def test_15f(p, mkt):
    test_addr = mkt + "15F"
    ans = p.parse(test_addr)
    ac = ans['components']
    assert ac['floor']['floor_num'] == '15'
    assert ac['floor']['floor_type'] == 'FL'
    assert ac['address_unit']['unit_num'] == '15'
    assert ac['address_unit']['unit_type'] == 'FL'   


def test_floor_word(p, mkt):
    examples = [
        "Ground Floor",
        "Floor Ground"
    ]
    for test_addr in examples:
        ans = p.parse(mkt + test_addr)
        ac = ans['components']
        assert ac['floor']['floor_num'] == 'GROUND'
        assert ac['floor']['floor_type'] == 'FL'
        assert ac['address_unit']['unit_num'] == 'GROUND'
        assert ac['address_unit']['unit_type'] == 'FL'

def test_standalone_number(p, mkt):
    # This should not parse as a floor
    test_addr = mkt + "15"
    ans = p.parse(test_addr)
    ac = ans['components']
    assert ac['floor']['floor_num'] is None 
    assert ac['floor']['floor_type'] is None    

def test_adversarially_long_input(p, mkt):
    test_addr = mkt + "FL 99999999999999999"
    ans = p.parse(test_addr)
    ac = ans['components']
    assert ac['floor']['floor_num'] is None 
    assert ac['floor']['floor_type'] is None 
    assert ac['address_unit']['unit_num'] is None 
    assert ac['address_unit']['unit_type'] is None    
   
def test_11th_floor(p, mkt):
    test_addr = mkt + "11TH FL"
    ans = p.parse(test_addr)
    ac = ans['components']
    assert ac['floor']['floor_num'] == '11'
    assert ac['floor']['floor_type'] == 'FL' 
    assert ac['address_unit']['unit_num'] == '11' 
    assert ac['address_unit']['unit_type'] == 'FL'    

def test_floor_lstrip_0(p, mkt):
    test_addr = mkt + "01ST FL"
    ans = p.parse(test_addr)
    ac = ans['components']
    assert ac['floor']['floor_num'] == '1'
    assert ac['floor']['floor_type'] == 'FL' 
    assert ac['address_unit']['unit_num'] == '1' 
    assert ac['address_unit']['unit_type'] == 'FL' 

def test_apt_nf(p):
    test_addr = '1326 S BROAD ST APT 1F'
    ans = p.parse(test_addr)
    ac = ans['components']
    assert ac['floor']['floor_num'] is None 
    assert ac['floor']['floor_type'] is None
    assert ac['address_unit']['unit_num'] == '1F'
    assert ac['address_unit']['unit_type'] == 'APT' 

def test_apt_number_ends_in_f(p):
    test_addr = '3411F SPRING GARDEN ST'
    ans = p.parse(test_addr)
    ac = ans['components']    
    assert ac['floor']['floor_num'] is None 
    assert ac['floor']['floor_type'] is None

def test_18261F_edgecase(p):
    test_addr = '1826 GREEN ST # 18261F'
    ans = p.parse(test_addr)
    ac = ans['components']    
    assert ac['floor']['floor_num'] is None 
    assert ac['floor']['floor_type'] is None
    assert ac['address_unit']['unit_num'] == '18261F'
    assert ac['address_unit']['unit_type'] == '#' 

def test_populate_floor_field_from_old_way(p):
    test_addr = '1517 ARROTT ST # 2ND' # this parsed to '1517 ARROTT ST FL 2' already using apt_std lookup or something like it
    ans = p.parse(test_addr)
    ac = ans['components']
    # make sure that unit field values get copied back to floor field
    assert ac['floor']['floor_num'] == ac['address_unit']['unit_num'] == '2'
    assert ac['floor']['floor_type'] == ac['address_unit']['unit_type'] == 'FL'
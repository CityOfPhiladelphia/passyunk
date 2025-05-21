from passyunk.parser import PassyunkParser
from passyunk.parser import parse 
import pytest

@pytest.fixture
def p():
    return PassyunkParser()

@pytest.fixture
def MAX_RANGE():
    return 200


def test_latlon(p):
    resp = p.parse("-75 40")
    assert resp["type"] == "latlon"

def test_latlon_outofrange(p):
    resp = p.parse("-99 99")
    assert resp["type"] == "none"

def test_latlon_nonclass(MAX_RANGE):
    resp = parse("-75 40", MAX_RANGE)
    assert resp.type == "latlon"

def test_stateplane(p):
    resp = p.parse("2_700_000 260_000")
    assert resp["type"] == "stateplane"

def test_stateplane_outofrange(p):
    resp = p.parse("9999999 99999999")
    assert resp["type"] == "none"

def test_stateplane_nonclass(MAX_RANGE):
    resp = parse("2_700_000 260_000", MAX_RANGE)
    assert resp.type == "stateplane"

def test_opa_account(p):
    resp = p.parse("123456789")
    assert resp["type"] == "opa_account"

def test_opa_account_nonclass(MAX_RANGE):
    resp = parse("123456789", MAX_RANGE)
    assert resp.type == "opa_account"

def test_mapreg(p):
    resp = p.parse("123N12-1234")
    assert resp["type"] == "mapreg"

def test_mapreg_nonclass(MAX_RANGE):
    resp = parse("123N12-1234", MAX_RANGE)
    assert resp.type == "mapreg"

def test_zip(p):
    resp = p.parse("19103")
    assert resp["type"] == "zipcode"

def test_zip_outofrange(p):
    resp = p.parse("00000")
    assert resp["type"] == "none"

def test_zip_nonclass(MAX_RANGE):
    resp = parse("19103", MAX_RANGE)
    assert resp.type == "zipcode"

def test_intersection_addr(p):
    resp = p.parse("MARKET & BROAD ST")
    assert resp["type"] == "intersection_addr"

def test_intersection_addr_nonclass(MAX_RANGE):
    resp = parse("MARKET & BROAD ST", MAX_RANGE)
    assert resp.type == "intersection_addr"

def test_block(p):
    resp = p.parse("100 BLOCK OF BROAD ST")
    assert resp["type"] == "block" 

def test_block_nonclass(MAX_RANGE):
    resp = parse("100 BLOCK OF BROAD ST", MAX_RANGE)
    assert resp.type == "block" 

def test_address(p):
    resp = p.parse("1234 MARKET ST")
    assert resp["type"] == "address"

def test_address_nonclass(MAX_RANGE):
    resp = parse("1234 MARKET ST", MAX_RANGE)
    assert resp.type == "address"

def test_landmark(p):
    resp = p.parse("CITY HALL")
    assert resp["type"] == "landmark"

def test_landmark_nonclass(MAX_RANGE):
    resp = parse("CITY HALL", MAX_RANGE)
    assert resp.type == "landmark"
 
def test_opal_location_id_type(p):
    resp = p.parse("L000001")
    assert resp["type"] == "opal_location_id"

def test_opal_location_id_type_nonclass(MAX_RANGE):
    resp = parse("L000001", MAX_RANGE)
    assert resp.type == "opal_location_id"


from passyunk.parser import PassyunkParser
import pytest

@pytest.fixture
def p():
    return PassyunkParser()

def test_long_jfk(p):
    """Make sure that city/state/ZIP are junked appropriately and floor is at end as desired"""
    test_input = "1401 John F. Kennedy Blvd. 10th Floor Philadelphia, PA 19102"
    ans = p.parse(test_input)
    ac = ans["components"]
    print(ac)
    assert ac["output_address"] == "1401 JOHN F KENNEDY BLVD FL 10"
    assert ac["base_address"] == "1401 JOHN F KENNEDY BLVD"
    assert ac["street"]["full"] == "JOHN F KENNEDY BLVD"
    assert ac["street"]["name"] == "JOHN F KENNEDY"
    assert ac["street"]["suffix"] == "BLVD"
    assert ac["floor"]["floor_num"] == "10"
    assert ac["floor"]["floor_type"] == "FL"
    assert ac["mailing"]["zipcode"] == "19102"
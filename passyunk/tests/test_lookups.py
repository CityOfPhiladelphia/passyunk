from passyunk.parser import PassyunkParser
from passyunk.parser_addr import (
    create_suffix_lookup, create_name_switch_lookup, create_centerline_street_lookup, # these names didn't change
    create_dir_lookup, create_saint_lookup, create_namestd_lookup, create_apt_lookup,
    create_aptstd_lookup, create_apte_lookup, 

    issuffix, is_name_switch, is_centerline_name, is_centerline_street_name,
    is_centerline_street_pre, is_centerline_street_suffix, is_dir, is_saint,
    is_name_std, is_apt, is_apt_std, is_apte
)
import pytest

@pytest.fixture
def p():
    return PassyunkParser()

def test_create_dir_lookup(p):
    lookup = create_dir_lookup()
    assert type(lookup) == dict
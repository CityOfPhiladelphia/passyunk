from passyunk.parser import PassyunkParser
from passyunk.parser_addr import (
    csv_path,

    create_suffix_lookup, create_name_switch_lookup, create_centerline_street_lookup, # these names didn't change
    create_dir_lookup, create_ordinal_lookup, create_saint_lookup, create_namestd_lookup, 
    create_apt_lookup, create_aptstd_lookup, create_apte_lookup,

    AddrOrdinal, 

    issuffix, is_name_switch, is_centerline_name, is_centerline_street_name,
    is_centerline_street_pre, is_centerline_street_suffix, is_dir, is_saint,
    is_name_std, is_apt, is_apt_std, is_apte
)
import pytest
import subprocess

@pytest.fixture
def p():
    return PassyunkParser()

def csv_line_count(thing):
    path = csv_path(thing)
    result = subprocess.run(['wc', '-l', path], stdout=subprocess.PIPE)
    return int(result.stdout.split()[0])


# Test each create_...lookup() function to see if it exists and returns a dict
# of the right size, i.e. has scanned through the right csv to create keys for
# each row.

def test_create_suffix_lookup(p):
    lookup = create_suffix_lookup()
    len_csv = csv_line_count('suffix')
    assert type(lookup) == dict
    print(f"CSV: {len_csv}, Lookup: {len(lookup)}")
    # Sometimes the lookup is slightly smaller than the csv, probably because
    # of repeat keys. It's never bigger
    assert len_csv >= len(lookup) >= int(len(lookup) * 0.99)

def test_create_name_switch_lookup(p):
    lookup = create_name_switch_lookup()
    len_csv = csv_line_count('name_switch')
    assert type(lookup) == dict
    print(f"CSV: {len_csv}, Lookup: {len(lookup)}")
    assert len_csv >= len(lookup) >= int(len(lookup) * 0.99)

# this one has to be different because it returns five things, not one
def test_create_centerline_street_lookup(p):
    # TODO: figure out appropriate lengths for each of these
    lookup, lookup_list, lookup_name, lookup_pre, lookup_suffix = create_centerline_street_lookup()
    len_csv = csv_line_count('centerline_streets')
    for thing in [lookup, lookup_name, lookup_pre, lookup_suffix]:
        assert type(thing) == dict
        print(f"CSV: {len_csv}, Thing: {len(thing)}")
        assert len_csv >= len(thing)
    assert type(lookup_list) == list
    print(f"List: {len(lookup_list)}")
    assert len(lookup_list) == len_csv

def test_create_dir_lookup(p):
    lookup = create_dir_lookup()
    len_csv = csv_line_count('directional')
    assert type(lookup) == dict
    print(f"CSV: {len_csv}, Lookup: {len(lookup)}")
    assert len_csv >= len(lookup) >= int(len(lookup) * 0.99)

def test_create_ordinal_lookup(p): 
    lookup = create_ordinal_lookup()
    # This one is manual since its keys are hardcoded
    assert type(lookup) == dict
    assert set(lookup.keys()) == {
        '1', '11', '2', '12', '3', '13', '4', '5', '6', '7', '8', '9', '0'
    }
    for key in lookup.keys():
        assert type(lookup[key]) == AddrOrdinal
        assert lookup[key].ordigit == key
        if key == '1':
            assert lookup[key].orsuffix == 'ST'
        elif key == '2':
            assert lookup[key].orsuffix == 'ND'
        elif key == '3':
            assert lookup[key].orsuffix == 'RD'
        else:
            assert lookup[key].orsuffix == 'TH'

def test_create_saint_lookup(p):
    lookup = create_saint_lookup()
    len_csv = csv_line_count('saint')
    assert type(lookup) == dict
    print(f"CSV: {len_csv}, Lookup: {len(lookup)}")
    assert len_csv >= len(lookup) >= int(len(lookup) * 0.99)

def test_create_namestd_lookup(p):
    lookup = create_namestd_lookup()
    len_csv = csv_line_count('std')
    assert type(lookup) == dict
    print(f"CSV: {len_csv}, Lookup: {len(lookup)}")
    assert len_csv >= len(lookup) >= int(len(lookup) * 0.99)

def test_create_apt_lookup(p):
    lookup = create_apt_lookup()
    len_csv = csv_line_count('apt')
    assert type(lookup) == dict
    print(f"CSV: {len_csv}, Lookup: {len(lookup)}")
    assert len_csv >= len(lookup) >= int(len(lookup) * 0.99)

def test_create_aptstd_lookup(p):
    lookup = create_aptstd_lookup()
    len_csv = csv_line_count('apt_std')
    assert type(lookup) == dict
    print(f"CSV: {len_csv}, Lookup: {len(lookup)}")
    assert len_csv >= len(lookup) >= int(len(lookup) * 0.99)

def test_create_apte_lookup(p):
    lookup = create_apte_lookup()
    len_csv = csv_line_count('apte')
    assert type(lookup) == dict
    print(f"CSV: {len_csv}, Lookup: {len(lookup)}")
    assert len_csv >= len(lookup) >= int(len(lookup) * 0.99)


# Test each is_...() function to see if desired behavior occurs

def test_issuffix(p):
    print(issuffix("ALLEY").std)
    assert issuffix("ALLEY").std == '2'


from passyunk.parser import PassyunkParser
from passyunk.parser_addr import (
    csv_path,

    create_suffix_lookup, create_name_switch_lookup, create_centerline_street_lookup, # these names didn't change
    create_dir_lookup, create_ordinal_lookup, create_saint_lookup, create_namestd_lookup, 
    create_apt_lookup, create_aptstd_lookup, create_apte_lookup,

    Nameswitch, CenterlineName, CenterlineNameOnly, Suffix, Directional,
    AddrOrdinal, Saint, Namestd, Apt, AptStd, Apte,

    is_suffix, is_name_switch, is_centerline_name, is_centerline_street_name,
    is_centerline_street_pre, is_centerline_street_suffix, is_dir, is_saint,
    is_name_std, is_apt, is_apt_std, is_apte
)
import pytest
import re
import subprocess

""" HELPERS """

@pytest.fixture
def p():
    return PassyunkParser()

def csv_line_count(thing):
    path = csv_path(thing)
    result = subprocess.run(['wc', '-l', path], stdout=subprocess.PIPE)
    return int(result.stdout.split()[0])

"""
Test each create_...lookup() function to see if it exists and returns a dict
of the right size, i.e. has scanned through the right csv to create keys for
each row.
"""

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


""" Test each is_...() function to see if desired behavior occurs """

def test_is_suffix(p):
    test0 = is_suffix("JUNKNONSENSE") # not a suffix
    test1 = is_suffix("AVE") # standard suffix abbr
    test2 = is_suffix("ALLEY") # long suffix
    test3 = is_suffix("SQU") # common abbr
    for num, resp in enumerate([test0, test1, test2, test3]):
        assert type(resp) == Suffix
        assert set(vars(resp).keys()) == {'full', 'common', 'correct', 'std'}
        assert resp.std == str(num)

def test_is_name_switch(p):
    test_yes = is_name_switch("N TANEY ST") # doubles as test of TANEY/LECOUNT switch sticking
    test_no = is_name_switch("JUNKNONSENSE ST")
    for tst in [test_yes, test_no]:
        assert type(tst) == Nameswitch
    assert vars(test_yes) == {'pre': 'N', 'name': 'LECOUNT', 'suffix': 'ST', 'post': '', 'name_from': 'N TANEY ST'}
    assert vars(test_no) == {'pre': ' ', 'name': '0', 'suffix': ' ', 'post': ' ', 'name_from': ' '}

def test_is_centerline_name(p):
    test_yes = is_centerline_name("E WASHINGTON LN N") # has all five fields
    test_no = is_centerline_name("NOTPREFIX JUNK ST NOTSUFFIX")
    for tst in [test_yes, test_no]:
        assert type(tst) == CenterlineName
    assert vars(test_yes) == {'full': 'E WASHINGTON LN N', 'pre': 'E', 'name': 'WASHINGTON', 'suffix': 'LN', 'post': 'N'}
    assert vars(test_no) == {'full': '0', 'pre': ' ', 'name': ' ', 'suffix': ' ', 'post': ' '}

def test_is_centerline_street_name(p):
    test_yes = is_centerline_street_name("BROAD") 
    for ix, result in enumerate(test_yes): # should be a list of length 2
        assert type(result) == CenterlineName
        assert result.full == 'N BROAD ST' if ix == 0 else 'S BROAD ST'
        assert result.pre == 'N' if ix == 0 else 'S'
        assert result.name == 'BROAD'
        assert result.suffix == 'ST'
        assert result.post == ''
    test_no = is_centerline_street_name("JUNK")
    assert test_no == [' ', 0, 0]

def test_is_centerline_street_pre(p):
    test_yes = is_centerline_street_pre("N BROAD") # will be a list of length 1
    assert type(test_yes[0]) == CenterlineName
    assert vars(test_yes[0]) == {'full': 'N BROAD ST', 'pre': 'N', 'name': 'BROAD', 'suffix': 'ST', 'post': ''}
    test_no = is_centerline_street_pre("X JUNK")
    assert test_no == [' ', 0, 0]

def test_is_centerline_street_suffix(p):
    test_yes = is_centerline_street_suffix("WASHINGTON LN") # will be a list of length 5:
    # WASHINGTON LN, E WASHINGTON LN, E WASHINGTON LN N, E WASHINGTON LN S, W WASHINGTON LN
    for ix, result in enumerate(test_yes): # should be a list of length 2
        assert type(result) == CenterlineName
        assert set(vars(result).keys()) == {'full', 'pre', 'name', 'suffix', 'post'}
        assert result.name == 'WASHINGTON'
        assert result.suffix == 'LN'
        # check that suffix, if present, matches the full street name in pdata
        match_ending = re.search(r'(?<= )(N|S)$', result.full)
        if match_ending:
            assert match_ending.group(0) == result.post

def test_is_dir(p):
    full_to_common = {'NORTH': 'N', 'EAST': 'E', 'SOUTH': 'S', 'WEST': 'W'}
    common_to_full = {v:k for k,v in full_to_common.items()}
    for dir_correct in common_to_full.keys():
        test_yes = is_dir(dir_correct)
        assert type(test_yes) == Directional
        assert test_yes.full == common_to_full[dir_correct]
        assert test_yes.common == test_yes.correct == dir_correct
        assert test_yes.std == '1'
    for dir_long in full_to_common.keys():
        test_yes = is_dir(dir_long)
        assert type(test_yes) == Directional
        assert test_yes.full == test_yes.common == dir_long
        assert test_yes.correct == full_to_common[dir_long]
        assert test_yes.std == '2'
    test_no = is_dir("JUNK")
    assert type(test_no) == Directional
    assert vars(test_no) == {'full': ' ', 'common': 'JUNK', 'correct': ' ', 'std': '0'}

def test_is_saint(p): # is_saint() returns a boolean, so just check that
    assert is_saint("MALACHY")
    assert not is_saint("ROLAND")

def test_is_name_std(p):
    test_found = is_name_std("PAAAYUNK")
    assert type(test_found) == Namestd
    assert test_found.correct == "PASSYUNK"
    test_notfound = is_name_std("JUNKNONSENSE")
    assert type(test_notfound) == Namestd
    assert test_notfound.correct == ''

def test_is_apt(p):
    test_yes = is_apt("APARTMENT")
    test_no = is_apt("APATOSAURUS")
    for tst in [test_yes, test_no]:
        assert type(tst) == Apt
    assert test_yes.correct == 'APT'
    assert test_no.correct == ''

def test_is_apt_std(p): # is_apt_std() returns a string, so just check that
    assert is_apt_std("001G") == '1G' # common on left of csv, correct on right, unlike many others
    assert is_apt_std("JUNK") == ''

def test_is_apte(p):
    apte_yes = is_apte('LOBBY')
    assert type(apte_yes) == Apte
    assert apte_yes.correct == 'LBBY'
    apte_no = is_apte('JUNK')
    assert type(apte_no) == Apte
    assert apte_no.correct == ''
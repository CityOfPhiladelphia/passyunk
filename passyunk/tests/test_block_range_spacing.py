import pytest

from passyunk.parser import PassyunkParser


@pytest.fixture
def p():
    return PassyunkParser()


def test_block_range_with_hyphen_whitespace(p):
    compact = p.parse('1800-1899 block blair st')
    spaced = p.parse('1800   -   1899 block blair st')

    assert compact['type'] == 'block'
    assert spaced['type'] == 'block'
    assert spaced['components']['base_address'] == compact['components']['base_address']
    assert spaced['components']['output_address'] == compact['components']['output_address']

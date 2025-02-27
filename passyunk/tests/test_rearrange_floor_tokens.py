from passyunk.rearrange_floor_tokens import rearrange_floor_tokens
import pytest

examples = {
('MARKET', 'ST', '15F') : ['MARKET', 'ST', 'FL', '15'],
('MARKET', 'ST', '15FL') : ['MARKET', 'ST', 'FL', '15'],
('MARKET', 'ST', 'GROUND', 'FLOOR') : ['MARKET', 'ST', 'FLOOR', 'GROUND'],
('MARKET', 'ST', 'FLOOR', '15', 'OFFICE') : ['MARKET', 'ST', 'OFFICE', 'FLOOR', '15'],
('MARKET', 'ST', 'FLOOR', '15', 'APT') : ['MARKET', 'ST', 'APT', 'FLOOR', '15'],
('MARKET', 'ST', 'UNIT', '#', '6', 'FLOOR', '#', '15') : ['MARKET', 'ST', 'UNIT', '#', '6', 'FLOOR', '#', '15'],
('MARKET', 'ST', 'FLOOR', '#', '15', 'UNIT', '#', '6') : ['MARKET', 'ST', 'UNIT', '#', '6', 'FLOOR', '#', '15'],
('MARKET', 'ST', 'GROUND', 'FLOOR', 'LBBY') : ['MARKET', 'ST', 'LBBY', 'FLOOR', 'GROUND'], # failing
('MARKET', 'ST', 'FL', '#', '15', 'UNIT', '6') : ['MARKET', 'ST', 'UNIT', '6', 'FL', '#', '15'],
('1234', 'MARKET', 'ST', 'FLOOR', '7', 'JUNK', 'TRASH', 'GARBAGE') : ['1234', 'MARKET', 'ST', 'JUNK', 'TRASH', 'GARBAGE', 'FLOOR', '7'],
('1234', 'MARKET', 'ST', '15F', 'TRASH', 'NONSENSE'): ['1234', 'MARKET', 'ST', 'TRASH', 'NONSENSE', 'FL', '15'],
}

def test_rearrange_floor_tokens():
    for k, v in examples.items():
        assert rearrange_floor_tokens(list(k)) == v

def test_rearrange_apt_nf():
    assert rearrange_floor_tokens(['1234', 'MARKET', 'ST', 'APT', '3F']) == ['1234', 'MARKET', 'ST', 'APT', '3F'] # should not change

def test_rearrange_unit_nf():
    assert rearrange_floor_tokens(['1234', 'MARKET', 'ST', 'UNIT', '3F']) == ['1234', 'MARKET', 'ST', 'UNIT', '3F'] # should not change    

def test_rearrange_pound_nf():
        assert rearrange_floor_tokens(['1234', 'MARKET', 'ST', '#', '3F']) == ['1234', 'MARKET', 'ST', '#', '3F'] # should not change
from passyunk.rearrange_floor_tokens import rearrange_floor_tokens
import pytest


def test_basic1():
    assert rearrange_floor_tokens(['MARKET', 'ST', '15F']) == ['MARKET', 'ST', 'FL', '15']

def test_basic2():
    assert rearrange_floor_tokens(['MARKET', 'ST', '15FL']) == ['MARKET', 'ST', 'FL', '15']

def test_basic3():
    assert rearrange_floor_tokens(['MARKET', 'ST', 'GROUND', 'FLOOR']) == ['MARKET', 'ST', 'FLOOR', 'GROUND']

def test_basic4():
    assert rearrange_floor_tokens(['MARKET', 'ST', 'FLOOR', '15', 'OFFICE']) == ['MARKET', 'ST', 'OFFICE', 'FLOOR', '15']

def test_basic5():
    assert rearrange_floor_tokens(['MARKET', 'ST', 'FLOOR', '15', 'APT']) == ['MARKET', 'ST', 'APT', 'FLOOR', '15']

def test_asterisks1():
    assert rearrange_floor_tokens(['MARKET', 'ST', 'UNIT', '#', '6', 'FLOOR', '#', '15']) == ['MARKET', 'ST', 'UNIT', '#', '6', 'FLOOR', '15']

def test_asterisks2():
    assert rearrange_floor_tokens(['MARKET', 'ST', 'FLOOR', '#', '15', 'UNIT', '#', '6']) == ['MARKET', 'ST', 'UNIT', '#', '6', 'FLOOR', '15']

def test_asterisks3():
    assert rearrange_floor_tokens(['MARKET', 'ST', 'FL', '#', '15', 'UNIT', '6']) == ['MARKET', 'ST', 'UNIT', '6', 'FL', '15']

def test_lbby():
    assert rearrange_floor_tokens(['MARKET', 'ST', 'GROUND', 'FLOOR', 'LBBY']) == ['MARKET', 'ST', 'LBBY', 'FLOOR', 'GROUND']

def test_rearrange_trash():
    assert rearrange_floor_tokens(['1234', 'MARKET', 'ST', 'FLOOR', '7', 'JUNK', 'TRASH', 'GARBAGE']) == ['1234', 'MARKET', 'ST', 'JUNK', 'TRASH', 'GARBAGE', 'FLOOR', '7']

def test_rearrange_trash2():
    assert rearrange_floor_tokens(['1234', 'MARKET', 'ST', '15F', 'TRASH', 'NONSENSE']) == ['1234', 'MARKET', 'ST', 'TRASH', 'NONSENSE', 'FL', '15']

# Things that should not be changed by this function

def test_rearrange_apt_nf():
    assert rearrange_floor_tokens(['1234', 'MARKET', 'ST', 'APT', '3F']) == ['1234', 'MARKET', 'ST', 'APT', '3F']

def test_rearrange_unit_nf():
    assert rearrange_floor_tokens(['1234', 'MARKET', 'ST', 'UNIT', '3F']) == ['1234', 'MARKET', 'ST', 'UNIT', '3F']  

def test_rearrange_pound_nf():
    assert rearrange_floor_tokens(['1234', 'MARKET', 'ST', '#', '3F']) == ['1234', 'MARKET', 'ST', '#', '3F']

def test_rearrange_side_nf():
    assert rearrange_floor_tokens('1009 S 8TH ST SIDE 2F'.split()) == '1009 S 8TH ST SIDE 2F'.split()

def test_rearrange_streetnumber_ends_in_f():
    assert rearrange_floor_tokens('3411F SPRING GARDEN ST'.split()) == '3411F SPRING GARDEN ST'.split()

def test_lstrip_0_from_floornum():
    assert rearrange_floor_tokens('3405 ARTHUR ST # 01ST FL'.split()) == ['3405', 'ARTHUR', 'ST', '#', 'FL', '1']
#from data import APTFLOOR, NON_NUMERIC_FLOORS # for standalone testing of file, uncomment this and comment line below
from .data import APTFLOOR, NON_NUMERIC_FLOORS
import re

def is_floor_num(token: str) -> bool:
    """Check whether this token can come AFTER a word for floor."""
    return (token.isdigit() or 
            token in NON_NUMERIC_FLOORS or
            (token[0] == '#' and token[1:].isdigit()))

ORD_RE = r'(\d)(ST|ND|RD|TH)' # will match string endings such as 1ST, 11TH, 2ND, 3RD, 4TH...

def is_floor_ordinal(token: str) -> bool:
    """Check whether this token can come BEFORE a word for floor."""
    return (len(token) >= 3 and 
            (re.search(ORD_RE, token) or 
             token in NON_NUMERIC_FLOORS))


def remove_ordinal_suffix(token: str) -> str:
    return re.sub(ORD_RE, r'\1', token).lstrip('0')


# TODO: consider replacing with a csv-derived lookup object in line with create_aptstd_lookup
# TODO: consider eliminating this option altogether since a lot of legit addresses are e.g. '...APT 2F' or 'UNIT 2F'
def is_oneword_floor(token: str) -> bool:
    if len(token) > 4: # prevent legit unit numbers like #18261F from becoming floors
        return False
    return ((token[:-1].isdigit() and token[-1] == 'F') or
            (token[:-2].isdigit() and token[-2:] == 'FL'))

def rearrange_floor_tokens(tokens: list[str]) -> list[str]:
    """Put the portion of a tokens list representing the floor at the end, so it
    can be easily dealt with in handle_units() prior to preexisting passyunk logic"""
    if len(tokens) < 3:
        return tokens

    if tokens[-1] in APTFLOOR: # e.g. [... "GROUND", "FLOOR"]
        if is_floor_ordinal(tokens[-2]):
            tokens[-2] = remove_ordinal_suffix(tokens[-2])
            moving_token = tokens.pop(-1)
            tokens.insert(-1, moving_token)
            return tokens
    
    if tokens[-2] in APTFLOOR:
        if is_floor_num(tokens[-1]): # e.g. [..."FLOOR", "15"]
            return tokens
        if is_floor_ordinal(tokens[-3]): # e.g. [..."GROUND", "FLOOR", "OFFICE"]
            tokens[-3] = remove_ordinal_suffix(tokens[-3])
            moving_token = tokens.pop(-1)
            tokens.insert(-2, moving_token) # i.e. insert third-to-last
            floor_token = tokens.pop(-1)
            tokens.insert(-1, floor_token)
            return tokens
    
    if is_oneword_floor(tokens[-1]): # e.g. [... "15F"] 
        if tokens[-2] in ['APT', 'UNIT', '#', 'FRNT', 'SIDE', 'STE']: # but not e.g. [... 'UNIT', '1F']
            return tokens
        moving_token = tokens.pop(-1)
        moving_token = re.sub(r'F|L|#', '', moving_token)
        tokens.append("FL")
        tokens.append(moving_token)
        return tokens 
    
    if tokens[-3] in APTFLOOR: # e.g. [...'FLOOR', '#', '7']
        if tokens[-2] == '#' and is_floor_num(tokens[-1]):
            tokens.pop(-2)
            return tokens
        
    # Walk back through the tokens, looking for a floor designator earlier in the input
    for ix, token in enumerate(tokens[::-1]): 
        nix = -ix - 1 # get the pythonic negative index
        if nix >= -2:
            continue
        if nix == -len(tokens): # street numbers like '3411F SPRING GARDEN ST' should remain unchanged
            break
        if token in APTFLOOR:
            if is_floor_num(tokens[nix+1]): # e.g. [...'FLOOR', '7', ...]
                moving_slice = tokens[nix:nix+2]
                before_tokens = tokens[:nix]
                after_tokens = tokens[nix+2:] 
                tokens = before_tokens + after_tokens + moving_slice
                # tokens[-1] = no_numbersign(tokens[-1])
                return tokens
            if tokens[nix+1] == '#' and tokens[nix+2].isdigit(): # e.g. [...'FLOOR', '#', '7', ...]
                moving_slice = tokens[nix:nix+3]
                before_tokens = tokens[:nix]
                after_tokens = tokens[nix+3:]
                tokens = before_tokens + after_tokens + moving_slice
                tokens.pop(-2)
                return tokens
            if is_floor_ordinal(tokens[nix-1]): # e.g. [...'GROUND', 'FLOOR', ...] or [... '15TH', 'FLOOR', ...]
                ordinal = tokens[nix-1]
                fl = tokens[nix]
                before_tokens = tokens[:nix-1]
                after_tokens = tokens[nix+1:]
                tokens = before_tokens + after_tokens
                tokens.append(fl)
                tokens.append(remove_ordinal_suffix(ordinal))
                return tokens 
        if is_oneword_floor(token): # e.g. [... '15F' ...]
            moving_token = tokens.pop(nix)
            moving_token = moving_token.replace('L', '').replace('F', '')
            tokens.append("FL")
            tokens.append(moving_token)
            return tokens
    
    return tokens 
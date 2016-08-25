import re

__author__ = 'tom.swanson'
aptfloor = ['FL', 'FLR', 'FLOOR']
CONJUNCTIONS = ['AND', '@', '\\', 'AT', '&']
STATELIST = ['PA', 'PENNSYLVANIA']
CITYLIST = ['PHILADELPHIA', 'PHILA', 'PHILLY', 'PHILADELPHA', 'PHILADELPHIA', 'PHILADELHIA', 'PHIALDELPHIA',
            'PHILADLPHIA']
CARDINAL_DIR = ['N', 'E', 'S', 'W']
PREPOSTDIR = ['INDEPENDENCE MALL', 'SCHUYLKILL AVE', 'WASHINGTON LN']
POSTDIR = ['LOGAN CIR', 'PINE PL', 'ASHMEAD PL', 'MARWOOD RD']
PREDIR_AS_NAME = ['WEST END', 'EAST FALLS']
SUFFIX_IN_NAME = ['SPRING GRDN', 'AUTUMN HL', 'CHESTNUT HL', 'COBBS CRK', 'DELAIRE LNDG', 'HICKORY HL', 'FAIR HL',
                  'HUNTING PARK', 'AYRDALE CRES']
APTSPECIAL_2TOKEN = ['2ND FL', '1ST FL', '2ND', '1ST', 'PINE PL', 'SCHUYLKILL AVE']
APTSPECIAL_1TOKEN = ['2ND', '1ST', '2R', '1R', '01FL', '02FL', '03FL']

zipcode_re = re.compile('^(\d{5}(\-\d{4})?)?$')

# 9 digit numeric
opa_account_re = re.compile('^(\d{9})?$')

po_box_re = re.compile('^P(\.|OST)? ?O(\.|FFICE)? ?BOX (?P<num>\w+)$')

# These are all the special characters that are allowed in input addresses.
# A few chars have to be escape for regex purposes: - ^ ] \
SPECIAL_CHARS_ALLOWED = r' \-\\\t/&@,.#'
# Add alphanumerics to special chars allowed, negate, and compile regex object.
ILLEGAL_CHARS_RE = re.compile('[^A-Z0-9{}]'.format(SPECIAL_CHARS_ALLOWED))


class Enum(set):
    def __getattr__(self, name):
        if name in self:
            return name
        raise AttributeError


AddrType = Enum(['none', 'address', 'account', 'street', 'intersection_addr', 'block', 'place', 'pobox', 'zipcode'])

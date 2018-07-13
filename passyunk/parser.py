"""

Philadelphia Address Standardizer

Author: Tom Swanson

Created: 8/25/2014
Last Updated: 2/9/2016

Version: 1.0

"""

from __future__ import absolute_import

import csv
import os
import re
import sys
import warnings
from copy import deepcopy
from shapely.geometry import mapping
from .centerline import create_cl_lookup, get_cl_info, get_cl_info_street2, create_al_lookup, create_int_lookup, \
    get_address_geom
from .data import opa_account_re, zipcode_re, po_box_re, mapreg_re, AddrType, \
    ILLEGAL_CHARS_RE
from .election import create_election_lookup, get_election_info
from .parser_addr import parse_addr_1, name_switch, is_centerline_street_name, is_centerline_street_pre, \
    is_centerline_street_suffix, is_centerline_name, Address
from .zip4 import create_zip4_lookup, get_zip_info
from .landmark import Landmark

is_cl_file = False
is_al_file = False
is_election_file = False
is_zip_file = False


class AddressUber:
    def __init__(self):
        self.components = Address()
        self.input_address = ''
        self.type = ''

    def __repr__(self):
        return self.__str__()


class Nameswitch:
    def __init__(self, row):
        self.pre = row[0]
        self.name = row[1]
        self.suffix = row[2]
        self.post = row[3]
        self.name_from = row[4]


class CenterlineName:
    def __init__(self, row):
        self.full = row[0]
        self.pre = row[1]
        self.name = row[2]
        self.suffix = row[3]
        self.post = row[4]


class CenterlineNameOnly:
    def __init__(self, row):
        self.name = row[0]
        self.low = row[1]
        self.high = row[2]


'''
SETUP FUNCTIONS
'''


def csv_path(file_name):
    return os.path.join(cwd, file_name + '.csv')


def create_name_switch_lookup():
    path = csv_path('name_switch')
    f = open(path, 'r')
    lookup = {}
    try:
        reader = csv.reader(f)
        for row in reader:
            r = Nameswitch(row)
            lookup[r.name_from] = r
    except IOError:
        print('Error opening ' + path, sys.exc_info()[0])
    f.close()
    return lookup


def create_centerline_street_lookup():
    path = csv_path('centerline_streets')
    f = open(path, 'r')
    lookup = {}
    lookup_name = {}
    lookup_pre = {}
    lookup_suffix = {}
    lookup_list = []
    i = 0
    j = 0
    jpre = 0
    jsuff = 0

    try:
        reader = csv.reader(f)
        previous = ''
        rp = ''
        previous_pre_name = ''
        previous_suffix = ''
        for row in reader:
            r = CenterlineName(row)
            if i == 0:
                rp = r
            current = r.name
            current_pre_name = r.pre + ' ' + r.name
            current_suffix = r.name + ' ' + r.suffix
            if current != previous and i != 0:
                ack = [previous, j, i]
                r2 = CenterlineNameOnly(ack)
                lookup_name[previous] = r2
                j = i
            if current_pre_name != previous_pre_name and i != 0:
                ack = [previous_pre_name, jpre, i]
                r2 = CenterlineNameOnly(ack)
                if rp.pre != '':
                    lookup_pre[previous_pre_name] = r2
                jpre = i
            if current_suffix != previous_suffix and i != 0:
                ack = [previous_suffix, jsuff, i]
                r2 = CenterlineNameOnly(ack)
                if rp.suffix != '':
                    lookup_suffix[previous_suffix] = r2
                jsuff = i
            lookup_list.append(r)
            lookup[r.full] = r
            rp = r
            previous = current
            previous_pre_name = current_pre_name
            previous_suffix = current_suffix
            i += 1

    except IOError:
        print('Error opening ' + path, sys.exc_info()[0])
    f.close()
    return lookup, lookup_list, lookup_name, lookup_pre, lookup_suffix


def create_full_names(address, addr_type):
    if addr_type == AddrType.opa_account or addr_type == AddrType.zipcode:
        return address

    temp = '%s %s %s %s' % (address.street.predir, address.street.name, address.street.suffix, address.street.postdir)
    address.street.full = ' '.join(temp.split())

    temp = '%s %s %s %s' % (
        address.street_2.predir, address.street_2.name, address.street_2.suffix, address.street_2.postdir)
    address.street_2.full = ' '.join(temp.split())

    if address.address.isaddr:
        # no Range
        if address.address.low_num >= 0 > address.address.high_num:
            address.address.full = address.address.low
            # if address.address.addr_suffix != '':
            #    address.address.full = address.address.full+address.address.addr_suffix
            if address.address.fractional != '':
                address.address.full = address.address.full + ' ' + address.address.fractional

        # return a full range - if there's a fraction, ignore
        elif addr_type == AddrType.block and address.address.low_num != address.address.high_num:
            address.address.full = address.address.low + '-' + address.address.high
        elif address.address.addrnum_type == 'NNNNA-NN' or address.address.addrnum_type == 'NNNN-NN':
            # city address range
            temp_num = address.address.high_num % 100
            if temp_num < 10:
                temp = '0' + str(temp_num)
            else:
                temp = str(temp_num)
            # if address.address.addr_suffix != '' and address.address.fractional != '':
            #     address.address.full = address.address.low + address.address.addr_suffix + '-' + temp + ' ' +
            # address.address.fractional
            # elif address.address.addr_suffix != '':
            #     address.address.full = address.address.low + address.address.addr_suffix + '-' + temp
            if address.address.fractional != '':
                address.address.full = address.address.low + '-' + temp + ' ' + address.address.fractional
            else:
                address.address.full = address.address.low + '-' + temp
        else:

            if address.address.fractional != '':
                address.address.full = address.address.low + '-' + \
                                       address.address.high + ' ' + \
                                       address.address.fractional
            elif address.address.low != '' and address.address.high != '':
                address.address.full = address.address.low + '-' + address.address.high
            else:
                address.address.full = ''
    # if you have an address number, use it even if it is and intersections
    if address.address.isaddr:
        address.base_address = address.address.full + ' ' + address.street.full
        addr_type == AddrType.address
    elif addr_type == AddrType.intersection_addr:
        address.base_address = address.street.full + ' & ' + address.street_2.full
    else:
        address.base_address = address.street.full

    return address


def centerline_rematch(address):
    # If only street name provided and there is only one version of the full name...
    # 1234 Berks => 1234 Berks St

    if address.predir == '' and address.postdir == '' and address.suffix == '':
        test = address.name
        centerline_name = is_centerline_street_name(test)
        if len(centerline_name) == 1:
            address.predir = centerline_name[0].pre
            address.name = centerline_name[0].name
            address.suffix = centerline_name[0].suffix
            address.postdir = centerline_name[0].post
            address.parse_method = 'CL_N'
            address.is_centerline_match = True
            return
        if len(test) > 3 and test[-1] == 'S':
            test = test[0:-1]
            centerline_name = is_centerline_street_name(test)
            if len(centerline_name) == 1:
                address.predir = centerline_name[0].pre
                address.name = centerline_name[0].name
                address.suffix = centerline_name[0].suffix
                address.postdir = centerline_name[0].post
                address.parse_method = 'CL_N'
                address.is_centerline_match = True
                return

    if address.predir != '' and address.postdir == '' and address.suffix == '':
        test = address.predir + ' ' + address.name
        centerline_name = is_centerline_street_pre(test)
        if len(centerline_name) == 1 and centerline_name[0].suffix != '':
            address.predir = centerline_name[0].pre
            address.name = centerline_name[0].name
            address.suffix = centerline_name[0].suffix
            address.postdir = centerline_name[0].post
            address.parse_method = 'CL_P'
            address.is_centerline_match = True

    if address.predir == '' and address.postdir == '' and address.suffix != '':
        test = address.name + ' ' + address.suffix
        centerline_name = is_centerline_street_suffix(test)
        if len(centerline_name) == 1 and centerline_name[0].pre != '':
            address.predir = centerline_name[0].pre
            address.name = centerline_name[0].name
            address.suffix = centerline_name[0].suffix
            address.postdir = centerline_name[0].post
            address.parse_method = 'CL_S'
            address.is_centerline_match = True
            # street_centerline_lookup, street_centerline_name_lookup,name_lookup,pre_lookup,suffix_lookup


# latlon wgs84  Lon -75.0 to - 74 Lat 39 to 40
# state plane Y - 2,600,000 2,800,000  X - 200,000 to 320,000
def xy_check(item):
    tmp = item.strip()
    tmp = tmp.replace('+', '')
    tmp = tmp.replace(',', ' ')
    tmp = ' '.join(tmp.split())
    tokens = tmp.split(' ')
    if len(tokens) != 2:
        return
    try:
        y = float(tokens[0])
    except:
        return
    try:
        x = float(tokens[1])
    except:
        return

    if y < -74.0 and y > -76.0 and x < 41.0 and x > 39.0:
        return 'L%.6f,%.6f' % (y, x)
    elif y < 2800000.0 and y > 2600000.0 and x < 320000.0 and x > 200000.0:
        return 'S%.6f,%.6f' % (y, x)
    else:
        return 'JUNK'


def parse(item, MAX_RANGE):
    # address = Addr()
    address_uber = AddressUber()
    address = address_uber.components
    # latlon_search = latlon_re.search(item)
    item = '' if item is None else item
    is_xy = xy_check(item)
    if not is_xy:
        item = input_cleanup(address_uber, item)

    if item == '':
        address_uber.type = AddrType.none
        # raise ValueError('Address not specified: {}'.format(item))
        # return address_uber

    # if you get a 9 digit numeric, treat it as an OPA account
    opa_account_search = opa_account_re.search(item)
    regmap_search = mapreg_re.search(item)
    zipcode_search = zipcode_re.search(item)
    po_box_search = po_box_re.search(item)
    landmark = Landmark(item)

    if is_xy:
        address_uber.input_address = item
        if is_xy[0] == 'L':
            address_uber.type = AddrType.latlon
            address_uber.components.output_address = is_xy[1:]
        elif is_xy[0] == 'S':
            address_uber.type = AddrType.stateplane
            address_uber.components.output_address = is_xy[1:]
        else:
            address_uber.type = AddrType.none

    elif len(item) == 9 and opa_account_search:
        address_uber.components.output_address = item
        address_uber.type = AddrType.opa_account

    elif (len(item) == 10 or len(item) == 11) and regmap_search:
        address_uber.components.output_address = item.replace('-', '')
        address_uber.type = AddrType.mapreg

    elif len(item) == 5 and zipcode_search:
        if 19100 <= int(item) <= 19199:
            address_uber.components.output_address = item
            address_uber.type = AddrType.zipcode
        else:
            address_uber.components.output_address = item
            address_uber.type = AddrType.none

    elif ' AND ' in item and item[-8:] != ' A AND B' and not item.split(' ')[0].isdigit():
        # if leading digit then don't treat as intersection. TODO: make leading digit test more robust
        tokens = item.split(' AND ')
        if tokens[0][:5] == 'NEAR ':
            tokens[0] = tokens[0][5:]
        address = parse_addr_1(address, tokens[0])
        # for some reason there are numerous addresses like this in the logs - 127 VASSAR ST/LI
        if tokens[1] == 'LI':
            address_uber.type = AddrType.address
        else:
            address2 = Address()
            address2 = parse_addr_1(address2, tokens[1])
            address.street_2 = address2.street
            # get_cl_info(address, address_uber, MAX_RANGE)

    elif po_box_search:
        search = po_box_re.search(item)
        num = search.group('num')
        address_uber.type = AddrType.pobox
        address.street.name = 'PO BOX {}'.format(num)

    else:
        # Look for 'AND' and filter from left
        if 'AND' in item:
            tokens = item.split(' AND ')
            address = parse_addr_1(address, tokens[0])
        else:
            address = parse_addr_1(address, item)
        if address.street.parse_method == 'UNK':
            address_uber.type = AddrType.none
            address_uber.components.output_address = item
        else:
            if address.address.isaddr and address_uber.type != AddrType.block:
                if address.address.addrnum_type == 'RANGE':
                    # address_uber.type = AddrType.range  leaving in case we revisit this logic
                    address_uber.type = AddrType.address
                else:
                    address_uber.type = AddrType.address
                if address.street.name == '':
                    raise ValueError('Parsed address does not have a street name: {}'.format(item))
            elif address_uber.type != AddrType.block:
                address_uber.type = AddrType.none

    name_switch(address)

    if address_uber.type == AddrType.address and not address_uber.components.street.is_centerline_match:
        centerline_rematch(address.street)

    if address_uber.type == AddrType.intersection_addr:
        centerline_rematch(address.street)
        centerline_rematch(address.street_2)

    if address_uber.components.cl_seg_id != '':
        address_uber.components.street.is_centerline_match = True

    create_full_names(address, address_uber.type)

    # create copy of address_uber before alias changes
    address_uber_copy = deepcopy(address_uber)
    address_copy = deepcopy(address)
    # if the users doesn't have the centerline file, parser will still work
    if is_cl_file:
        get_cl_info(address, address_uber, MAX_RANGE)

    # check if landmark if address_uber.type = none or street with a street_2.full value
    if address_uber.type in (AddrType.none, '') or (address_uber.type == AddrType.street and (
                    address_uber.components.street_2.full )):
        landmark.landmark_check()
        if landmark.is_landmark:
            item = landmark.landmark_address
            address = parse_addr_1(address, item)
            address_uber.type = AddrType.address
            get_cl_info(address, address_uber, MAX_RANGE)

    create_full_names(address, address_uber.type)
    # if the users doesn't have the zip4 file, parser will still work
    if is_zip_file:
        get_zip_info(address, address_uber, MAX_RANGE)
        # if the address is an alias the zip file may or may not have the alias listed. If not, try the original
        if not address.mailing.zipcode and address != address_copy:
            get_zip_info(address_copy, address_uber_copy, MAX_RANGE)
            address.mailing.uspstype = address_copy.mailing.uspstype
            address.mailing.bldgfirm = address_copy.mailing.bldgfirm
            address.mailing.zip4 = address_copy.mailing.zip4
            address.mailing.zipcode = address_copy.mailing.zipcode
            address.mailing.matchdesc = address_copy.mailing.matchdesc
        create_full_names(address, address_uber.type)

    # important that full names are created before adding election
    if is_election_file:
        get_election_info(address)
        # if the address is an alias the zip file may or may not have the alias listed. If not, try the original
        if not address.election.blockid and address != address_copy:
            get_election_info(address_copy)
            address.election.blockid = address_copy.election.blockid
            address.election.precinct = address_copy.election.precinct

    if address_uber.components.address_unit.unit_type == '' and address_uber.components.address_unit.unit_num != '':
        address_uber.components.address_unit.unit_type = '#'

    if len(address.mailing.zip4) == 4 and address.mailing.zip4[2:4] == 'ND':
        address.mailing.zip4 = ''
    if address_uber.type == AddrType.intersection_addr and address.base_address.find(' & ') == -1:
        address_uber.type = AddrType.address
    if address_uber.type == AddrType.intersection_addr:
        address_uber.components.output_address = address.base_address
    elif address_uber.type != AddrType.opa_account and \
                    address_uber.type != AddrType.mapreg and \
                    address_uber.type != AddrType.latlon and \
                    address_uber.type != AddrType.stateplane and \
                    address_uber.type != AddrType.zipcode:
        if address.address_unit.unit_num != -1:
            address_uber.components.output_address = address.base_address + ' ' + \
                                                     address.address_unit.unit_type + ' ' + \
                                                     address.address_unit.unit_num
        else:
            address_uber.components.output_address = address.base_address + ' ' + \
                                                     address.address_unit.unit_type + ' '
        address_uber.components.output_address = ' '.join(address_uber.components.output_address.split())
    temp_centerline = is_centerline_name(address_uber.components.street.full)

    if temp_centerline.full != '0':
        address_uber.components.street.is_centerline_match = True

    if address_uber.type == AddrType.street and address.street.street_code == '':
        address_uber.type = AddrType.none

    temp_centerline = is_centerline_name(address_uber.components.street_2.full)
    if temp_centerline.full != '0':
        address_uber.components.street_2.is_centerline_match = True

    if address_uber.components.base_address == '':
        address_uber.components.base_address = None
    if address_uber.components.mailing.zipcode == '':
        address_uber.components.mailing.zipcode = None
    if address_uber.components.mailing.zip4 == '':
        address_uber.components.mailing.zip4 = None
    if address_uber.components.mailing.uspstype == '':
        address_uber.components.mailing.uspstype = None
    if address_uber.components.mailing.bldgfirm == '':
        address_uber.components.mailing.bldgfirm = None
    if address_uber.components.cl_addr_match == '':
        address_uber.components.cl_addr_match = None
    if address_uber.components.mailing.matchdesc == '':
        address_uber.components.mailing.matchdesc = None
    if address_uber.components.cl_responsibility == '':
        address_uber.components.cl_responsibility = None
    if address_uber.components.cl_seg_id == '':
        address_uber.components.cl_seg_id = None
    if address_uber.components.street.street_code == '':
        address_uber.components.street.street_code = None

    if address_uber.components.address.addr_suffix == '':
        address_uber.components.address.addr_suffix = None
    if address_uber.components.address.high_num_full == -1:
        address_uber.components.address.high_num_full = None
    if address_uber.components.address.addrnum_type == '':
        address_uber.components.address.addrnum_type = None
    if address_uber.components.address.fractional == '':
        address_uber.components.address.fractional = None
    if address_uber.components.address.full == '':
        address_uber.components.address.full = None
    if address_uber.components.address.high == '':
        address_uber.components.address.high = None
    if address_uber.components.address.high_num == -1:
        address_uber.components.address.high_num = None
    if address_uber.components.address.isaddr == '':
        address_uber.components.address.isaddr = None
    if address_uber.components.address.low == '':
        address_uber.components.address.low = None
    if address_uber.components.address.low_num == -1:
        address_uber.components.address.low_num = None
    if address_uber.components.address.parity == '':
        address_uber.components.address.parity = None

    if address_uber.components.street.parse_method == '':
        address_uber.components.street.parse_method = None
    if address_uber.components.street.full == '':
        address_uber.components.street.full = None
    if address_uber.components.street.name == '':
        address_uber.components.street.name = None
    if address_uber.components.street.suffix == '':
        address_uber.components.street.suffix = None
    if address_uber.components.street.predir == '':
        address_uber.components.street.predir = None
    if address_uber.components.street.postdir == '':
        address_uber.components.street.postdir = None

    if address_uber.components.street_2.parse_method == '':
        address_uber.components.street_2.parse_method = None
    if address_uber.components.street_2.full == '':
        address_uber.components.street_2.full = None
    if address_uber.components.street_2.name == '':
        address_uber.components.street_2.name = None
    if address_uber.components.street_2.suffix == '':
        address_uber.components.street_2.suffix = None
    if address_uber.components.street_2.predir == '':
        address_uber.components.street_2.predir = None
    if address_uber.components.street_2.postdir == '':
        address_uber.components.street_2.postdir = None
    if address_uber.components.street_2.street_code == '':
        address_uber.components.street_2.street_code = None

    if address_uber.components.election.blockid == '':
        address_uber.components.election.blockid = None
    if address_uber.components.election.precinct == '':
        address_uber.components.election.precinct = None

    # since there aren't set values that are valid for these fields, long strings of junk valuse can come through
    # 6252 N. 4TH ST. 19120DFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFBBBBBBB B
    if address_uber.components.address_unit.unit_num != -1 and len(address_uber.components.address_unit.unit_num) > 12:
        address_uber.components.address_unit.unit_num = address_uber.components.address_unit.unit_num[:12]
    if len(address_uber.components.address_unit.unit_type) > 12:
        address_uber.components.address_unit.unit_num = address_uber.components.address_unit.unit_type[:12]

    if address_uber.components.address_unit.unit_num == '':
        address_uber.components.address_unit.unit_num = None
    if address_uber.components.address_unit.unit_num == -1:
        address_uber.components.address_unit.unit_num = None
    if address_uber.components.address_unit.unit_type == '':
        address_uber.components.address_unit.unit_type = None
    if address_uber.input_address == '':
        address_uber.input_address = None
    if address_uber.components.output_address == '':
        address_uber.components.output_address = None
    if address_uber.type == '':
        address_uber.type = None
    # Hack to set type back to landmark & assign geometry for non-addressed landmarks
    if landmark.is_landmark:
        address_uber.type = AddrType.landmark
        address.geometry = mapping(landmark.landmark_shape) if not landmark.landmark_address else address.geometry

    del address_uber.components.street.shape
    del address_uber.components.street_2.shape
    del landmark

    return address_uber


def input_cleanup(address_uber, item):
    # defensive, just in case you get some ridiculous input
    item = item[0:80]
    address_uber.input_address = item
    item = item.upper()

    # Make sure no junk ascii chars get through
    item = ILLEGAL_CHARS_RE.sub('', item)

    items = item.split('#')
    if len(items) > 2:
        item = "{} # {}".format(items[0], items[2])

    # get rid of trailing #  1608 South St #
    if len(items) == 2 and items[1] == '':
        item = items[0]

    item = item.replace(',', ' ')
    item = item.replace('.', ' ')
    item = item.replace('#', ' # ')
    item = item.replace('&', ' AND ')
    item = item.replace('/', ' AND ')
    item = item.replace('@', ' AND ')
    item = item.replace(' AT ', ' AND ')
    item = item.replace(' UNIT UNIT', ' UNIT ')  # yes this is common
    item = item.replace('1 AND 2', ' 1/2 ')
    item = item.replace(' - ', '-')
    item = item.replace(' -', '-')
    item = item.replace('- ', '-')

    # Remove ES, WS, NS, SS
    item = re.sub(' (NS|SS|ES|WS)$', '', item)

    item = item.replace(' OPP ', ' ')
    if item.startswith('OPP '):
        item = item[4:]

    if ' BLOCK ' in item or ' BLK ' in item:
        #  Parking data
        item = item.replace('UNIT BLK', '1 ')

        item = item.replace(' BLOCK OF ', ' ')
        item = item.replace(' BLOCK ', ' ')
        item = item.replace(' BLK OF ', ' ')
        item = item.replace(' BLK ', ' ')
        address_uber.type = AddrType.block

    item = ' '.join(item.split())

    return item


'''
RUN
'''

cwd = os.path.dirname(__file__)
cwd += '/pdata'
# Get config
# config_path = os.path.join(cwd, 'config.py')
# return_dict = True if CONFIG['return_dict'] else False


street_centerline_lookup, street_centerline_name_lookup, cl_name_lookup, cl_pre_lookup, \
cl_suffix_lookup = create_centerline_street_lookup()

# alias_centerline_lookup, alias_centerline_name_lookup, al_name_lookup, al_pre_lookup, \
# al_suffix_lookup = create_centerline_alias_lookup()

# if the user doesn't have the zip4 or centerline file, parser will still work
is_zip_file = create_zip4_lookup()
if not is_zip_file:
    warnings.warn('USPS file not found.')
is_cl_file = create_cl_lookup()
if not is_cl_file:
    warnings.warn('Centerline file not found.')
is_al_file = create_al_lookup()
if not is_al_file:
    warnings.warn('Alias file not found.')
is_election_file = create_election_lookup()
if not is_election_file:
    warnings.warn('Election file not found.')
is_int_file = create_int_lookup()
if not is_int_file:
    warnings.warn('Intersection file not found')

class PassyunkParser:
    def __init__(self, return_dict=True, MAX_RANGE=200):
        self.return_dict = return_dict
        self.MAX_RANGE = MAX_RANGE
        self.zip_file_loaded = True if is_zip_file else False
        self.cl_file_loaded =  True if is_cl_file else False
        self.election_file_loaded =  True if is_election_file else False

    def parse(self, addr_str):
        parsed_out = parse(addr_str, self.MAX_RANGE)

        if self.return_dict:
            # Hack to make nested addrnum a dict as well
            # parsed_out.components = parsed_out.components.__dict__
            parsed_out.components.mailing = parsed_out.components.mailing.__dict__
            parsed_out.components.election = parsed_out.components.election.__dict__
            parsed_out.components.address = parsed_out.components.address.__dict__
            parsed_out.components.street = parsed_out.components.street.__dict__
            parsed_out.components.street_2 = parsed_out.components.street_2.__dict__
            parsed_out.components.address_unit = parsed_out.components.address_unit.__dict__
            parsed_out.components = parsed_out.components.__dict__
            return parsed_out.__dict__

        return parsed_out

"""

Philadelphia Address Standardizer

Author: Tom Swanson

Created: 8/25/2014
Last Updated: 2/9/2016

Version: 1.0

"""

from __future__ import absolute_import

import csv
import sys
import os
import re

from .parser_data import STATELIST, CITYLIST, CARDINAL_DIR, PREPOSTDIR, POSTDIR, \
    PREDIR_AS_NAME, \
    SUFFIX_IN_NAME, zipcode_re, opa_account_re, zipcode_re, po_box_re, AddrType, \
    ILLEGAL_CHARS_RE

from passyunk.zip4 import create_zip4_lookup, is_zip4_base, get_zip_info
from passyunk.centerline import create_cl_lookup,get_cl_info


class Addrnum:
    def __init__(self):
        self.full = ''
        self.addrnum_type = ''
        self.low_num = -1
        self.high_num = -1
        self.high_num_full = -1
        self.low = ''
        self.high = ''
        self.parity = ''
        self.fractional = ''
        self.addr_suffix = ''
        self.isaddr = False


class Street:
    def __init__(self):
        self.full = ''
        self.predir = ''
        self.name = ''
        self.suffix = ''
        self.postdir = ''
        self.parse_method = ''
        self.is_centerline_match = False


class AddressUber:
    def __init__(self):
        self.components = Address()
        self.input_address = ''
        self.type = ''


class Address:
    def __init__(self):
        self.street_address = ''
        self.base_address = ''
        self.address = Addrnum()
        self.street = Street()
        self.street_2 = Street()
        self.unit = Unit()
        self.zipcode = ''
        self.zip4 = ''
        self.uspstype = ''
        self.bldgfirm = ''
        self.matchdesc = ''
        self.st_code = ''
        self.seg_id = ''
        self.responsibility = ''
        self.cl_addr_match = ''



class Unit:
    def __init__(self):
        self.unit_num = ''
        self.unit_type = ''


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


class Suffix:
    def __init__(self, row):
        # 0 - not a suffix
        # 1 - standard suffix abbr
        # 2 - long suffix
        # 3 - common abbr
        self.full = row[0]
        self.common = row[1]
        self.correct = row[2]

        self.std = '3'
        # self.notes = row[4]

        if self.common == self.full:
            self.std = '2'
        if self.common == self.correct:
            self.std = '1'


class Directional:
    def __init__(self, row):
        # 0 - not a dir
        # 1 - abbr dir N,E,S,W
        # 2 - long dir NORTH,EAST,SOUTH,WEST
        self.full = row[0]
        self.common = row[1]
        self.correct = row[2]
        self.std = '1'
        # self.notes = row[4]

        if self.common == self.full:
            self.std = '2'


class AddrOrdinal:
    def __init__(self, row):
        self.ordigit = row[0]
        self.orsuffix = row[1]


class Saint:
    def __init__(self, row):
        self.saintName = row[0]


class Namestd:
    def __init__(self, row):
        self.correct = row[0]
        self.common = row[1]


class Apt:
    def __init__(self, row):
        self.correct = row[0]
        self.common = row[1]


class AptStd:
    def __init__(self, row):
        self.common = row[0]
        self.correct = row[1]


class Apte:
    def __init__(self, row):
        self.correct = row[0]
        self.common = row[1]


'''
SETUP FUNCTIONS
'''


def csv_path(file_name):
    return os.path.join(cwd, file_name + '.csv')


def create_suffix_lookup():
    path = csv_path('suffix')
    f = open(path, 'r')
    lookup = {}
    try:
        reader = csv.reader(f)
        for row in reader:
            r = Suffix(row)
            lookup[r.common] = r
    except IOError:
        print('Error opening ' + path, sys.exc_info()[0])
    f.close()
    return lookup


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
        current = ''
        previousPreName = ''
        currentPreName = ''
        previousSuffix = ''
        currentSuffix = ''
        for row in reader:
            r = CenterlineName(row)
            if i == 0:
                rp = r
            current = r.name
            currentPreName = r.pre + ' ' + r.name
            currentSuffix = r.name + ' ' + r.suffix
            if current != previous and i != 0:
                ack = [previous, j, i]
                r2 = CenterlineNameOnly(ack)
                lookup_name[previous] = r2
                j = i
            if currentPreName != previousPreName and i != 0:
                ack = [previousPreName, jpre, i]
                r2 = CenterlineNameOnly(ack)
                if rp.pre != '':
                    lookup_pre[previousPreName] = r2
                jpre = i
            if currentSuffix != previousSuffix and i != 0:
                ack = [previousSuffix, jsuff, i]
                r2 = CenterlineNameOnly(ack)
                if rp.suffix != '':
                    lookup_suffix[previousSuffix] = r2
                jsuff = i
            lookup_list.append(r)
            lookup[r.full] = r
            rp = r
            previous = current
            previousPreName = currentPreName
            previousSuffix = currentSuffix
            i += 1

    except IOError:
        print('Error opening ' + path, sys.exc_info()[0])
    f.close()
    return lookup, lookup_list, lookup_name, lookup_pre, lookup_suffix


def createdirlookup():
    path = csv_path('directional')
    f = open(path, 'r')
    lookup = {}
    try:
        reader = csv.reader(f)
        for row in reader:
            r = Directional(row)
            lookup[r.common] = r
    except IOError:
        print('Error opening ' + path, sys.exc_info()[0])
    f.close()
    return lookup


def create_ordinal_lookup():
    lookup = {}
    r = AddrOrdinal(['1', 'ST'])
    lookup[r.ordigit] = r
    r = AddrOrdinal(['11', 'TH'])
    lookup[r.ordigit] = r
    r = AddrOrdinal(['2', 'ND'])
    lookup[r.ordigit] = r
    r = AddrOrdinal(['12', 'TH'])
    lookup[r.ordigit] = r
    r = AddrOrdinal(['3', 'RD'])
    lookup[r.ordigit] = r
    r = AddrOrdinal(['13', 'TH'])
    lookup[r.ordigit] = r
    r = AddrOrdinal(['4', 'TH'])
    lookup[r.ordigit] = r
    r = AddrOrdinal(['5', 'TH'])
    lookup[r.ordigit] = r
    r = AddrOrdinal(['6', 'TH'])
    lookup[r.ordigit] = r
    r = AddrOrdinal(['7', 'TH'])
    lookup[r.ordigit] = r
    r = AddrOrdinal(['8', 'TH'])
    lookup[r.ordigit] = r
    r = AddrOrdinal(['9', 'TH'])
    lookup[r.ordigit] = r
    r = AddrOrdinal(['0', 'TH'])
    lookup[r.ordigit] = r
    return lookup


def createsaintlookup():
    path = csv_path('saint')
    f = open(path, 'r')
    lookup = {}
    try:
        reader = csv.reader(f)
        for row in reader:
            r = Saint(row)
            lookup[r.saintName] = r
    except IOError:
        print('Error opening ' + path, sys.exc_info()[0])
    f.close()
    return lookup


def createnamestdlookup():
    path = csv_path('std')
    f = open(path, 'r')
    lookup = {}
    try:
        reader = csv.reader(f)
        for row in reader:
            r = Namestd(row)
            lookup[r.common] = r
    except IOError:
        print('Error opening ' + path, sys.exc_info()[0])
    f.close()
    return lookup


def createaptlookup():
    path = csv_path('apt')
    f = open(path, 'r')
    lookup = {}
    try:
        reader = csv.reader(f)
        for row in reader:
            r = Apt(row)
            lookup[r.common] = r
    except IOError:
        print('Error opening ' + path, sys.exc_info()[0])
    f.close()
    return lookup


def createaptstdlookup():
    path = csv_path('apt_std')
    f = open(path, 'r')
    lookup = {}
    try:
        reader = csv.reader(f)
        for row in reader:
            r = AptStd(row)
            lookup[r.common] = r
    except IOError:
        print('Error opening ' + path, sys.exc_info()[0])
    f.close()
    return lookup


def createaptelookup():
    path = csv_path('apte')
    f = open(path, 'r')
    lookup = {}
    try:
        reader = csv.reader(f)
        for row in reader:
            r = Apte(row)
            lookup[r.common] = r
    except IOError:
        print('Error opening ' + path, sys.exc_info()[0])
    f.close()
    return lookup


'''
TYPE TESTS
'''


def issuffix(test):
    # 0 - not a suffix
    # 1 - standard suffix abbr
    # 2 - long suffix
    # 3 - common abbr

    try:
        suf = suffix_lookup[test]
    except KeyError:
        row = [' ', test, ' ']
        suf = Suffix(row)
        suf.std = '0'
    return suf


def is_name_switch(test):
    try:
        name = name_switch_lookup[test]
    except KeyError:
        row = [' ', ' ', ' ', ' ', ' ']
        name = Nameswitch(row)
        name.name = '0'
    return name


def is_centerline_name(test):
    try:
        name = street_centerline_lookup[test]
    except KeyError:
        row = [' ', ' ', ' ', ' ', ' ']
        name = CenterlineName(row)
        name.full = '0'
    return name


def is_centerline_street_name(test):
    try:
        name = cl_name_lookup[test]
    except KeyError:
        row = [' ', 0, 0]
        return row
    return street_centerline_name_lookup[name.low:name.high]


def is_centerline_street_pre(test):
    try:
        name = cl_pre_lookup[test]
    except KeyError:
        row = [' ', 0, 0]
        return row
    return street_centerline_name_lookup[name.low:name.high]


def is_centerline_street_suffix(test):
    try:
        name = cl_suffix_lookup[test]
    except KeyError:
        row = [' ', 0, 0]
        return row
    return street_centerline_name_lookup[name.low:name.high]


def is_dir(test):
    # 0 - not a dir
    # 1 - abbr dir N,E,S,W
    # 2 - long dir NORTH,EAST,SOUTH,WEST

    try:
        d = dirLookup[test]
    except KeyError:
        row = [' ', test, ' ']
        d = Directional(row)
        d.std = '0'

    return d


def is_saint(test):
    ret = True
    try:
        saintLookup[test]
    except KeyError:
        ret = False

    return ret


def is_name_std(test):
    try:
        nstd = nameStdLookup[test]
    except KeyError:
        row = ['', test]
        nstd = Namestd(row)

    return nstd


def is_apt(test):
    try:
        apttemp = aptLookup[test]
    except KeyError:
        row = ['', test]
        apttemp = Apt(row)

    return apttemp


def is_apt_std(test):
    try:
        apttemp = aptStdLookup[test]
    except KeyError:
        return ''

    return apttemp.correct


def is_apte(test):
    try:
        aptetemp = apteLookup[test]
    except KeyError:
        row = ['', test]
        aptetemp = Apte(row)

    return aptetemp


# Standardize names
def name_std(tokens, do_ordinal):
    i = len(tokens)
    while i > 0:
        j = 0
        while j + i <= len(tokens):

            nstd = is_name_std(' '.join(tokens[j:j + i]))
            if nstd.correct != '':
                tokens[j] = nstd.correct
                k = j + 1
                while k < j + i:
                    tokens[k] = ''
                    k += 1
            j += 1
        i -= 1
    temp = " ".join(tokens).split()
    if do_ordinal and len(temp) > 0 and temp[0].isdigit():
        temp = add_ordinal(temp)
        temp = name_std(temp, True)
    return temp


def create_full_names(address, addr_type):
    if addr_type == AddrType.account or addr_type == AddrType.zipcode:
        return address

    temp = '%s %s %s %s' % (address.street.predir, address.street.name, address.street.suffix, address.street.postdir)
    address.street.full = ' '.join(temp.split())

    temp = '%s %s %s %s' % (
        address.street_2.predir, address.street_2.name, address.street_2.suffix, address.street_2.postdir)
    address.street_2.full = ' '.join(temp.split())

    if address.address.isaddr:
        # no Range
        if address.address.low_num >= 0 and address.address.high_num < 0:
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
            #     address.address.full = address.address.low + address.address.addr_suffix + '-' + temp + ' ' + address.address.fractional
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
            else:
                address.address.full = address.address.low + '-' + address.address.high
    # if you have an address number, use it even if it is and intersections
    if address.address.isaddr:
        address.base_address = address.address.full + ' ' + address.street.full
        addr_type == AddrType.address
    elif addr_type == AddrType.intersection_addr:
        address.base_address = address.street.full + ' & ' + address.street_2.full
    else:
        address.base_address = address.street.full

    return address


'''
TYPE HANDLERS
'''


def handle_st(tokens):
    i = 0
    while i < len(tokens) - 1:
        if tokens[i] == 'ST' and is_saint(tokens[i + 1]):
            tokens[i] = 'SAINT'
        elif tokens[i] == 'ST' and tokens[i + 1][len(tokens[i + 1]) - 1] == 'S':
            test = tokens[i + 1]
            testlen = len(test)
            if is_saint(test[0:testlen - 1]):
                tokens[i] = 'SAINT'
        i += 1
    return tokens


def handle_city_state_zip(tokens):
    zipcode = ''
    tlen = len(tokens)
    # check for a valid Philadelphia zipcode
    ziptest = tokens[tlen - 1]

    if zipcode_re.match(ziptest) is not None:
        ack = ziptest.split('-')
        # need to handle 5311 FLORENCE AVE UNIT 19112
        if ziptest.isdigit() and int(ziptest) > 19000 and int(ziptest) < 19300 and tokens[tlen - 2] != 'UNIT':
            zipcode = ack[0]
            tokens.remove(ziptest)
    tlen = len(tokens)
    if tlen == 0:
        return ''
    statetest = tokens[tlen - 1]

    #Just make sure that a UNIT of  # PA is not treated as a state.  1010 RACE ST # PA
    if tlen > 2 and statetest in STATELIST and tokens[tlen - 2] != '#' and tokens[tlen - 2] != 'APT' and tokens[tlen - 2] != 'UNIT':
        tokens.remove(statetest)
    tlen = len(tokens)
    citytest = tokens[tlen - 1]
    if tlen >= 2 and citytest in CITYLIST:
        tokens.remove(citytest)
    if len(tokens) >= 2 and tokens[len(tokens) - 1][0:5] == 'PA191':
        tokens.pop()
    return zipcode


def handle_units(tokens, unit):
    tlen = len(tokens)

    # this should simplify the original method and possibly eliminate some of the logic below

    if tlen > 3:

        if tokens[len(tokens) - 2] == '#':
            aptstd = is_apt_std(tokens[len(tokens) - 1])
            if aptstd == '1ST':
                aptstd = 'FL 1'
            if aptstd == '2ND':
                aptstd = 'FL 2'
            if aptstd == '3RD':
                aptstd = 'FL 3'

            if aptstd:
                aptstdsplit = aptstd.split()
                if len(aptstdsplit) == 1:
                    unit.unit_num = aptstd
                    token_is_apt = is_apt(aptstd)
                    if token_is_apt.correct != '':
                        unit.unit_type = token_is_apt.correct
                        unit.unit_num = -1

                else:
                    token_is_apt = is_apt(aptstdsplit[0])
                    if token_is_apt.correct != '':
                        unit.unit_type = aptstdsplit[0]
                        unit.unit_num = aptstdsplit[1]
                    else:
                        unit.unit_type = '#'
                        unit.unit_num = aptstd
            else:
                unit.unit_num = tokens[len(tokens) - 1]
                unit.unit_type = '#'
            tokens.pop()
            tokens.pop()
            return [-1, '']

        if tokens[len(tokens) - 3] == '#':
            apttest = tokens[len(tokens) - 2] + ' ' + tokens[len(tokens) - 1]
            aptstd = is_apt_std(apttest)

            if aptstd:
                aptstdsplit = aptstd.split()
                if len(aptstdsplit) == 1:
                    unit.unit_num = aptstd
                    token_is_apt = is_apt(aptstd)
                    if token_is_apt.correct != '':
                        unit.unit_type = token_is_apt.correct
                        unit.unit_num = -1

                else:
                    token_is_apt = is_apt(aptstdsplit[0])
                    if token_is_apt.correct != '':
                        unit.unit_type = aptstdsplit[0]
                        unit.unit_num = aptstdsplit[1]
                    else:
                        unit.unit_type = '#'
                        unit.unit_num = aptstd

            else:
                unit.unit_num = apttest
                unit.unit_type = '#'

            tokens.pop()
            tokens.pop()
            tokens.pop()
            return [-1, '']

        apt = is_apt(tokens[len(tokens) - 2])
        dig = tokens[len(tokens) - 1].isdigit()
        if dig and apt.correct != '':
            unit.unit_num = str(int(tokens[len(tokens) - 1]))  # get rid of leading zeros
            unit.unit_type = apt.correct
            tokens.pop()
            tokens.pop()
            return [-1, '']

        aptstd = is_apt_std(tokens[len(tokens) - 1])
        if aptstd and apt.correct != '':
            unit.unit_num = aptstd
            unit.unit_type = apt.correct
            tokens.pop()
            tokens.pop()
            return [-1, '']

        if apt.correct != '' and len(tokens[len(tokens) - 1]) <= 2:
            unit.unit_num = tokens[len(tokens) - 1]
            unit.unit_type = apt.correct
            tokens.pop()
            tokens.pop()
            return [-1, '']

        if tokens[len(tokens) - 2] == '#':
            unit.unit_num = tokens[len(tokens) - 1]
            unit.unit_type = '#'
            tokens.pop()
            tokens.pop()
            return [-1, '']

    tlen = len(tokens)
    if tlen > 3:

        # first try the last two tokens
        aptstd = is_apt_std(' '.join(tokens[-2:]))
        if aptstd:
            temp = aptstd.split()
            if len(temp) == 2:
                tokens[tlen - 2] = temp[0]
                tokens[tlen - 1] = temp[1]
            else:
                tokens[tlen - 2] = temp[0]
                tokens.pop()
                tlen = len(tokens)

    # now lets try the last token
    if tlen > 2:
        if tokens[len(tokens) - 2] == '#':
            unit.unit_num = tokens[len(tokens) - 1]
            unit.unit_type = '#'
            tokens.pop()
            tokens.pop()
            return [-1, '']

        aptstd = is_apt_std(' '.join(tokens[-1:]))
        # don't return in this case, just standardize the token
        if aptstd:
            temp = aptstd.split()
            if len(temp) == 1:
                tokens[tlen - 1] = aptstd
            else:
                tokens[tlen - 1] = temp[0]
                lst = [temp[1]]
                tokens.extend(lst)
                tlen = len(tokens)

    # 1600 N SR 50 60 - junk
    if len(tokens)>3 and tokens[len(tokens)-1].isdigit() and tokens[len(tokens)-1].isdigit():
        return [-1, '']

    # if you get to this point and there is a #, everything after is the unit
    # 1198 1/2 E UPSAL ST E # B C D
    # 1019 W SOMERSET ST # A and B
    i = 0
    for is_pound in tokens:
        if is_pound == '#':
            if i+1 == len(tokens):
                return [-1,'']
            return [i,' '.join(tokens[i+1:])]
        i += 1



    i = 0
    while i < tlen - 1:
        # TODO refactor and remove

        addrn = is_addr(tokens[i + 1], 2)
        apt = is_apt(tokens[i])

        if addrn.isaddr and apt.correct != '':
            if apt.correct != '':
                tokens[i] = apt.correct
            return [i, ' '.join(tokens[i:])]
        i += 1

    if tlen > 2:
        addrn = is_addr(tokens[tlen - 1], 2)
        apt = is_apt(tokens[tlen - 2])
        # tempDir1 = isDir(tokens[tlen-2],dirLookup)
        # tempsuffix1 = isSuffix(tokens[tlen-2],suffixLookup)

        if addrn.isaddr and apt.correct != '':
            return [tlen - 2, apt.correct + ' ' + addrn.low]
        elif addrn.isaddr and addrn.low not in CARDINAL_DIR:
            return [tlen - 1, addrn.low]

    if tlen > 2:
        apt = is_apte(tokens[tlen - 1])
        tempsuffix1 = issuffix(tokens[tlen - 2])

        if apt.correct != '' and tempsuffix1.std != '0':
            return [tlen - 1, apt.correct]

    return [-1, '']


def handle_mt(tokens):
    i = 0
    while i < len(tokens) - 1:
        if tokens[i] == 'MT':
            tokens[i] = 'MOUNT'
        i += 1
    return tokens


def is_ordinal(token):
    if token == add_ordinal(token):
        return False
    else:
        return True


def add_ordinal(string):
    if string == '0' or string == '00' or string == '000':
        return string

    if len(string[0]) > 1:
        lastchar = string[0][-2:]
        try:
            ordinal = add_ordinal_lookup[lastchar]
            if len(string) > 1 and ordinal.orsuffix == string[1]:
                string.pop()
            string[0] = string[0] + ordinal.orsuffix
            return string
        except Exception:
            pass

    lastchar = string[0][-1:]

    try:
        ordinal = add_ordinal_lookup[lastchar]
        string[0] = string[0] + ordinal.orsuffix
        return string
    except Exception:
        pass
    return string


def is_addr(test, ver):
    # type:
    # 0 = standard
    # 1 = unit designator (need to allow single Char)
    # break between alpha,num,_,-,/
    """

    """
    if test[0:2] != '0-':
        test = test.lstrip('0')
    half = False

    if len(test) > 2 and test[-3:] == '1/2':
        half = True
        test = test[:-3]
    if test == 'ONE':
        test = '1'

    tokens = re.findall(r"[^\W\d_-]+|\d+|-|#|/", test)
    tokenlen = len(tokens)
    if tokenlen > 1 and tokens[-1].isalnum() == False:
        tokens.pop()
        tokenlen = len(tokens)

    if len(tokens) == 3 and tokens[1] == '-' and tokens[2].isalpha():
        tokens[1] = tokens[2]
        tokens.pop()
        tokenlen = len(tokens)

    addr_ret = Addrnum()

    if half:
        addr_ret.fractional = '1/2'

    # 9367-75
    # 925R-35
    # Handle Address Ranges from DOR
    if ((tokenlen == 3 or tokenlen == 4) and tokens[0].isdigit() and tokens[tokenlen - 2] == '-' and len(
            tokens[tokenlen - 1]) <= 2 and tokens[tokenlen - 1].isdigit()):

        alowst = tokens[0][-2:]
        ahighst = tokens[tokenlen - 1][-2:]
        if int(alowst) % 2 == 0:
            alowoeb = 'E'
        else:
            alowoeb = 'O'

        ahighoeb = alowoeb

        # For ranges, us the odd even of the low number

        # if int(ahighst) % 2 == 0:
        #     ahighoeb = 'E'
        # else:
        #     ahighoeb = 'O'
        # if ahighoeb != alowoeb:
        #     ahighoeb = 'B'

        ilow = int(alowst)
        ihigh = int(ahighst)
        ihigh_full = ihigh

        if len(tokens[0]) > 2:

            hundred = (int(tokens[0][0:-2])) * 100
            ilow += hundred
            ihigh_full += hundred

        if len(tokens[0]) == 2 and len(tokens[2]) == 1:
            tens = (int(tokens[0][0:-1])) * 10
            ihigh_full += tens

        if ilow>ihigh_full:
            raise ValueError('Addr range, low > high')

        #it shouldn't be a range right?
        if ilow == ihigh_full:
            ihigh = -1
            ihigh_full = -1


        if tokenlen == 3:
            addr_ret.low_num = ilow
            addr_ret.high_num = ihigh
            addr_ret.high_num_full = ihigh_full
            addr_ret.low = str(ilow)
            addr_ret.high = str(ihigh)
            if len(addr_ret.high) == 1:
                addr_ret.high = '0' + addr_ret.high
            addr_ret.parity = ahighoeb
            if ihigh == -1:
                addr_ret.addrnum_type = 'NNNN-xx'
            else:
                addr_ret.addrnum_type = 'NNNN-NN'
            addr_ret.isaddr = True
        else:
            addr_ret.low_num = ilow
            addr_ret.high_num = ihigh
            addr_ret.high_num_full = ihigh_full
            addr_ret.addr_suffix = tokens[1]
            addr_ret.low = str(ilow) + tokens[1]
            addr_ret.high = str(ihigh)
            if len(addr_ret.high) == 1:
                addr_ret.high = '0' + addr_ret.high
            addr_ret.parity = ahighoeb
            addr_ret.addrnum_type = 'NNNNA-NN'
            addr_ret.isaddr = True

        return addr_ret

    # 2201 1/2-03
    # Handle Address Ranges from DOR
    if not (not (tokenlen == 6) or not tokens[0].isdigit() or not (tokens[1] == '1')) and \
                    tokens[2] == '/' and \
                    tokens[3] == '2' and \
                    tokens[4] == '-' and \
            tokens[5].isdigit():

        alowst = tokens[0][-2:]
        ahighst = tokens[5][-2:]
        if int(alowst) % 2 == 0:
            alowoeb = 'E'
        else:
            alowoeb = 'O'
        if int(ahighst) % 2 == 0:
            ahighoeb = 'E'
        else:
            ahighoeb = 'O'
        if ahighoeb != alowoeb:
            ahighoeb = 'B'
            # alowoeb = 'B'

        ilow = int(alowst)
        ihigh = int(ahighst)
        if ilow > ihigh:
            ahighoeb = 'U'
            # alowoeb = 'U'

        if len(tokens[0]) > 2:
            hundred = int(tokens[0][:-2]) * 100
            ilow += hundred
            ihigh += hundred

        addr_ret.low_num = ilow
        addr_ret.high_num = ihigh
        addr_ret.fractional = '1/2'
        addr_ret.low = str(ilow)
        addr_ret.high = str(ihigh)
        if len(addr_ret.high) == 1:
            addr_ret.high = '0' + addr_ret.high
        addr_ret.parity = ahighoeb
        addr_ret.isaddr = True
        addr_ret.addrnum_type = 'NNNN 1/2-NN'
        return addr_ret

    if tokenlen == 1 and tokens[0].isdigit():
        if int(tokens[0]) % 2 == 0:
            addr_ret.parity = 'E'
        else:
            addr_ret.parity = 'O'
        # if half:
        #     tokens.append(' 1/2')
        # and addess number of zero, return as true but blank it out
        if tokens[0] == '0' or tokens[0] == '00':
            addr_ret.low_num = -1
            addr_ret.high_num = -1
            addr_ret.parity = 'U'
            addr_ret.low = ''
            addr_ret.high = ''
            addr_ret.isaddr = True
        else:
            addr_ret.low_num = int(tokens[0])
            addr_ret.high_num = -1
            addr_ret.low = ''.join(tokens)
            addr_ret.high = ''
            addr_ret.low = addr_ret.low.lstrip('0')
            addr_ret.isaddr = True
        addr_ret.addrnum_type = 'N'
        return addr_ret

    # A
    if ver == 2 and tokenlen == 1 and len(tokens[0]) == 1 and tokens[0].isalpha():
        # if half:
        #     tokens.append(' 1/2')
        addr_ret.parity = 'U'
        addr_ret.low_num = 0
        addr_ret.high_num = 0
        addr_ret.low = ''.join(tokens)
        addr_ret.high = ''.join(tokens)
        addr_ret.isaddr = True
        addr_ret.addrnum_type = 'A'
        return addr_ret

    # NNAA
    if tokenlen == 2 and tokens[0].isdigit():
        # numeric street
        if tokens[1] == 'ST' or tokens[1] == 'ND' or tokens[1] == 'RD' or tokens[1] == 'TH':
            addr_ret.isaddr = False
        else:
            # if half:
            #     tokens.append(' 1/2')
            if int(tokens[0]) % 2 == 0:
                addr_ret.parity = 'E'
            else:
                addr_ret.parity = 'O'
            addr_ret.low_num = int(tokens[0])
            addr_ret.high_num = -1
            addr_ret.low = tokens[0] + tokens[1]
            addr_ret.high = ''
            addr_ret.addr_suffix = tokens[1]
            addr_ret.addrnum_type = 'NNAA'
            addr_ret.isaddr = True
    # AANN
    if tokenlen == 2 and tokens[1].isdigit():
        if int(tokens[1]) % 2 == 0:
            addr_ret.parity = 'E'
        else:
            addr_ret.parity = 'O'
        # if half:
        #     tokens.append(' 1/2')
        addr_ret.low_num = int(tokens[1])
        addr_ret.high_num = -1
        addr_ret.low = ''.join(tokens)
        addr_ret.high = ''
        addr_ret.addrnum_type = 'AANN'
        addr_ret.isaddr = True

    # NN-NN etc - We are going to assume that the user is referring to a philly ranged address and try to create that
    if tokenlen == 3 and tokens[0].isdigit() and tokens[1] == '-' and tokens[2].isdigit():
        #only if it looks like a good range
        if (len(tokens[0]) == len(tokens[2])) and len(tokens[0]) >= 3:
            ret = 'NN-NN to NNNN-NN'
            tmp_low = tokens[0]
            tmp_high = tokens[2]
            #reverse if low is > high
            if int(tokens[0]) > int(tokens[2]):
                if (int(tokens[2]) - int(tokens[0])) < 100:
                    tmp_low = tokens[2]
                    tmp_high = tokens[0]
                    ret = 'NN-NN to NNNN-RR'
                else:
                    raise ValueError('Bad Address Range: {}'.format(test))

            #Leave it alone
            if abs((int(tokens[0]) - int(tokens[2]))) > 100:
                addr_ret.low_num = int(tmp_low)
                addr_ret.high_num_full = int(tmp_high)
                addr_ret.low = tmp_low
                ihigh = int(tmp_high)
                addr_ret.high_num = ihigh
                addr_ret.high = str(ihigh)
                addr_ret.parity = 'B'
                addr_ret.isaddr = True
                addr_ret.full = test
                addr_ret.addrnum_type = 'BIG RANGE'
                return addr_ret

            addr_ret.low_num = int(tmp_low)
            addr_ret.high_num_full = int(tmp_high)
            addr_ret.low = tmp_low
            ihigh = int(tmp_high[-2:])
            addr_ret.high_num = ihigh
            addr_ret.high = str(ihigh)
            if len(addr_ret.high) == 1:
                addr_ret.high = '0'+addr_ret.high

            if addr_ret.low_num % 2 == 0:
                alowoeb = 'E'
            else:
                alowoeb = 'O'

            ahighoeb = alowoeb
            # if addr_ret.high_num_full % 2 == 0:
            #     ahighoeb = 'E'
            # else:
            #     ahighoeb = 'O'
            # if ahighoeb != alowoeb:
            #     ahighoeb = 'B'

            addr_ret.parity = ahighoeb

            #it should be a range if it is equal
            if tmp_low == tmp_high:
                ret = 'NN=NN'
                addr_ret.high_num_full = -1
                addr_ret.high_num = -1
                addr_ret.high = ''

            addr_ret.addrnum_type = ret
            addr_ret.isaddr = True
            return addr_ret

        #otherwise, leave as is
        else:
            addr_ret.low_num = int(tokens[0])
            addr_ret.high_num = int(tokens[2])
            if addr_ret.low_num>addr_ret.high_num:
                raise ValueError('Addr range, low > high')
            addr_ret.low = tokens[0]
            addr_ret.high = tokens[2]
            addr_ret.isaddr = True
            addr_ret.addrnum_type = 'NN-NN'
            return addr_ret
    # UU-NN
    if tokenlen > 2 and tokens[tokenlen - 2] == '-' and tokens[tokenlen - 1].isdigit():
        if int(tokens[tokenlen - 1]) % 2 == 0:
            addr_ret.parity = 'E'
        else:
            addr_ret.parity = 'O'
        # if half:
        #     tokens.append(' 1/2')
        addr_ret.low_num = int(tokens[tokenlen - 1])
        addr_ret.high_num = -1
        addr_ret.low = ''.join(tokens)
        addr_ret.high = ''
        addr_ret.addrnum_type = 'UU-NN'
        addr_ret.isaddr = True
    # NN-UU
    if tokenlen > 2 and tokens[tokenlen - 2] == '-' and tokens[tokenlen - 1].isalpha() and tokens[0].isdigit():
        if int(tokens[0]) % 2 == 0:
            addr_ret.parity = 'E'
        else:
            addr_ret.parity = 'O'
        # if half:
        #     tokens.append(' 1/2')
        addr_ret.low_num = int(tokens[0])
        addr_ret.high_num = -1
        addr_ret.low = ''.join(tokens)
        addr_ret.high = ''
        addr_ret.addrnum_type = 'NN-UU'
        addr_ret.isaddr = True

    # these next address number formats were written for valid USPS types but may not exist in Philadelphia
    # AANNAA
    if tokenlen == 3 and tokens[1].isdigit():
        if int(tokens[1]) % 2 == 0:
            addr_ret.parity = 'E'
        else:
            addr_ret.parity = 'O'
        # if half:
        #     tokens.append(' 1/2')
        addr_ret.low_num = int(tokens[1])
        addr_ret.high_num = -1
        addr_ret.low = ''.join(tokens)
        addr_ret.high = ''
        addr_ret.addrnum_type = 'AANNAA'
        addr_ret.isaddr = True
    # NNAANN - this is a bit unusual
    if tokenlen == 3 and tokens[0].isdigit() and tokens[2].isdigit():
        if int(tokens[2]) % 2 == 0:
            addr_ret.parity = 'E'
        else:
            addr_ret.parity = 'O'
        # if half:
        #     tokens.append(' 1/2')
        addr_ret.low_num = int(tokens[2])
        addr_ret.high_num = -1
        addr_ret.low = ''.join(tokens)
        addr_ret.high = ''
        addr_ret.addrnum_type = 'NNAANN'
        addr_ret.isaddr = True

    # AANNAANN
    if tokenlen == 4 and tokens[1].isdigit() and tokens[3].isdigit():
        if int(tokens[3]) % 2 == 0:
            addr_ret.parity = 'E'
        else:
            addr_ret.parity = 'O'
        # if half:
        #     tokens.append(' 1/2')
        addr_ret.low_num = int(tokens[3])
        addr_ret.high_num = -1
        addr_ret.low = ''.join(tokens)
        addr_ret.high = ''
        addr_ret.addrnum_type = 'AANNAANN'
        addr_ret.isaddr = True
    # NNAANNAA
    if tokenlen == 4 and tokens[0].isdigit() and tokens[2].isdigit():
        if int(tokens[2]) % 2 == 0:
            addr_ret.parity = 'E'
        else:
            addr_ret.parity = 'O'
        # if half:
        #     tokens.append(' 1/2')
        addr_ret.low_num = int(tokens[2])
        addr_ret.high_num = -1
        addr_ret.low = ''.join(tokens)
        addr_ret.high = ''
        addr_ret.addrnum_type = 'NNAANNAA'
        addr_ret.isaddr = True
    return addr_ret


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


def parse_po_box(input_addr):
    search = po_box_re.search(input_addr)
    num = search.group('num')
    return 'PO BOX {}'.format(num)


def parse(item):
    # address = Addr()
    address_uber = AddressUber()
    address = address_uber.components

    item = input_cleanup(address_uber, item)

    if item == '':
        address_uber.type = AddrType.none
        raise ValueError('Address not specified: {}'.format(item))
        #return address_uber

    # if you get a 9 digit numeric, treat it as an OPA account
    opa_account_search = opa_account_re.search(item)

    zipcode_search = zipcode_re.search(item)

    po_box_search = po_box_re.search(item)

    if len(item) == 9 and opa_account_search:
        address_uber.components.street_address = item
        address_uber.type = AddrType.account

    if len(item) == 5 and zipcode_search:
        if int(item)>=19100 and int(item)<=19199:
            address_uber.components.street_address = item
            address_uber.type = AddrType.zipcode
        else:
            raise ValueError('Invalid zipcode')

    elif ' AND ' in item and item[-8:] != ' A AND B' :
        tokens = item.split(' AND ')
        address = parse_addr_1(address, tokens[0])
        address2 = Address()
        address2 = parse_addr_1(address2, tokens[1])
        address.street_2 = address2.street
        address_uber.type = AddrType.intersection_addr

    elif po_box_search:
        search = po_box_re.search(item)
        num = search.group('num')
        address_uber.type = AddrType.pobox
        address.street.name = 'PO BOX {}'.format(num)

    else:
        if ' BLOCK ' in item or ' BLK ' in item:
            item = item.replace(' BLOCK OF ', ' ')
            item = item.replace(' BLOCK ', ' ')
            item = item.replace(' BLK OF ', ' ')
            item = item.replace(' BLK ', ' ')
            address_uber.type = AddrType.block

        address = parse_addr_1(address, item)
        if address.street.parse_method == 'UNK':
            address_uber.type = AddrType.none
            raise ValueError('Input does not match know address or place type: {}'.format(item))
        else:
            if address.address.isaddr:
                address_uber.type = AddrType.address
                if address.street.name == '':
                    raise ValueError('Parsed address does not have a street name: {}'.format(item))

            else:
                address_uber.type = AddrType.street

    name_switch(address)

    if address_uber.type == AddrType.address and address_uber.components.street.is_centerline_match == False:
        centerline_rematch(address.street)

    if address_uber.type == AddrType.intersection_addr:
        centerline_rematch(address.street)
        centerline_rematch(address.street_2)

    get_cl_info(address, address_uber.input_address)
    create_full_names(address, address_uber.type)

    if address_uber.type == AddrType.address:
        get_zip_info(address,address_uber.input_address)
        get_cl_info(address,address_uber.input_address)
        if address_uber.components.unit.unit_type == '' and address_uber.components.unit.unit_num != '':
            address_uber.components.unit.unit_type = '#'


    if address_uber.type == AddrType.intersection and address.base_address.find(' & ') == -1:
        address_uber.type = AddrType.address
    if address_uber.type == AddrType.intersection:
        address_uber.components.street_address = address.base_address
    elif address_uber.type != AddrType.account:
        if address.unit.unit_num != -1:
            address_uber.components.street_address = address.base_address + ' ' + \
                                                     address.unit.unit_type + ' ' + \
                                                     address.unit.unit_num
        else:
            address_uber.components.street_address = address.base_address + ' ' + \
                                                     address.unit.unit_type + ' '

        address_uber.components.street_address = ' '.join(address_uber.components.street_address.split())

    temp_centerline = is_centerline_name(address_uber.components.street.full)
    if temp_centerline.full != '0':
        address_uber.components.street.is_centerline_match = True
    # else:
    #     temp_centerline = is_centerline_street_name(address_uber.components.street.name)


    temp_centerline = is_centerline_name(address_uber.components.street_2.full)
    if temp_centerline.full != '0':
        address_uber.components.street_2.is_centerline_match = True


    if address_uber.components.base_address == '':
        address_uber.components.base_address = None
    if address_uber.components.zipcode == '':
        address_uber.components.zipcode = None
    if address_uber.components.zip4 == '':
        address_uber.components.zip4 = None

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

    if address_uber.components.unit.unit_num == '':
        address_uber.components.unit.unit_num = None
    if address_uber.components.unit.unit_num == -1:
        address_uber.components.unit.unit_num = None
    if address_uber.components.unit.unit_type == '':
        address_uber.components.unit.unit_type = None
    if address_uber.input_address == '':
        address_uber.input_address = None
    if address_uber.components.street_address == '':
        address_uber.components.street_address = None
    if address_uber.type == '':
        address_uber.type = None

    return address_uber


def input_cleanup(address_uber, item):
    # defensive, just in case you get some ridiculous input
    item = item[0:80]
    address_uber.input_address = item
    item = item.upper()

    # Make sure no junk ascii chars get through
    item = ILLEGAL_CHARS_RE.sub('', item)

    items = item.split('#')
    if len(items) >2:
        item = "{} # {}".format(items[0], items[2])

    #get rid of trailing #  1608 South St #
    if len(items) == 2 and items[1] == '':
        item = items[0]

    item = item.replace(',', ' ')
    item = item.replace('.', ' ')
    item = item.replace('#', ' # ')
    item = item.replace('&', ' AND ')
    item = item.replace('/', ' AND ')
    item = item.replace('@', ' AND ')
    item = item.replace(' AT ', ' AND ')
    item = item.replace('1 AND 2', ' 1/2 ')
    item = ' '.join(item.split())
    return item


def name_switch(address):
    ack = '%s %s %s %s' % (address.street.predir, address.street.name, address.street.suffix, address.street.postdir)
    ack = ' '.join(ack.split(' ')).strip()
    nameswitch = is_name_switch(ack)
    if nameswitch.name != '0':
        address.street.predir = nameswitch.pre
        address.street.name = nameswitch.name
        address.street.suffix = nameswitch.suffix
        address.street.postdir = nameswitch.post


def parse_addr_1(address, item):
    tokens = item.split()

    # This is just for speed, check for clean address match, handle, and return
    if len(tokens) > 1 and tokens[0].isdigit():
        centerline_name = is_centerline_name(' '.join(tokens[1:]))
        #        centerline_street_name = is_centerline_street_name(' '.join(tokens[1:2]))
        if centerline_name.full != '0':
            address.street.predir = centerline_name.pre
            address.street.name = centerline_name.name
            address.street.suffix = centerline_name.suffix
            address.street.postdir = centerline_name.post

            address.address.addrnum_type = 'N'
            address.address.low_num = int(tokens[0])

            if address.address.low_num % 2 == 0:
                address.address.parity = 'E'
            else:
                address.address.parity = 'O'

            # address.address.high_num = int(tokens[0])
            address.address.low = str(int(tokens[0]))
            # address.address.high = str(int(tokens[0]))
            address.address.isaddr = True
            address.street.parse_method = 'CL1'
            return address

    # total hack but 'K' will be recognized as an apt otherwise when there is no suffix
    if item.find('J F K') >= 0 or item.find('JF K') >= 0 or item.find('M L K') >= 0:
        tokens = name_std(tokens, False)

    token_len = len(tokens)
    addrn = is_addr(tokens[0], 0)
    if token_len > 1 and addrn.isaddr and len(tokens[1]) >= 3 and tokens[1][1] == '/':
        # there are 6 OPA addresses with the format 4080 1/2-82 LANCASTER AVE
        if token_len > 3 and tokens[1] == '1/2' and tokens[2][0] == '-':
            addrn = is_addr(tokens[0] + '-' + tokens[2][1:] + ' 1/2', 0)
            tokens = tokens[3:token_len]
        else:
            addrn = is_addr(tokens[0] + ' ' + tokens[1], 0)
            tokens = tokens[2:token_len]

    elif addrn.isaddr and token_len > 1:
        address.address = addrn
        tokens = tokens[1:]

    token_len = len(tokens)

    if token_len == 3 and tokens[0] == 'RACE' and (tokens[2] == 'PA' or tokens[2] == 'PK'):
        address.unit.unit_num = tokens[2]
        tokens.pop()
        token_len = 2

    if token_len == 0:
        address.street.name = item
        address.street.parse_method = 'UNK'
        return address

    address.zipcode = handle_city_state_zip(tokens)
    token_len = len(tokens)
    if token_len == 0:
        address.street.name = item
        address.street.parse_method = 'UNK'
        return address
    address.unit.unit_type = ''
    units = handle_units(tokens, address.unit)

    if units[0] != -1 and address.unit.unit_type == '':
        tokens = unitdesigantor_second_pass(address, units, tokens)


    #  Fix for addresses like this - 90 E JOHNSON ST # 2ND FL R #32
    # 1608 South St # <- should be handled in cleanup
    i = 0
    for t in tokens:
        i+=1
        if t == '#':
            tokens = tokens[:i-1]

    if len(tokens) == 0:
        return address

    # dash char might slip through, get rid of it
    if tokens[len(tokens) - 1] == '-':
        tokens.pop()
    token_len = len(tokens)
    if token_len == 0:
        address.street.name = item
        address.street.parse_method = 'UNK'
        return address

    if token_len == 1:
        address.street.name = ' '.join(name_std(tokens, False))
        address.street.parse_method = 'A1'
        return address

    tokens = handle_st(tokens)
    tokens = handle_mt(tokens)

    if token_len == 2:
        suffix_end = issuffix(tokens[-1])

        # 1234 10TH ST
        if suffix_end.std != '0':
            if '{} {}'.format(' '.join(tokens[0:1]), suffix_end.correct) in SUFFIX_IN_NAME:
                address.street.predir = ''
                address.street.name = ' '.join(name_std(tokens, True))
                address.street.parse_method = '2ANN suff_name'
                return address
            else:
                address.address = addrn
                address.street.predir = ''
                address.street.name = ' '.join(name_std(tokens[:-1], True))
                address.street.suffix = suffix_end.correct
                address.street.postdir = ''
                address.street.parse_method = '2ANS'
                return address
        # 1234 N 10TH
        # 1234 WEST END
        pre_dir = is_dir(tokens[0])
        if pre_dir.std != '0':
            address.address = addrn
            address.street.suffix = ''
            address.street.postdir = ''

            if '{} {}'.format(pre_dir.full, ' '.join(tokens[1:])) in PREDIR_AS_NAME:
                address.street.predir = ''
                address.street.name = ' '.join(name_std(tokens, True))
                address.street.parse_method = '2ANN predir'
                return address
            else:
                address.street.predir = pre_dir.correct
                address.street.name = ' '.join(name_std(tokens[1:], True))
                address.street.parse_method = '2ADN'
            # address.unit.unit_type = ''

            return address
        # 1234 CENTENNIAL E - only way this is possible is that the suffix was left off
        if pre_dir.std != '0':
            address.address = addrn
            address.street.predir = ''
            address.street.name = ' '.join(name_std(tokens, True))
            address.street.suffix = ''
            address.street.postdir = ''
            # address.unit.unit_type = ''
            address.street.parse_method = '2ANN junk postdir'
            return address

        else:
            address.address = addrn
            address.street.predir = ''
            address.street.name = ' '.join(name_std(tokens, True))
            address.street.suffix = ''
            address.street.postdir = ''
            # address.unit.unit_type = ''
            address.street.parse_method = '2ANN'
            return address

    if token_len == 3:
        pre_dir = is_dir(tokens[0])
        post_dir = is_dir(tokens[2])
        suffix_minus_one = issuffix(tokens[2])
        suffix_end = issuffix(tokens[1])

        # 1234 N 10TH ST
        if suffix_minus_one.std != '0' and pre_dir.std != '0':
            address.address = addrn
            # WEST END
            if '{} {}'.format(pre_dir.full, tokens[1]) in PREDIR_AS_NAME:
                address.street.predir = ''
                address.street.name = ' '.join(name_std(tokens[0:-1], True))
                address.street.suffix = suffix_minus_one.correct
                address.street.postdir = ''
                address.street.parse_method = '3NNS predir'
            # N Centennial SQ -> Centennial SQ N
            elif '{} {}'.format(tokens[1], suffix_minus_one.correct) in POSTDIR:
                address.street.predir = ''
                address.street.name = ' '.join(name_std(tokens[1:-1], True))
                address.street.suffix = suffix_minus_one.correct
                address.street.postdir = pre_dir.correct
                address.street.parse_method = '3NSD switch'
            # S Fair hill
            elif '{} {}'.format(tokens[1], suffix_minus_one.correct) in SUFFIX_IN_NAME:
                address.street.predir = pre_dir.correct
                address.street.name = ' '.join(name_std(tokens[1:3], True))
                address.street.suffix = ''
                address.street.postdir = ''
                address.street.parse_method = '3DNN suff'
            else:
                address.street.predir = pre_dir.correct
                address.street.name = ' '.join(name_std(tokens[1:-1], True))
                address.street.suffix = suffix_minus_one.correct
                address.street.postdir = ''
                address.street.parse_method = '3ADNS'
            return address

        # 1234 N 10TH ST
        if suffix_minus_one.std != '0' and pre_dir.std != '0':
            address.address = addrn
            address.street.predir = pre_dir.correct
            address.street.name = ' '.join(name_std(tokens[1:-1], True))
            address.street.suffix = suffix_minus_one.correct
            address.street.postdir = ''
            address.street.parse_method = '3ADNS'
            return address

        # 1234 10TH ST N - rare
        if post_dir.std != '0' and suffix_end.std != '0':
            address.address = addrn
            address.street.predir = ''
            temp = '{} {}'.format(' '.join(name_std(tokens[:-2], True)), suffix_end.correct)
            address.street.suffix = suffix_end.correct
            if temp in POSTDIR:
                address.street.postdir = post_dir.correct
                address.street.name = ' '.join(name_std(tokens[:-2], True))
                address.street.parse_method = '3ANSD'
            else:
                ack = post_dir.correct + ' ' + ' '.join(name_std(tokens[:-2], True))
                temp = is_centerline_name(ack)
                if temp.full != '0':
                    address.street.postdir = ''
                    address.street.predir = post_dir.correct
                    address.street.name = ' '.join(name_std(tokens[:-2], True))
                    address.street.parse_method = '3ADNS dirswitch'

                # postdir is a unit
                ack = ' '.join(name_std(tokens[:-2], True))
                temp = is_centerline_name(ack)
                if temp.full and address.unit.unit_num != '':
                    address.street.postdir = ''
                    address.street.predir = ''
                    address.street.name = ' '.join(name_std(tokens[:-2], True))
                    address.street.parse_method = '3ANS removepostdir'
                else:
                    address.street.postdir = post_dir.correct
                    address.street.predir = ''
                    address.street.name = ' '.join(name_std(tokens[:-2], True))
                    address.street.parse_method = '3ANS unknownpostdirorunit'

            return address

        # 1234 FLAT ROCK RD
        if suffix_minus_one.std != '0' and pre_dir.std == '0':
            address.address = addrn
            address.street.predir = ''
            address.street.name = ' '.join(name_std(tokens[:-1], True))
            address.street.suffix = suffix_minus_one.correct
            address.street.postdir = ''
            address.street.parse_method = '3ANNS'
            return address

    if token_len == 4:
        pre_dir = is_dir(tokens[0])
        post_dir = is_dir(tokens[3])
        suffix_minus_one = issuffix(tokens[2])
        suffix_end = issuffix(tokens[3])
        suffix_plus_one = issuffix(tokens[1])

        # W s independence mall W
        if pre_dir.std != '0' and post_dir.std != '0' and suffix_minus_one.std != '0' and ' '.join(
                name_std(tokens[1:-1], True)) in PREPOSTDIR:
            address.address = addrn
            address.street.predir = pre_dir.correct
            address.street.name = ' '.join(name_std(tokens[1:2], True))
            address.street.suffix = suffix_minus_one.correct
            address.street.postdir = post_dir.correct
            address.street.parse_method = '4ADsS'
            return address
        # W Chestnut Hill Ave
        if pre_dir.std != '0' and suffix_end.std != '0' and suffix_minus_one.std != '0':
            address.address = addrn
            address.street.predir = pre_dir.correct
            address.street.name = ' '.join(name_std(tokens[1:-1], True))
            address.street.suffix = suffix_end.correct
            address.street.postdir = ''
            address.street.parse_method = '4ADsS'
            return address

        if pre_dir.std != '0':
            if suffix_end.std != '0':
                tempdir3 = is_dir(tokens[2])
                # the pre or postdir got jammed in in front of the suffix happens for PREPOSTDIR
                if tempdir3.std == '1':
                    test = '{} {}'.format(' '.join(name_std(tokens[1:-2], True)), suffix_end.correct)
                    if test in PREPOSTDIR:
                        address.street.postdir = tempdir3.correct
                    address.street.name = ' '.join(name_std(tokens[1:-2], True))
                else:
                    address.street.name = ' '.join(name_std(tokens[1:3], True))
                    address.street.postdir = ''

                address.address = addrn
                address.street.predir = pre_dir.correct
                address.street.suffix = suffix_end.correct
                address.street.parse_method = '4ADNNS'
                return address

                # Pattern addrnum name suffix dir
        if post_dir.std != '0' and suffix_end.std != '0':
            address.address = addrn
            address.street.predir = ''
            address.street.name = ' '.join(name_std(tokens[:-2], True))
            address.street.suffix = suffix_end.correct
            address.street.postdir = post_dir.correct
            address.street.parse_method = '4ANNSD'
            return address

        # Possible unit number that didn't get caught
        if pre_dir.std != '0' and suffix_minus_one.std != '0' and suffix_end.std == '0':
            address.address = addrn
            address.street.predir = pre_dir.correct
            address.street.name = ' '.join(name_std(tokens[1:2], True))
            address.street.suffix = suffix_minus_one.correct
            apt_std = is_apt_std(tokens[token_len - 1])
            # Might need to handle the postdir streets here
            if post_dir.std != 0 and len(post_dir.common) == 1 and address.unit.unit_num == '':
                if post_dir.full == pre_dir.full:
                    address.unit.unit_num = ''
                    address.unit.unit_type = ''
                    address.street.postdir = ''
                    address.street.parse_method = '4ADNSdupDir'
                else:
                    address.unit.unit_num = post_dir.correct
                    address.unit.unit_type = '#'
                    address.street.postdir = ''
                    address.street.parse_method = '4ADNSdirUnit'
            elif apt_std:
                address.street.postdir = ''
                address.street.parse_method = '4ADNSUnit'
                address.unit.unit_num = apt_std
                address.unit.unit_type = '#'
            else:
                # 121 S INDPNC MALL E # 218
                if address.street.name == 'INDENPENDENCE':
                    address.street.postdir = post_dir.correct

                else:
                    address.street.postdir = ''
                address.street.parse_method = '4ADNSJ'
            return address

        if pre_dir.std != '0' and suffix_minus_one.std == '0' and post_dir.std == '0' and suffix_end.std == '0':
            address.address = addrn
            address.street.predir = pre_dir.correct
            address.street.name = ' '.join(name_std(tokens[1:4], True))
            address.street.suffix = ''
            address.street.postdir = ''
            address.street.parse_method = '4DNNN'
            return address

        if pre_dir.std == '0' and suffix_minus_one.std != '0' and suffix_end.std == '0' and address.unit.unit_num == '':
            address.address = addrn
            address.street.predir = ''
            address.street.name = ' '.join(name_std(tokens[0:2], True))
            address.street.suffix = suffix_minus_one.correct
            address.street.postdir = ''
            address.unit.unit_type = is_apt_std(tokens[token_len - 1])
            address.street.parse_method = '4NNSU'
            return address

        if pre_dir.std == '0' and suffix_end.std != '0':
            address.address = addrn
            address.street.predir = ''
            address.street.name = ' '.join(name_std(tokens[0:3], True))
            address.street.suffix = suffix_end.correct
            address.street.postdir = ''
            address.street.parse_method = '4NNNS'
            return address

        # 2 junk tokens - 1234 Market St junk junk
        if suffix_plus_one.std != '0' and \
                        pre_dir.std == '0' and \
                        post_dir.std == '0' and \
                        suffix_minus_one.std == '0' and \
                        suffix_end.std == '0':
            address.address = addrn
            address.street.predir = ''
            address.street.name = ' '.join(name_std(tokens[0:1], True))
            address.street.suffix = suffix_plus_one.correct
            address.street.postdir = ''
            address.street.parse_method = '4NSJJ'
            return address

    if 5 <= len(tokens) < 7:
        pre_dir = is_dir(tokens[0])
        post_dir = is_dir(tokens[token_len - 1])
        suffix_minus_one = issuffix(tokens[token_len - 2])
        suffix_end = issuffix(tokens[token_len - 1])

        # Streets with 3 or more words/tokens
        # AVENUE OF THE REPUBLIC - no suffix
        # CECIL B MOORE AVE
        # G F CONGDON DR - private
        # JOHN F KENNEDY BLVD
        # MARTIN LUTHER KING DR - need to standardize between Jr or not
        # SAINT JOHN NEUMANN PL
        # SAINT JOHN NEUMANN WAY

        # This is a difficult - Is the post dir a pre dir or an apt?
        # No 3 token streets have post dir or a pre dir so it needs to be apt
        if pre_dir.std == '0' and post_dir.std != '0' and suffix_end.std != '0':
            address.address = addrn
            address.street.predir = ''
            address.street.name = ' '.join(name_std(tokens[0:3], True))
            address.street.suffix = suffix_end.correct
            address.street.postdir = ''
            address.unit.unit_num = post_dir.common
            address.street.parse_method = '5ANNNSD?'
            return address

        # PreDir and a suffix at the end.  This shouldn't exist however
        # Exception 7 N CHRIS COLUMBUS BLVD PARK
        if pre_dir.std != '0' and suffix_end.std != '0':
            address.address = addrn
            address.street.predir = pre_dir.correct
            # special case OPS address 7 N CHRIS COLUMBUS BLVD PARK
            if tokens[token_len - 1] == 'PARK':
                address.unit.unit_type == 'PARK'
                address.street.name = ' '.join(name_std(tokens[1:-2], True))
                address.street.suffix = suffix_minus_one.correct
            else:
                address.street.name = ' '.join(name_std(tokens[1:-1], True))
                address.street.suffix = suffix_end.correct

            address.street.postdir = ''
            address.street.parse_method = '5ADNNNS'
            return address

        if pre_dir.std == '0' and suffix_minus_one.std == '0' and suffix_end.std != '0':
            address.address = addrn
            address.street.predir = ''
            address.street.name = ' '.join(name_std(tokens[0:4], True))
            if address.street.name != 'AVENUE OF THE REPUBLIC':
                address.street.suffix = suffix_end.correct
            address.street.postdir = ''
            address.unit.unit_type = is_apt_std(tokens[token_len - 1])

            address.street.parse_method = '5NNNSU'
            return address

        # There are no streets like this with post dir, must be a unit
        if pre_dir.std == '0' and suffix_minus_one.std != '0' and post_dir.std != '0':
            address.address = addrn
            address.street.predir = ''
            address.street.name = ' '.join(name_std(tokens[:-2], True))
            address.street.suffix = suffix_minus_one.correct
            address.street.postdir = ''
            address.unit.unit_num = post_dir.correct
            address.unit.unit_type = '#'
            address.street.parse_method = '5ANNNNSD'
            return address

        if pre_dir.std == '0' and suffix_minus_one.std != '0':
            address.address = addrn
            address.street.predir = ''
            address.street.name = ' '.join(name_std(tokens[:-2], True))
            if address.street.name != 'AVENUE OF THE REPUBLIC':
                address.street.suffix = ''
            else:
                address.street.suffix = suffix_minus_one.correct
            address.street.postdir = ''
            address.street.parse_method = '5ANNNNS'
            return address

    if token_len == 3:
        pre_dir = is_dir(tokens[0])
        post_dir = is_dir(tokens[2])
        suffix_minus_one = issuffix(tokens[1])
        suffix_end = issuffix(tokens[2])

        # Last token is junk or apt
        if pre_dir.std == '0' and suffix_minus_one.std != '0' and post_dir.std == '0' and suffix_end.std == '0':
            address.address = addrn
            address.street.predir = ''
            address.street.name = ' '.join(name_std(tokens[0:1], True))
            address.street.suffix = suffix_minus_one.correct
            address.street.postdir = ''
            apt_std = is_apt_std(tokens[token_len - 1])
            if apt_std:
                address.unit.unit_num = apt_std
                address.unit.unit_type = '#'
                address.street.parse_method = '3bNSU'
            else:
                address.street.parse_method = '3bNSJ'
            return address

        # predir name name suffix
        if pre_dir.std == '0' and suffix_minus_one.std == '0' and post_dir.std == '0' and suffix_end.std == '0':
            address.address = addrn
            address.street.predir = ''
            address.street.name = ' '.join(name_std(tokens[0:3], True))
            address.street.suffix = ''
            address.street.postdir = ''
            address.street.parse_method = '3bNNN'
            return address

        if pre_dir.std != '0' and suffix_minus_one.std == '0' and post_dir.std == '0' and suffix_end.std == '0':
            address.address = addrn
            address.street.predir = pre_dir.correct
            address.street.name = ' '.join(name_std(tokens[1:3], True))
            address.street.suffix = ''
            address.street.postdir = ''
            address.street.parse_method = '3bDNN'
            return address

    # There's junk
    if token_len > 4:
        pre_dir = is_dir(tokens[0])
        suffix_minus_one = issuffix(tokens[len(tokens) - 2])
        suffix_end = issuffix(tokens[len(tokens) - 1])

        # predir name suffix junk
        if pre_dir.std != '0' and suffix_minus_one.std == '1':
            address.address = addrn
            address.street.predir = pre_dir.correct
            address.street.name = ' '.join(name_std(tokens[1:3], True))
            address.street.suffix = suffix_minus_one.correct
            address.street.postdir = ''
            address.street.parse_method = '5ADNSx'
            return address

            # predir name name suffix
        if pre_dir.std != '0' and suffix_end.std != '0':
            address.address = addrn
            address.street.predir = pre_dir.correct
            address.street.name = ' '.join(name_std(tokens[1:3], True))
            address.street.suffix = suffix_end.correct
            address.street.postdir = ''
            address.street.parse_method = '5APNNSx'
            return address

    #raise error at this point
    address.street.parse_method = 'TODO'
    address.street.name = ' '.join(name_std(tokens, True))
    return address


def unitdesigantor_second_pass(address, apt, tokens):
    address.unit.unit_type = apt[1]
    tokens = tokens[0:apt[0]]
    aptsplit = address.unit.unit_type.split(' ')
    if len(aptsplit) == 1:
        apte = is_apte(aptsplit[0])
        if apte.correct != '':
            address.unit.unit_num = ''
            address.unit.unit_type = aptsplit[0]
        else:
            address.unit.unit_num = address.unit.unit_type
            address.unit.unit_type = '#'
    else:
        apt = is_apt(aptsplit[0])
        apt2 = is_apt(aptsplit[1])
        if apt.correct != '':
            address.unit.unit_type = aptsplit[0]
            address.unit.unit_num = aptsplit[1]
        elif apt2.correct != '':
            address.unit.unit_type = aptsplit[1]
            address.unit.unit_num = aptsplit[0]
        else:
            address.unit.unit_type = ''
            address.unit.unit_num = ' '.join(aptsplit)
    return tokens


'''
RUN
'''

cwd = os.path.dirname(__file__)
cwd += '/pdata'
# Get config
# config_path = os.path.join(cwd, 'config.py')
# return_dict = True if CONFIG['return_dict'] else False

suffix_lookup = create_suffix_lookup()
dirLookup = createdirlookup()
saintLookup = createsaintlookup()
nameStdLookup = createnamestdlookup()
aptLookup = createaptlookup()
apteLookup = createaptelookup()
aptStdLookup = createaptstdlookup()
add_ordinal_lookup = create_ordinal_lookup()
name_switch_lookup = create_name_switch_lookup()
street_centerline_lookup, street_centerline_name_lookup, cl_name_lookup, cl_pre_lookup, cl_suffix_lookup = create_centerline_street_lookup()
create_zip4_lookup()
create_cl_lookup()


class PassyunkParser:
    def __init__(self, return_dict=True):
        self.return_dict = return_dict

    def parse(self, addr_str):
        parsed_out = parse(addr_str)

        if self.return_dict:
            # Hack to make nested addrnum a dict as well
            # parsed_out.components = parsed_out.components.__dict__
            parsed_out.components.address = parsed_out.components.address.__dict__
            parsed_out.components.street = parsed_out.components.street.__dict__
            parsed_out.components.street_2 = parsed_out.components.street_2.__dict__
            parsed_out.components.unit = parsed_out.components.unit.__dict__
            parsed_out.components = parsed_out.components.__dict__
            return parsed_out.__dict__

        return parsed_out


# TEST
if __name__ == '__main__':
    parser = PassyunkParser()
    #137 W SUSQUEHANNA AVE # 2ND FRONT

    parsed = parser.parse('1842 STRAHLE ST')
    # print(parsed)

    import json

    print(json.dumps(parsed, sort_keys=True, indent=2))

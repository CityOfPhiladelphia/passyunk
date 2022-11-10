from __future__ import print_function

import csv
import os
import sys

__author__ = 'tom.swanson'

cwd = os.path.dirname(__file__)
cwd += '/pdata'
# use the cleanded up file
blocksfile = 'election_block'


def csv_path(file_name):
    return os.path.join(cwd, file_name + '.csv').replace('\\', '/')


election_basename = {}
election_list = []
election_name = {}


class Blocks:
    def __init__(self, row):
        self.base = row[0]
        self.pre = row[1]
        self.name = row[2]
        self.suffix = row[3]
        self.post = row[4]
        self.low = int(row[5]) if len(row[5].strip()) > 0 else 0
        self.high = int(row[6]) if len(row[5].strip()) > 0 else 0
        self.oeb = row[7]
        self.blockid = row[8]
        self.usage = row[9]
        self.status = row[10]
        self.precinct = row[11]
        self.votercount = row[12]
        self.segid = row[13]
        self.zipcode = row[14]
        self.uspszip = row[15]
        self.standardized = row[16]


class NameOnly:
    def __init__(self, row):
        self.name = row[0]
        self.low = row[1]
        self.high = row[2]


def test_election_file():
    path = csv_path(blocksfile)
    print(f'Checking csv existence at: {path}..')
    return os.path.isfile(path)


def create_election_lookup():
    if not test_election_file():
        print('election csv file doesnt exist.')
        return False

    path = csv_path(blocksfile)
    f = open(path, 'r')
    i = 0
    j = 0
    jbase = 0
    p_name = ''
    p_base = ''
    try:
        reader = csv.reader(f)

        for row in reader:
            if i == 0:
                i += 1
                continue
            r = Blocks(row)
            c_name = r.name
            c_base = r.base

            if c_name != p_name and i != 0:
                ack = [p_name, j - 1, i - 1]
                r2 = NameOnly(ack)
                election_name[p_name] = r2
                j = i

            if c_base != p_base and i != 0:
                ack = [p_base, jbase - 1, i - 1]
                r2 = NameOnly(ack)
                election_basename[p_base] = r2
                jbase = i

            election_list.append(r)
            p_name = c_name
            p_base = c_base
            i += 1

    except IOError:
        print('Error opening ' + path, sys.exc_info()[0])
    ack = [p_base, jbase - 1, i - 1]
    r2 = NameOnly(ack)
    election_basename[p_base] = r2

    # validate_zip4_basename()

    f.close()
    return True


def validate_election_basename():
    for r in election_basename:
        row = election_basename[r]
        row_list = election_list[row.low:row.high]
        name = {}
        for st in row_list:
            name[st.base] = st.base
        if len(name) > 1:
            for ack in name:
                print(ack)


def is_election_base(test):
    try:
        name = election_basename[test]
    except KeyError:
        row = []
        # row.append([' ', 0, 0])
        return row
    return election_list[name.low:name.high]


def is_election_name(test):
    try:
        name = election_name[test]
    except KeyError:
        row = []
        # row.append([' ', 0, 0])
        return row
    return election_list[name.low:name.high]


def get_unique_zipcodes(lst):
    tmp = {}
    zips = []
    for row in lst:
        tmp[row.zipcode] = row.zipcode
    # seems easier to just return a list than to deal with a dict - zips.values()[0]
    for r in tmp:
        zips.append(r)
    return zips


def get_election_info(address):
    elist = is_election_base(address.street.full)

    if len(elist) > 0:
        mlist = []
        for row in elist:
            # Some blocks in election_blocks.csv don't have address ranges (253 PORT ROYAL)
            try:
                if row.low <= address.address.low_num <= row.high and (
                                address.address.parity == row.oeb or row.oeb == 'B'):
                    mlist.append(row)
            except TypeError:
                pass
        if len(mlist) == 0:
            address.blockid = ''
            address.precinct = ''
        if len(mlist) == 1:
            address.election.blockid = mlist[0].blockid
            address.election.precinct = mlist[0].precinct
            return

        elif len(mlist) >=2:
            unique_precinct = get_unique_precincts(mlist)
            if len(unique_precinct) == 1:
                address.election.precinct = mlist[0].precinct
            else:
                address.precinct = 'MULTIPLE'

        else:
            address.precinct = ''
            return

def get_unique_precincts(lst):
    tmp = {}
    precinct = []
    for row in lst:
        tmp[row.precinct] = row.precinct
    # seems easier to just return a list than to deal with a dict - precinct.values()[0]
    for r in tmp:
        precinct.append(r)
    return precinct

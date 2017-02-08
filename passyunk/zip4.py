from __future__ import print_function

import csv
import os
import re
import sys

__author__ = 'tom.swanson'

cwd = os.path.dirname(__file__)
cwd += '/pdata'
# use the cleanded up file
zip4file = 'uspszip4'


def csv_path(file_name):
    return os.path.join(cwd, file_name + '.csv').replace('\\', '/')


zip4_basename = {}
zip4_list = []
zip4_name = {}


class Zip4s:
    def __init__(self, row):
        self.base = row[0]
        self.pre = row[1]
        self.name = row[2]
        self.suffix = row[3]
        self.post = row[4]
        self.low = int(row[5])
        self.high = int(row[6])
        self.oeb = row[7]
        self.unit = row[8].strip()
        # self.unitlow = row[9]
        self.unitlow = parse_unit_num(row[9].strip())
        # self.unithigh = row[10]
        self.unithigh = parse_unit_num(row[10].strip())
        self.unitoeb = row[11]
        self.buildingorfirm = row[12].strip()
        self.recordtype = row[13].strip()
        self.zipcode = row[14]
        self.zip4 = row[15]


class NameOnly:
    def __init__(self, row):
        self.name = row[0]
        self.low = row[1]
        self.high = row[2]


class UnitNum:
    def __init__(self):
        self.full = ''
        self.pre = ''
        self.post = ''
        self.num = -1


def parse_unit_num(unitnum):
    rt = UnitNum()
    if unitnum == '':
        return rt

    try:
        rt.num = int(unitnum)
        rt.full = unitnum
        return rt
    except ValueError:
        pass

    if unitnum.isalpha():
        rt.full = unitnum
        rt.num = -1
        return rt
    if unitnum.isalnum():
        ack = re.findall(r"[^\W\d_]+|\d+", unitnum)
        if len(ack) < 2:
            print("error: " + unitnum, file=sys.stderr)
        if len(ack) == 2:
            if ack[0].isdigit() and ack[1].isalpha():
                rt.full = unitnum
                rt.post = ack[1]
                rt.num = int(ack[0])
            if ack[1].isdigit() and ack[0].isalpha():
                rt.full = unitnum
                rt.pre = ack[0]
                rt.num = int(ack[1])
        if len(ack) == 3:
            if ack[2].isdigit():
                rt.full = unitnum
                rt.pre = ack[0] + ack[1]
                rt.num = int(ack[2])
            elif ack[1].isdigit() and ack[2].isalpha():
                rt.full = unitnum
                rt.pre = ack[0]
                rt.post = ack[2]
                rt.num = int(ack[1])
        if len(ack) > 3:
            i = 0
            l = len(ack)
            if ack[l - 1].isdigit():
                rt.full = unitnum
                for a in ack:
                    rt.pre += a
                    i += 1
                    if i == l - 1:
                        break
                rt.num = int(ack[l - 1])
            elif ack[l - 2].isdigit() and ack[l - 1].isalpha():
                rt.full = unitnum
                for a in ack:
                    rt.pre += a
                    i += 1
                    if i == l - 2:
                        break
                rt.post = ack[l - 1]
                rt.num = int(ack[l - 2])

    return rt


def test_zip4_file():
    path = csv_path(zip4file)
    return os.path.isfile(path)


def create_zip4_lookup():
    if not test_zip4_file():
        return False
    path = csv_path(zip4file)
    f = open(path, 'r')
    i = 0
    j = 0
    jbase = 0

    try:
        reader = csv.reader(f)
        p_name = ''
        p_base = ''

        for row in reader:
            if i == 0:
                i += 1
                continue
            r = Zip4s(row)
            c_name = r.name
            c_base = r.base

            if c_name != p_name and i != 0:
                ack = [p_name, j - 1, i - 1]
                r2 = NameOnly(ack)
                zip4_name[p_name] = r2
                j = i

            if c_base != p_base and i != 0:
                ack = [p_base, jbase - 1, i - 1]
                r2 = NameOnly(ack)
                zip4_basename[p_base] = r2
                jbase = i

            zip4_list.append(r)
            p_name = c_name
            p_base = c_base
            i += 1

    except IOError:
        print('Error opening ' + path, sys.exc_info()[0])
    ack = [p_base, jbase - 1, i - 1]
    r2 = NameOnly(ack)
    zip4_basename[p_base] = r2

    # validate_zip4_basename()

    f.close()
    return True


def validate_zip4_basename():
    for r in zip4_basename:
        row = zip4_basename[r]
        row_list = zip4_list[row.low:row.high]
        name = {}
        for st in row_list:
            name[st.base] = st.base
        if len(name) > 1:
            for ack in name:
                print(ack)


def is_zip4_base(test):
    try:
        name = zip4_basename[test]
    except KeyError:
        row = []
        # row.append([' ', 0, 0])
        return row
    return zip4_list[name.low:name.high]


def is_zip4_name(test):
    try:
        name = zip4_name[test]
    except KeyError:
        row = []
        # row.append([' ', 0, 0])
        return row
    return zip4_list[name.low:name.high]


def get_unique_zipcodes(lst):
    tmp = {}
    zips = []
    for row in lst:
        tmp[row.zipcode] = row.zipcode
    # seems easier to just return a list than to deal with a dict - zips.values()[0]
    for r in tmp:
        zips.append(r)
    return zips


def get_zip_info(address, input_):
    zlist = is_zip4_base(address.street.full)
    addr_unit = parse_unit_num(address.address_unit.unit_num)
    addr_type = address.address_unit.unit_type
    if addr_type == '#':
        addr_type = ''

    if len(zlist) > 0:
        mlist = []
        for row in zlist:
            if row.low <= address.address.low_num <= row.high and (
                            address.address.parity == row.oeb or row.oeb == 'B'):
                # if address.address_unit.unit_type == '' and address.address_unit.unit_num =='' and row.unit == '' and row.unitlow.full == '':
                #     mlist.append(row)
                # if address.address_unit.unit_num != '' and row.unit != '' and address.address_unit.unit_num == row.unit:
                #     mlist.append(row)
                # if address.address_unit.unit_type != '' and row.unitlow.full != '':
                mlist.append(row)

        if len(mlist) == 0:
            address.mailing.zip4 = ''
        if len(mlist) == 1:
            address.mailing.zipcode = mlist[0].zipcode
            address.mailing.zip4 = mlist[0].zip4
            address.mailing.uspstype = mlist[0].recordtype
            address.mailing.bldgfirm = mlist[0].buildingorfirm
            return

        elif len(mlist) > 1:
            if address.address_unit.unit_num == '' and addr_type == '':
                address.mailing.matchdesc = 'Multiple Zip4 Matches'

            # this is likely a building with multiple zip4s
            # example for logic - 523 N BROAD ST , we want the buildingfirm if it exists, take the base zip4
            if address.address_unit.unit_num == '' and addr_type == '':
                for m in mlist:
                    if m.unit == '' and m.unitlow.full == '':

                        #use the base zip4, take the first one
                        if m.recordtype == 'S' and address.mailing.uspstype == '':
                            address.mailing.uspstype = m.recordtype
                            address.mailing.zip4 = m.zip4

                        # not sure if there are more than one ever but we will take the last one for now
                        # this appears to be the logic usps applies where bldg firm addresses are the base
                        # zip4
                        if m.buildingorfirm.strip() != '':
                            address.mailing.bldgfirm = m.buildingorfirm
                            address.mailing.uspstype = m.recordtype
                            address.mailing.zip4 = m.zip4


                # Make sure the zipzode in the list is unique.  If so, your good, revert otherwise.
                zips = get_unique_zipcodes(mlist)
                if len(zips) == 1:
                    address.mailing.zipcode = zips[0]
                else:
                    address.mailing.matchdesc = 'Multiple Zipcode Matches'
                    address.mailing.uspstype = ''
                    address.mailing.zip4 = ''
                    address.mailing.bldgfirm = ''

                # for key,value in sorted(recordtypedict.items()):
                #    print(value, file=sys.stderr)
                # print('multiple matches for address with unit num but no type '+ input_, file=sys.stderr)
                return

            # input address does not have a unit type.  If the unit numbers match and there is only one match in USPS
            # it's a good match.  If there are more than one, it would appear that there is something like Penthouse and
            # apt with the same number.  If there are no matches, don't give up, USPS might not have that specific unit.
            # Check highrise list
            if address.address_unit.unit_num != '' and addr_type == '':
                mlist2 = []
                for m in mlist:
                    # TODO handle OEB
                    # Compare unit nums in a try statement to keep Python 3 from
                    # complaining about mixed str/int types.
                    try:
                        if m.unitlow.num <= addr_unit.num <= m.unithigh.num and m.unitlow.pre == addr_unit.pre and m.unitlow.post <= addr_unit.post <= m.unithigh.post:
                            mlist2.append(m)
                        if addr_unit.num == -1 and m.unitlow.full <= addr_unit.num <= m.unithigh.full:
                            mlist2.append(m)
                    except TypeError:
                        pass
                if len(mlist2) == 1:
                    address.mailing.zipcode = mlist2[0].zipcode
                    address.mailing.zip4 = mlist2[0].zip4
                    address.address_unit.unit_type = mlist2[0].unit
                    address.mailing.uspstype = mlist2[0].recordtype
                    return

                # if usps has a record for both UNIT and APT, take the APT record
                #   This give the correct result but might need to handle these zip4 records better in future
                # 220 LOCUST ST # 2AS -2AS
                # 220 LOCUST ST # 2A - 2H
                if len(mlist2) == 2 and mlist2[0].zip4 == mlist2[1].zip4:
                    address.mailing.zipcode = mlist2[0].zipcode
                    address.mailing.zip4 = mlist2[0].zip4
                    address.address_unit.unit_type = mlist2[0].unit
                    address.mailing.uspstype = mlist2[0].recordtype
                    # print('Multiple matches, everything the same but unit: '+ input_, file=sys.stderr)
                    # print('  '+mlist2[0].unit, file=sys.stderr)
                    # print('  '+mlist2[1].unit, file=sys.stderr)
                    return

                # Check to see if one of the records has an exact unit high and low match to the input addr.  If so use it.
                # TODO: 11580 ROOSEVELT BLVD # 116
                if len(mlist2) == 2 and mlist2[0].zip4 != mlist2[1].zip4 and mlist2[0].unit == mlist2[1].unit:
                    if mlist2[0].unitlow.full == mlist2[0].unithigh.full:
                        address.mailing.zipcode = mlist2[0].zipcode
                        address.mailing.zip4 = mlist2[0].zip4
                        address.address_unit.unit_type = mlist2[0].unit
                        address.mailing.uspstype = mlist2[0].recordtype
                        # print('Multiple matches, unit range and exact: '+ input_, file=sys.stderr)
                        # print('  '+mlist2[0].unitlow.full, file=sys.stderr)
                        # print('  '+mlist2[0].unithigh.full, file=sys.stderr)
                        return
                    if mlist2[1].unitlow.full == mlist2[1].unithigh.full:
                        address.mailing.zipcode = mlist2[1].zipcode
                        address.mailing.zip4 = mlist2[1].zip4
                        address.address_unit.unit_type = mlist2[1].unit
                        address.mailing.uspstype = mlist2[0].recordtype
                        # print('Multiple matches, unit range and exact: '+ input_, file=sys.stderr)
                        # print('  '+mlist2[1].unitlow.full, file=sys.stderr)
                        # print('  '+mlist2[1].unithigh.full, file=sys.stderr)
                        return

                if len(mlist2) == 0:
                    # lets just try the base address.  If there is just one match with zip4s with not secondary addr,
                    # its a good match
                    # 808 Carpenter St # D
                    mlist2 = []
                    for m in mlist:
                        # TODO handle OEB
                        if m.recordtype == 'H' and m.unitlow.full == '' and m.unit == '':
                            mlist2.append(m)
                        if len(mlist2) == 1:
                            address.mailing.zipcode = mlist2[0].zipcode
                            address.mailing.zip4 = mlist2[0].zip4
                            address.address_unit.unit_type = mlist2[0].unit
                            address.mailing.uspstype = m.recordtype
                            return

                    # might be able to get a good zipcode still
                    zips = get_unique_zipcodes(mlist)
                    if len(zips) == 1:
                        address.mailing.zipcode = zips[0]
                        address.mailing.matchdesc = 'NMx'
                        return
                        # print('Todo: 0 matches for address with unit num but no type ' + input_, file=sys.stderr)

                if len(mlist2) > 1:
                    # might be able to get a good zipcode still
                    zips = get_unique_zipcodes(mlist)
                    if len(zips) == 1:
                        address.mailing.zipcode = zips[0]
                        address.mailing.matchdesc = 'NMu'
                    # print('multiple matches for address with unit num but no type ' + input_, file=sys.stderr)
                    return

            # only have a unit type and no unit number
            if address.address_unit.unit_num == '' and address.address_unit.unit_type != '':
                mlist2 = []
                for m in mlist:
                    if m.unit == address.address_unit.unit_type:
                        mlist2.append(m)
                if len(mlist2) == 1:
                    address.mailing.zipcode = mlist2[0].zipcode
                    address.mailing.zip4 = mlist2[0].zip4
                    address.mailing.uspstype = mlist2[0].recordtype
                    return
                if len(mlist2) == 0:
                    zips = get_unique_zipcodes(mlist)
                    if len(zips) == 1:
                        address.mailing.zipcode = zips[0]
                        # print('Todo: 0 matches for address with unit type but no number ' + input_, file=sys.stderr)
                if len(mlist2) > 1:
                    # might be able to get a good zipcode still
                    zips = get_unique_zipcodes(mlist)
                    if len(zips) == 1:
                        address.mailing.zipcode = zips[0]
                    # print('multiple matches for address with unit type but no number ' + input_, file=sys.stderr)
                    return

            if address.address_unit.unit_num != '' and addr_type != '':
                mlist2 = []
                # TODO handle OEB
                for m in mlist:
                    if m.unit == address.address_unit.unit_type and \
                                            m.unitlow.num <= addr_unit.num <= m.unithigh.num and \
                                            m.unitlow.post <= addr_unit.post <= m.unithigh.post and \
                                    m.unitlow.pre == addr_unit.pre:
                        if m.unitlow.num == -1 and m.unitlow.post == '' and m.unitlow.pre == '':
                            if addr_unit.full != -1 and m.unitlow.full <= addr_unit.full <= m.unithigh.full:
                                mlist2.append(m)
                        else:
                            mlist2.append(m)

                if len(mlist2) == 1:
                    address.mailing.zipcode = mlist2[0].zipcode
                    address.mailing.zip4 = mlist2[0].zip4
                    address.mailing.uspstype = mlist2[0].recordtype
                    return
                # lets try this again without the unit_type
                if len(mlist2) == 0:
                    for m in mlist:
                        if m.unitlow.num <= addr_unit.num <= m.unithigh.num and m.unitlow.pre == addr_unit.pre:
                            mlist2.append(m)
                    if len(mlist2) == 1:
                        # Stay away from agressive unit changes
                        # For now, just listing exceptions as they are found
                        if addr_type == 'FL' and mlist2[0].unit == 'APT' or \
                                                addr_type == 'REAR' and mlist2[0].unit == 'APT' or \
                                                addr_type == 'REAR' and mlist2[0].unit == 'FRNT' or \
                                                addr_type == 'FRNT' and mlist2[0].unit == 'REAR' or \
                                                addr_type == 'FL' and mlist2[0].unit == 'SIDE' or \
                                                addr_type == 'FL' and mlist2[0].unit == 'REAR' or \
                                                addr_type == 'FL' and mlist2[0].unit == 'FRNT':
                            pass  # print('Unit No Change - '+ input_ +' : '+ mlist2[0].unit, file=sys.stderr)
                        else:
                            if address.address_unit.unit_type == mlist2[0].unit or (
                                            address.address_unit.unit_type == 'UNIT' and mlist2[0].unit == 'APT') or (
                                            address.address_unit.unit_type == 'APT' and mlist2[0].unit == 'UNIT'):
                                address.address_unit.unit_type = mlist2[0].unit
                                suppress_msg = True
                            else:
                                address.address_unit.unit_type = mlist2[0].unit
                                suppress_msg = False
                            address.mailing.zipcode = mlist2[0].zipcode
                            address.mailing.zip4 = mlist2[0].zip4
                            address.mailing.uspstype = mlist2[0].recordtype

                            # need because of addrs like this - 3900 FORD ROAD UNIT PH
                            if address.address_unit.unit_type == address.address_unit.unit_num:
                                address.address_unit.unit_num = ''
                                # if suppress_msg == False:
                                # print('Unit Change - ' + input_ + ' : ' + mlist2[0].unit, file=sys.stderr)
                            return

                    # might be able to get a good zipcode still
                    zips = get_unique_zipcodes(mlist)
                    if len(zips) == 1:
                        address.mailing.zipcode = zips[0]
                        address.mailing.matchdesc = 'NM'
                        return

                        # print('Todo: 0 matches for address with unit type and  number ' + input_, file=sys.stderr)

                if len(mlist2) > 1:
                    for m in mlist2:
                        if m.unitlow.full == addr_unit.full and m.unithigh.full == addr_unit.full:
                            address.mailing.uspstype = m.recordtype
                            address.mailing.zipcode = m.zipcode
                            address.mailing.zip4 = m.zip4
                            return

                    # might be able to get a good zipcode still
                    zips = get_unique_zipcodes(mlist)
                    if len(zips) == 1:
                        address.mailing.zipcode = zips[0]
                        address.mailing.matchdesc = 'MMA_UN_UZ'
                        #print('multiple matches for address with unit type and number - unique zip :' + input_,
                        #      file=sys.stderr)
                    else:
                        address.mailing.matchdesc = 'MMA_UN_MUZ'
                        #print('multiple matches for address with unit type and number multiple unique zip :' + input_,
                        #      file=sys.stderr)
                    return

                    # print('multiple: ' + input_, file=sys.stderr)
                    # else:
                    #     print('no zip: '+address.address.full+' '+address.street.full, file=sys.stderr)

                    # zlist =is_zip4_name(address.street.full)
                    # if len(zlist) > 0:
                    #     print("ack", file=sys.stderr)

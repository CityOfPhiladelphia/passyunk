from __future__ import print_function

import csv
import os
import sys
# import Levenshtein
from fuzzywuzzy import process
from shapely.wkt import loads
from shapely.geometry import mapping

__author__ = 'tom.swanson'

cwd = os.path.dirname(__file__)
cwd += '/pdata'
# cwd = cwd.replace('\\','/')
cl_file = 'centerline_shape'
full_range_buffer = 17
# MAX_RANGE = 200

# cfout = open(os.path.dirname(__file__)+'/sandbox/fuzzyout.csv', 'w')
# print(Levenshtein.ratio('BREAD', 'BROAD'))


def csv_path(file_name):
    return os.path.join(cwd, file_name + '.csv').replace('\\', '/')


cl_basename = {}  # dict
cl_list = []  # array
cl_name = {}
cl_name_fw = []

for x in range(0, 26):
    cl_name_fw.append([x])


class Centerline:
    def __init__(self, row):
        self.pre = row[0].strip()
        self.name = row[1].strip()
        self.suffix = row[2].strip()
        self.post = row[3].strip()
        self.from_left = int(row[4])
        self.to_left = int(row[5])
        self.from_right = int(row[6])
        self.to_right = int(row[7])
        self.street_code = row[8]
        self.cl_seg_id = row[9]
        self.cl_responsibility = row[10].strip()
        self.base = '{} {} {} {}'.format(self.pre, self.name, self.suffix, self.post)
        self.base = ' '.join(self.base.split())
        self.oeb_right = oeb(self.from_right, self.to_right)
        self.oeb_left = oeb(self.from_left, self.to_left)
        self.shape = row[11]

    def __str__(self):
        return 'Centerline: {}-{} {}'.format(
            min(self.from_left, self.from_right),
            max(self.to_left, self.to_right),
            self.base
        )

    def __repr__(self):
        return self.__str__()

class NameOnly:
    def __init__(self, row):
        self.name = row[0]
        self.low = row[1]
        self.high = row[2]


class NameFW:
    def __init__(self):
        self.name = ''

class ShapeOnly:
    def __init__(self, row):
        self.shape = row[11]
def test_cl_file():
    path = csv_path(cl_file)
    return os.path.isfile(path)


def create_cl_lookup():
    is_cl_file = test_cl_file()
    if not is_cl_file:
        return False
    path = csv_path(cl_file)
    f = open(path, 'r')
    i = 0
    j = 0
    jbase = 0
    p_base = ''
    try:
        reader = csv.reader(f)
        p_name = ''
        p_base = ''

        for row in reader:
            if i == 0:
                i += 1
                continue
            r = Centerline(row)
            if i == 0:
                rp = r
            c_name = r.name
            c_base = r.base

            if c_name != p_name and i != 0:
                ack = [p_name, j - 1, i - 1]
                r2 = NameOnly(ack)
                cl_name[p_name] = r2
                j = i

            if c_base != p_base and i != 0:
                ack = [p_base, jbase - 1, i - 1]
                r2 = NameOnly(ack)
                cl_basename[p_base] = r2
                jbase = i

            cl_list.append(r)
            rp = r
            p_name = c_name
            p_base = c_base
            i += 1

    except IOError:
        print('Error opening ' + path, sys.exc_info()[0])
    ack = [p_base, jbase - 1, i - 1]
    r2 = NameOnly(ack)
    cl_basename[p_base] = r2

    validate_cl_basename()

    create_cl_name_fw()

    f.close()
    return True


def create_cl_name_fw():
    # cl_name.sort()
    for item in cl_name:
        if item == '':
            continue
        if len(item) <= 4:
            continue
        i = ord(item[0])
        if i < 65 or i > 90:
            continue
        i -= 65
        try:
            cl_name_fw[i].append(item)
        except Exception:
            print('Exception loading Centerline for fw ' + item + ' ' + str(i), sys.exc_info()[0])

    for item in cl_name_fw:
        # print(item[0],len(item))
        item.pop(0)
        item.sort()
    return


def oeb(fr, to):
    ret = 'U'
    if fr == '' or fr == '0' or to == '' or to == '0':
        return 'U'

    if fr % 2 == 0:
        ret = 'E'
    else:
        ret = 'O'
    if to % 2 == 0:
        ret_to = 'E'
    else:
        ret_to = 'O'

    if ret != ret_to:
        return 'B'

    return ret


def validate_cl_basename():
    for r in cl_basename:
        row = cl_basename[r]
        row_list = cl_list[row.low:row.high]
        name = {}
        for st in row_list:
            name[st.base] = st.base
        if len(name) > 1:
            for ack in name:
                print(ack)


def is_cl_base(test):
    try:
        name = cl_basename[test]
    except KeyError:
        row = []
        # row.append([' ', 0, 0])
        return row
    return cl_list[name.low:name.high]


def is_cl_name(test):
    try:
        name = cl_name[test]
    except KeyError:
        row = []
        # row.append([' ', 0, 0])
        return row
    return cl_list[name.low:name.high]


def interpolate_line(line, distance_ratio, _buffer):
	'''
	Interpolate along a line with a buffer at both ends.
	'''
	length = line.length
	buffered_length = length - (_buffer * 2)
	buffered_distance = distance_ratio * buffered_length
	absolute_distance = _buffer + buffered_distance
	return line.interpolate(absolute_distance)


def get_midpoint_geom(address):
    cl_shape = loads(address.street.shape)
    geom = cl_shape.centroid
    geom = mapping(geom)
    address.geometry = geom


def get_full_range_geom(address, match):
    addr_low_num = address.address.low_num
    cl_shape = loads(address.street.shape)
    f_l = match.from_left
    f_r = match.from_right
    t_l = match.to_left
    t_r = match.to_right
    seg_side = "R" if f_r % 2 == addr_low_num % 2 else "L"
    # Check if address low num is within centerline seg full address range with parity:
    from_num, to_num = (f_r, t_r) if seg_side == "R" else (
    f_l, t_l)
    side_delta = to_num - from_num
    if side_delta == 0:
        distance_ratio = 0.5
    else:
        distance_ratio = (addr_low_num - from_num) / side_delta
    geom = interpolate_line(cl_shape, distance_ratio, full_range_buffer)
    geom = mapping(geom)
    address.geometry = geom


def get_intersection_geom(address):
    geom1 = loads(address.street.shape)
    geom2 = loads(address.street.shape_2)
    geom = geom1.intersection(geom2)
    geom = mapping(geom)
    address.geometry = geom


def get_address_geom(address, addr_uber, match):
    type = addr_uber.type
    if type == 'street':
        get_midpoint_geom(address)
    elif type == 'address':
        get_full_range_geom(address, match)
    elif type == 'intersection_addr':
        get_intersection_geom(address)
    else:
        pass
    return address.geometry


def get_cl_info(address, addr_uber, MAX_RANGE):
    addr_low_num = address.address.low_num
    addr_parity = address.address.parity

    # Get matching centerlines based on street name
    centerlines = is_cl_base(address.street.full)

    # If there are matches
    if len(centerlines) > 0:
        matches = []
        cur_closest = None
        cur_closest_offset = None
        cur_closest_addr = 0

        # Loop over matches
        for cl in centerlines:
            from_left = cl.from_left
            from_right = cl.from_right
            to_left = cl.to_left
            to_right = cl.to_right

            # Try to match on the left
            if from_left <= addr_low_num <= to_left and \
                cl.oeb_left == addr_parity:
                matches.append(cl)
            # Try to match on the right
            elif from_right <= addr_low_num <= to_right and \
                cl.oeb_right == addr_parity:
                matches.append(cl)
            # If no matches, find the one with the nearest address range
            else:
                if from_left == 0:
                    continue

                # Loop over addresses in range to find the min
                if cur_closest is None or \
                    abs(from_left - addr_low_num) < cur_closest_offset:
                    cur_closest_offset = abs(from_left - addr_low_num)
                    cur_closest = cl
                    cur_closest_addr = from_left
                if abs(from_right - addr_low_num) < cur_closest_offset:
                    cur_closest_offset = abs(from_right - addr_low_num)
                    cur_closest = cl
                    cur_closest_addr = from_right
                if abs(addr_low_num - to_left) < cur_closest_offset:
                    cur_closest_offset = abs(addr_low_num - to_left)
                    cur_closest = cl
                    cur_closest_addr = to_left
                if abs(addr_low_num - to_right) < cur_closest_offset:
                    cur_closest_offset = abs(addr_low_num - to_right)
                    cur_closest = cl
                    cur_closest_addr = to_right

        if len(matches) == 0:
            # good street name but no matching address range
            if addr_low_num == -1 and cur_closest is not None:
                address.street.street_code = cur_closest.street_code
                address.street.shape = cur_closest.shape
                address.street.is_centerline_match = True
                return

            if cur_closest_offset is not None and cur_closest_offset < MAX_RANGE:
                address.street.street_code = cur_closest.street_code
                address.street.shape = cur_closest.shape
                address.cl_seg_id = cur_closest.cl_seg_id
                address.cl_responsibility = cur_closest.cl_responsibility
                address.cl_addr_match = 'RANGE:' + str(cur_closest_offset)
                address.address.full = str(cur_closest_addr)
                return

            # Treat as a Street Match
            addr_uber.type = 'street'
            address.street.street_code = cl.street_code
            address.street.shape = cl.shape
            address.geometry = get_address_geom(address, addr_uber, cl)
            address.cl_addr_match = 'MATCH TO STREET. ADDR NUMBER NO MATCH'
            return

        # Exact Match
        if len(matches) == 1:
            match = matches[0]
            address.street.street_code = match.street_code
            address.street.shape = match.shape
            address.cl_seg_id = match.cl_seg_id
            address.cl_responsibility = match.cl_responsibility
            address.cl_addr_match = 'A'
            address.geometry = get_address_geom(address, addr_uber, match)
            return

        # Exact Street match, multiple range matches, return the count of matches
        if len(matches) > 1:
            address.street.street_code = cl.street_code
            address.street.shape = cl.shape
            address.cl_addr_match = 'AM'
            # address.cl_addr_match = str(len(matches))
            return

    # If we didn't find a match using the street base (e.g. N 10TH ST), try
    # using the street name (10TH).
    centerlines = is_cl_name(address.street.name)

    if len(centerlines) > 0:
        matches = []
        for row in centerlines:
            if row.from_left <= addr_low_num <= row.to_left and row.oeb_left == addr_parity:
                if (address.street.predir != '' and address.street.predir == row.pre) or (
                                address.street.predir == '' and row.pre == '') or (
                                address.street.predir == '' and row.pre != '') or (
                                address.street.predir != '' and row.pre == ''):
                    if (address.street.postdir != '' and address.street.postdir == row.post) or (
                                    address.street.postdir == '' and row.post == '') or (
                                    address.street.postdir == '' and row.post != '') or (
                                    address.street.postdir != '' and row.post == ''):
                        if (address.street.suffix != '' and address.street.suffix == row.suffix) or (
                                        address.street.suffix == '' and row.suffix == '') or (
                                        address.street.suffix == '' and row.suffix != '') or (
                                        address.street.suffix != '' and row.suffix == ''):
                            matches.append(row)
            elif row.from_right <= addr_low_num <= row.to_right and row.oeb_right == addr_parity:
                if (address.street.predir != '' and address.street.predir == row.pre) or (
                                address.street.predir == '' and row.pre == '') or (
                                address.street.predir == '' and row.pre != '') or (
                                address.street.predir != '' and row.pre == ''):
                    if (address.street.postdir != '' and address.street.postdir == row.post) or (
                                    address.street.postdir == '' and row.post == '') or (
                                    address.street.postdir == '' and row.post != '') or (
                                    address.street.postdir != '' and row.post == ''):
                        if (address.street.suffix != '' and address.street.suffix == row.suffix) or (
                                        address.street.suffix == '' and row.suffix == '') or (
                                        address.street.suffix == '' and row.suffix != '') or (
                                        address.street.suffix != '' and row.suffix == ''):
                            matches.append(row)

        # Let's just see if a match to the street name can be made.  If there is only one match, it should be safe to use
        # at this point.  The only difference in logic below from above is that suffixes do not have to match
        # 1018 ALPENA DR - should find RD
        if len(matches) == 0:
            matches = []
            for row in centerlines:
                if row.from_left <= addr_low_num <= row.to_left and row.oeb_left == addr_parity:
                    if (address.street.predir != '' and address.street.predir == row.pre) or (
                                    address.street.predir == '' and row.pre == '') or (
                                    address.street.predir == '' and row.pre != '') or (
                                    address.street.predir != '' and row.pre == ''):
                        if (address.street.postdir != '' and address.street.postdir == row.post) or (
                                        address.street.postdir == '' and row.post == '') or (
                                        address.street.postdir == '' and row.post != '') or (
                                        address.street.postdir != '' and row.post == ''):
                            if (address.street.suffix != '' and address.street.suffix != row.suffix) or (
                                            address.street.suffix == '' and row.suffix == '') or (
                                            address.street.suffix == '' and row.suffix != '') or (
                                            address.street.suffix != '' and row.suffix == ''):
                                matches.append(row)
                elif row.from_right <= addr_low_num <= row.to_right and row.oeb_right == addr_parity:
                    if (address.street.predir != '' and address.street.predir == row.pre) or (
                                    address.street.predir == '' and row.pre == '') or (
                                    address.street.predir == '' and row.pre != '') or (
                                    address.street.predir != '' and row.pre == ''):
                        if (address.street.postdir != '' and address.street.postdir == row.post) or (
                                        address.street.postdir == '' and row.post == '') or (
                                        address.street.postdir == '' and row.post != '') or (
                                        address.street.postdir != '' and row.post == ''):
                            if (address.street.suffix != '' and address.street.suffix != row.suffix) or (
                                            address.street.suffix == '' and row.suffix == '') or (
                                            address.street.suffix == '' and row.suffix != '') or (
                                            address.street.suffix != '' and row.suffix == ''):
                                matches.append(row)

            if len(matches) == 0:
                address.cl_addr_match = 'NONE'
                return

            if len(matches) > 1:
                address.cl_addr_match = 'MULTI2'
                return

            if len(matches) == 1:
                match = matches[0]
                match_type = 'SS'
                if address.street.predir != match.pre:
                    match_type += ' Pre'
                    address.street.predir = match.pre
                if address.street.postdir != match.post:
                    match_type += ' Post'
                    address.street.postdir = match.post
                if address.street.suffix != match.suffix:
                    match_type += ' Suffix'
                    address.street.suffix = match.suffix
                address.street.street_code = match.street_code
                address.street.shape = match.shape
                address.cl_seg_id = match.cl_seg_id
                address.cl_responsibility = match.cl_responsibility
                address.cl_addr_match = match_type
                return

        if len(matches) == 1:
            match = matches[0]
            match_type = 'B'

            if address.street.predir != match.pre:
                match_type += ' Pre'
                address.street.predir = match.pre
            if address.street.postdir != match.post:
                match_type += ' Post'
                address.street.postdir = match.post
                # The postdir was parsed to unit - 1 S SCHUYLKILL AV W,  Need to removed unit now that post dir was
                # added back in
                if address.street.postdir == address.address_unit.unit_num and address.address_unit.unit_type == '#':
                    address.address_unit.unit_num = ''
                    address.address_unit.unit_type = ''

            if address.street.suffix != match.suffix:
                match_type += ' Suffix'
                address.street.suffix = match.suffix
            address.street.street_code = match.street_code
            address.street.shape = match.shape
            address.cl_seg_id = match.cl_seg_id
            address.cl_responsibility = match.cl_responsibility
            address.cl_addr_match = match_type
            return

        # need to resolve dir and/or suffix
        if len(matches) > 1:
            address.street.street_code = row.street_code
            address.street.shape = row.shape
            address.cl_addr_match = 'MULTI'  # str(len(matches))
            return

    if len(address.street.name) > 3 and address.street.name.isalpha():
        # no CL match yet, try fuzzy
        i = ord(address.street.name[0])
        if i < 65 or i > 90:
            print('Invalid street name for fuzzy match: ' + address.street.name)
        i -= 65

        # match scores of 90 are very suspect using this method
        options = process.extract(address.street.name, cl_name_fw[i], limit=2)

        tie = ''
        # print(input_)
        # print(options)
        if len(options) > 0 and options[0][0][0] == address.street.name[0] and len(address.street.name) > 3 and \
                        int(options[0][1]) >= 91 and abs(len(address.street.name) - len(options[0][0])) <= 4:
            if len(options) > 1 and options[0][1] == options[1][1]:
                tie_print = addr_uber.input_address + ',' + address.street.name + ',' + options[0][0] + ',' + str(
                    options[0][1]) + ',' + options[1][0] + ',' + str(
                    options[1][1])
                # print(tie_print)
                tie = 'Y'
            # out = input_ + ',' + address.street.name + ',' + options[0][0] + ',' + str(options[0][1])+ ',' + tie+'\n'
            # cfout.write(out)
            # cfout.flush()
            address.street.name = options[0][0]
            address.street.score = tie + str(options[0][1])

            get_cl_info(address, addr_uber, MAX_RANGE)
            return

# simple method for adding street_code to street_2
def get_cl_info_street2(address):

    # Get matching centerlines based on street name
    centerlines = is_cl_base(address.street_2.full)

    # If there are matches
    if len(centerlines) > 0:
        address.street_2.street_code = centerlines[0].street_code
        address.street_2.shape = centerlines[0].shape
        return


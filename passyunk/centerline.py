from __future__ import print_function

import csv
import os
import sys
# import Levenshtein
from fuzzywuzzy import process
from shapely.wkt import loads
from shapely.geometry import mapping, Point, MultiLineString
from math import sin, cos, atan2, pi

__author__ = 'tom.swanson'

cwd = os.path.dirname(__file__)
cwd += '/pdata'
# cwd = cwd.replace('\\','/')
#cl_file = 'centerline'
al_file = 'alias'
cl_file = 'centerline_shape'
int_file = 'intersections'
full_range_buffer = 17
centerline_offset = 5
# MAX_RANGE = 200

# cfout = open(os.path.dirname(__file__)+'/sandbox/fuzzyout.csv', 'w')
# print(Levenshtein.ratio('BREAD', 'BROAD'))


def csv_path(file_name):
    return os.path.join(cwd, file_name + '.csv').replace('\\', '/')


cl_basename = {}  # dict
cl_list = []  # array
cl_name = {}
cl_name_fw = []
al_basename = {}
al_list = []
al_name = {}
al_name_fw = []

for x in range(0, 26):
    cl_name_fw.append([x])


class Intersection:
    def __init__(self, int_row):
        self.street_1_code = int_row[0].strip()
        self.street_2_code = int_row[1].strip()
        self.shape = int_row[2].strip()


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


class Alias:
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
        self.cl_pre = row[11].strip()
        self.cl_name = row[12].strip()
        self.cl_suffix = row[13].strip()
        self.cl_post = row[14].strip()
        self.cl_name_full = row[15].strip()


    def __str__(self):
        return 'Alias: {}-{} {}'.format(
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


def test_file(file):
    path = csv_path(file)
    return os.path.isfile(path)


def test_al_file():
    path = csv_path(al_file)
    return os.path.isfile(path)


def create_cl_lookup():
    is_cl_file = test_file(cl_file)
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


def create_al_lookup():
    is_al_file = test_al_file()
    if not is_al_file:
        return False
    path = csv_path(al_file)
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
            r = Alias(row)
            if i == 0:
                rp = r
            c_name = r.name
            c_base = r.base

            if c_name != p_name and i != 0:
                ack = [p_name, j - 1, i - 1]
                r2 = NameOnly(ack)
                al_name[p_name] = r2
                j = i

            if c_base != p_base and i != 0:
                ack = [p_base, jbase - 1, i - 1]
                r2 = NameOnly(ack)
                al_basename[p_base] = r2
                jbase = i

            al_list.append(r)
            rp = r
            p_name = c_name
            p_base = c_base
            i += 1

    except IOError:
        print('Error opening ' + path, sys.exc_info()[0])
    ack = [p_base, jbase - 1, i - 1]
    r2 = NameOnly(ack)
    al_basename[p_base] = r2

    validate_al_basename()

    # create_al_name_fw()

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


def validate_al_basename():
    for r in al_basename:
        row = al_basename[r]
        row_list = al_list[row.low:row.high]
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


def is_al_base(test):
    try:
        name = al_basename[test]
    except KeyError:
        row = []
        # row.append([' ', 0, 0])
        return row
    return al_list[name.low:name.high]


def is_cl_name(test):
    try:
        name = cl_name[test]
    except KeyError:
        row = []
        # row.append([' ', 0, 0])
        return row
    return cl_list[name.low:name.high]


def is_al_name(test):
    try:
        name = al_name[test]
    except KeyError:
        row = []
        # row.append([' ', 0, 0])
        return row
    return al_list[name.low:name.high]


def interpolate_line(line, distance_ratio, _buffer):
	'''
	Interpolate along a line with a buffer at both ends.
	'''
	length = line.length
	buffered_length = length - (_buffer * 2)
	buffered_distance = distance_ratio * buffered_length
	absolute_distance = _buffer + buffered_distance
	return line.interpolate(absolute_distance)


def offset(line, point, distance, seg_side):
    # Check for vertical line
    if line.coords[0][0] == line.coords[1][0]:
        pt_0 = line.coords[0]
        pt_1 = line.coords[1]
        upwards = True if pt_1[1] > pt_0[1] else False
        if (upwards and seg_side == 'R') or (not upwards and seg_side == 'L'):
            x_factor = 1
        else:
            x_factor = -1
        return Point([point.x + (distance * x_factor), point.y])

    assert None not in [line, point]
    assert distance > 0
    assert seg_side in ['L', 'R']

    xsect_x = point.x
    xsect_y = point.y
    coord_1 = None
    coord_2 = None

    # Find coords on either side of intersect point
    for i, coord in enumerate(line.coords[:-1]):
        coord_x, coord_y = coord
        next_coord = line.coords[i + 1]
        next_coord_x, next_coord_y = next_coord
        sandwich_x = coord_x < xsect_x < next_coord_x
        sandwich_y = coord_y <= xsect_y <= next_coord_y
        if sandwich_x or sandwich_y:
            coord_1 = coord
            coord_2 = next_coord
            break
    # Normalize coords to place in proper quadrant
    norm_x = next_coord[0] - coord[0]
    norm_y = next_coord[1] - coord[1]
    # Get angle of seg
    seg_angle = atan2(norm_y, norm_x)
    # Get angle of offset line
    if seg_side == 'L':
        offset_angle = seg_angle + (pi / 2)
    else:
        offset_angle = seg_angle - (pi / 2)
    # Get offset point
    delta_x = cos(offset_angle) * distance
    delta_y = sin(offset_angle) * distance
    x = xsect_x + delta_x
    y = xsect_y + delta_y
    return Point([x, y])


def project_shape(shape, from_srid, to_srid):
    from functools import partial
    import pyproj
    from shapely.ops import transform

    project = partial(
        pyproj.transform,
        # source coordinate system; preserve_units so that pyproj does not assume meters
        pyproj.Proj(init='epsg:{}'.format(from_srid), preserve_units=True),
        # destination coordinate system
        pyproj.Proj(init='epsg:{}'.format(to_srid), preserve_units=True))

    return transform(project, shape)


def get_street_geom(address):
    # TODO: use centerlines in state
    centerlines = is_cl_name(address.street.name)
    coords = []
    for centerline in centerlines:
        coords.append(loads(centerline.shape))
    multilinestring = MultiLineString(coords)
    xy = multilinestring.centroid
    snapped = multilinestring.interpolate(multilinestring.project(xy))
    geom = mapping(snapped)
    address.geometry = geom


def get_midpoint_geom(address, match):
    cl_shape = loads(address.street.shape)
    xy = cl_shape.centroid
    addr_low_num = address.address.low_num
    # apply offset only if there's an addr_low_num
    if addr_low_num != -1:
        f_r = match.from_right
        seg_side = "R" if f_r % 2 == addr_low_num % 2 else "L"
        xy_offset = offset(cl_shape, xy, centerline_offset, seg_side)
        geom = mapping(xy_offset)
    else:
        geom = mapping(xy)
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
    xy = interpolate_line(cl_shape, distance_ratio, full_range_buffer)
    xy_offset = offset(cl_shape, xy, centerline_offset, seg_side)
    geom = project_shape(xy_offset, 2272, 4326)
    geom = mapping(geom)
    address.geometry = geom


def get_int_geom(address):
    street_1_code = min(int(address.street.street_code), int(address.street_2.street_code))
    street_2_code = max(int(address.street.street_code), int(address.street_2.street_code))
    is_int_file = test_file(int_file)
    if not is_int_file:
        return False
    path = csv_path(int_file)
    with open(path) as infile:
        reader = csv.reader(infile)
        next(reader, None)
        for row in reader:
            intersection = Intersection(row)
            if int(intersection.street_1_code) == street_1_code and int(intersection.street_2_code) == street_2_code:
                geom = mapping(loads(intersection.shape))
                address.geometry = geom


def get_address_geom(address, addr_uber=None, match=None):
    type = addr_uber.type
    if type == 'street':
        get_street_geom(address)
    elif type == 'address':
        get_full_range_geom(address, match)
    elif type == 'intersection_addr':
        if address.street.street_code and address.street_2.street_code:
            get_int_geom(address)
    else:
        pass
    return address.geometry

def assign_cl_info(address, match):
    address.street.street_code = match.street_code
    address.cl_seg_id = match.cl_seg_id
    address.cl_responsibility = match.cl_responsibility
    address.street.shape = match.shape

def get_cl_info(address, addr_uber, MAX_RANGE):
    addr_low_num = address.address.low_num
    addr_parity = address.address.parity
    addr_street_full = address.street.full
    # Get matching centerlines based on street name
    centerlines = is_cl_base(addr_street_full)
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
            aliases = is_al_base(addr_street_full)
            # Check for alias
            if len(aliases) > 0:
                matches = []
                cur_closest = None
                cur_closest_offset = None
                cur_closest_addr = 0

                # Loop over matches
                for al in aliases:
                    from_left = al.from_left
                    from_right = al.from_right
                    to_left = al.to_left
                    to_right = al.to_right

                    if (from_left <= addr_low_num <= to_left and al.oeb_left == addr_parity) or (
                                from_right <= addr_low_num <= to_right and al.oeb_right == addr_parity):
                        addr_uber.components.street.full = al.cl_name_full
                        addr_uber.components.street.predir = al.cl_pre
                        addr_uber.components.street.name = al.cl_name
                        addr_uber.components.street.suffix = al.cl_suffix
                        addr_uber.components.street.postdir = al.cl_post

                        return get_cl_info(address, addr_uber, MAX_RANGE)

            if len(matches) == 0:
            # Didn't find an alias match
                if addr_low_num == -1 and cur_closest is not None:
                    address.street.is_centerline_match = True
                    address.street.street_code = cur_closest.street_code
                    address.street.shape = cur_closest.shape
                    # assign_cl_info(address, cur_closest)
                    return

                if cur_closest_offset is not None and cur_closest_offset < MAX_RANGE:
                    address.cl_addr_match = 'RANGE:' + str(cur_closest_offset)
                    address.address.full = str(cur_closest_addr)
                    assign_cl_info(address, cur_closest)
                    return

                # Treat as a Street Match
                if addr_uber.type != 'intersection_addr':
                    addr_uber.type = 'street'
                address.street.street_code = cl.street_code
                address.cl_addr_match = 'MATCH TO STREET. ADDR NUMBER NO MATCH'
                return

            if addr_low_num == -1 and cur_closest is not None:
                address.street.is_centerline_match = True
                address.street.street_code = cur_closest.street_code
                address.street.shape = cur_closest.shape
                # assign_cl_info(address, cur_closest)
                get_address_geom(address, addr_uber=addr_uber, match=cur_closest)
                return

            if cur_closest_offset is not None and cur_closest_offset < MAX_RANGE:
                address.cl_addr_match = 'RANGE:' + str(cur_closest_offset)
                address.address.full = str(cur_closest_addr)
                assign_cl_info(address, cur_closest)
                return

            # Treat as a Street Match
            addr_uber.type = 'street'
            address.street.street_code = cl.street_code
            address.street.shape = cl.shape
            get_address_geom(address, addr_uber=addr_uber, match=cl)
            address.cl_addr_match = 'MATCH TO STREET. ADDR NUMBER NO MATCH'
            return

        # Exact Match
        if len(matches) == 1:
            match = matches[0]
            address.cl_addr_match = 'A'
            assign_cl_info(address, match)
            get_address_geom(address, addr_uber=addr_uber, match=match)
            return

        # Exact Street match, multiple range matches, return the count of matches
        if len(matches) > 1:
            address.cl_addr_match = 'AM'
            address.street.street_code = cl.street_code
            address.street.shape = cl.shape
            get_address_geom(address, addr_uber=addr_uber, match=cl)
            # address.cl_addr_match = str(len(matches))
            return
    # If we didn't find a match using the street base (e.g. N 10TH ST), try
    # using the street name (10TH).
    centerlines = is_cl_name(address.street.name)
    if len(centerlines) > 0:
        matches = []
        for row in centerlines:
            if row.from_left <= addr_low_num <= row.to_left and row.oeb_left == addr_parity:
                if address.street.predir == row.pre or '' in [address.street.predir, row.pre]:
                    if address.street.postdir == row.post or '' in [address.street.postdir, row.post]:
                        if address.street.suffix == row.suffix or '' in [address.street.suffix, row.suffix]:
                            matches.append(row)
            elif row.from_right <= addr_low_num <= row.to_right and row.oeb_right == addr_parity:
                if address.street.predir == row.pre or '' in [address.street.predir, row.pre]:
                    if address.street.postdir == row.post or '' in [address.street.postdir, row.post]:
                        if address.street.suffix == row.suffix or '' in [address.street.suffix, row.suffix]:
                            matches.append(row)
        # Let's just see if a match to the street name can be made.  If there is only one match, it should be safe to use
        # at this point.  The only difference in logic below from above is that suffixes do not have to match
        # 1018 ALPENA DR - should find RD
        if len(matches) == 0:
            matches = []
            for row in centerlines:
                if row.from_left <= addr_low_num <= row.to_left and row.oeb_left == addr_parity:
                    if address.street.predir == row.pre or '' in [address.street.predir, row.pre]:
                        if address.street.postdir == row.post or '' in [address.street.postidr, row.post]:
                            if (address.street.suffix != '' and address.street.suffix != row.suffix) or '' in [address.street.suffix, row.suffix]:
                                matches.append(row)
                elif row.from_right <= addr_low_num <= row.to_right and row.oeb_right == addr_parity:
                    if address.street.predir == row.pre or '' in [address.street.predir, row.pre]:
                        if address.street.postdir == row.post or '' in [address.street.postdir, row.post]:
                            if (address.street.suffix != '' and address.street.suffix != row.suffix) or '' in [address.street.suffix, row.suffix]:
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

                address.cl_addr_match = match_type
                assign_cl_info(address, match)
                address.geometry = get_address_geom(address, addr_uber=addr_uber, match=match)
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

            address.cl_addr_match = match_type
            assign_cl_info(address, match)
            address.geometry = get_address_geom(address, addr_uber=addr_uber, match=match)
            return

        # need to resolve dir and/or suffix
        if len(matches) > 1:
            address.street.street_code = row.street_code
            address.street.shape = row.shape
            address.cl_addr_match = 'MULTI'  # str(len(matches))
            get_address_geom(address, addr_uber=addr_uber, match=row)
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
        if len(options) > 0 and options[0][0][0] == address.street.name[0] and len(address.street.name) > 3 and \
                        int(options[0][1]) >= 91 and abs(len(address.street.name) - len(options[0][0])) <= 4:
            if len(options) > 1 and options[0][1] == options[1][1]:
                tie_print = addr_uber.input_address + ',' + address.street.name + ',' + options[0][0] + ',' + str(
                    options[0][1]) + ',' + options[1][0] + ',' + str(
                    options[1][1])
                tie = 'Y'
            address.street.name = options[0][0]
            address.street.score = tie + str(options[0][1])
            get_cl_info(address, addr_uber, MAX_RANGE)
            return
    #TODO: Add attempts to match on alias street name w/ and w/o suffix as well as fuzzy matching

# simple method for adding street_code to street_2
def get_cl_info_street2(address):
    # Get matching centerlines based on street name
    centerlines = is_cl_base(address.street_2.full)
    # If there are matches
    if len(centerlines) > 0:
        address.street_2.street_code = centerlines[0].street_code
        address.street_2.shape = centerlines[0].shape
        if address.street.shape and address.street_2.shape:
            get_int_geom(address)
        return


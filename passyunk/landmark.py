import os, sys
import csv
import re
import string
from copy import deepcopy
from fuzzywuzzy import process
from shapely.wkt import loads
from .namestd import StandardName
from .centerline import project_shape, test_file, csv_path
from .data import INPUT_SRID, OUTPUT_SRID, LANDMARK_CENTROID


landmark_file = 'landmarks'
landmark_map = {}

def create_landmark_lookup():
    is_landmark_file = test_file(landmark_file)
    if not is_landmark_file:
        return False
    path = csv_path(landmark_file)
    try:
        with open(path, "r") as f:
            reader = csv.reader(f)
            for row in reader:
                landmark_address = row[1]
                landmark_shape = row[2]
                # Don't match on 'the' as first word
                rlist = row[0].split()
                rlist = rlist[1:] if rlist[0] == 'THE' else rlist
                lname = ' '.join(rlist)
                if not lname in landmark_map:
                    landmark_map[lname] = []
                landmark_map[lname].append([landmark_address, landmark_shape])

    except IOError:
        print('Error opening ' + path, sys.exc_info()[0])
    return True


class Landmark:
    def __init__(self, item):
        self.item = item
        self.landmark_name = ''
        self.landmark_address = ''
        self.landmark_shape = ''
        self.is_landmark = False


    def landmark_check(self, output_srid=OUTPUT_SRID, landmark_centroid=LANDMARK_CENTROID):
        tmp = self.item.strip()
        # Name standardization:
        tmp_list = re.sub('[' + string.punctuation + ']', '', tmp).split()
        tmp_list_copy = deepcopy(tmp_list)
        std = StandardName(tmp_list, False).output
        # Don't match on 'the' if first word
        try:
            tmp = ' '.join(std[1:]) if std[0].upper() in ('THE', 'TEH') else ' '.join(std)
        except:
            tmp = tmp.upper()
        # Fuzzy matching:
        try:
            first_letter = tmp[0]
        except:
            first_letter = ''
        landmark_dict = {k:v for k,v in landmark_map.items() if k[0] == first_letter}
        landmark_list = [x for x in landmark_dict.keys()]
        results = process.extract(tmp, landmark_list, limit=3)
        results = sorted(results, key=lambda r: r[1], reverse=True)
        # If no matches above score, try without standardizations
        if results and results[0][1] <= 89:
            tmp = ' '.join(tmp_list_copy[1:]) if tmp_list_copy[0].upper() in ('THE', 'TEH') else ' '.join(tmp_list_copy)
            results = process.extract(tmp, landmark_list, limit=3)
            results = sorted(results, key=lambda r: r[1], reverse=True)
        try:
            # Don't return landmark if matches duplicate names
            results = [] if results[0][1] == results[1][1] else results
            lname = results[0][0]
            landmark_attr = landmark_dict[lname]
            # Currently only handle uniquely named landmarks
            # landmark_address = landmark_addresses[0] if results[0][1] > 89 and len(landmark_addresses) == 1 else ''
            if results[0][1] > 89:
                landmark_address = landmark_attr[0][0]
                landmark_shape = landmark_attr[0][1]
            else:
                landmark_address = ''
                landmark_shape = ''
            if landmark_address or landmark_shape:
                self.is_landmark = True
                self.landmark_address = landmark_address
                self.landmark_shape = project_shape(loads(landmark_shape), INPUT_SRID, output_srid)
                if landmark_centroid:
                    self.landmark_shape = self.landmark_shape.centroid
                self.landmark_name = lname
        except:
            pass


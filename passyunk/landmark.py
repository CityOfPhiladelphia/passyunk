import os, sys
import csv
import re
import string
from fuzzywuzzy import process
from .namestd import StandardName


class Landmark:
    def __init__(self, item):
        self.item = item
        self.landmark_name = ''
        self.landmark_address = ''
        self.is_landmark = False

    def csv_path(self, file_name):
        cwd = os.path.dirname(__file__)
        cwd += '/pdata'
        return os.path.join(cwd, file_name + '.csv')

    def list_landmarks(self, first_letter):
        path = self.csv_path('landmarks')
        landmark_dict = {}
        try:
            with open(path, 'r') as f:
                reader = csv.reader(f)
                for row in reader:
                    # Don't match on 'the' as first word
                    rlist = row[0].split()
                    rlist = rlist[1:] if rlist[0] == 'THE' else rlist
                    lname = ' '.join(rlist)
                    if lname[0] != first_letter:
                        continue
                    if not lname in landmark_dict:
                        landmark_dict[lname] = []
                    landmark_dict[lname].append(row[1])
        except IOError:
            print('Error opening ' + path, sys.exc_info()[0])
        return landmark_dict

    def landmark_check(self):
        tmp = self.item.strip()
        # Name standardization:
        tmp_list = re.sub('[' + string.punctuation + ']', '', tmp).split()
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

        landmark_dict = self.list_landmarks(first_letter)
        landmark_list = [x for x in landmark_dict.keys()]
        results = process.extract(tmp, landmark_list, limit=3)
        results = sorted(results, key=lambda r: r[1], reverse=True)
        try:
            results = [] if results[0][1] == results[1][1] else results
            lname = results[0][0]
            landmark_addresses = landmark_dict[lname]
            # Currently only handle uniquely named landmarks
            # landmark_address = landmark_addresses[0] if results[0][1] > 89 and len(landmark_addresses) == 1 else ''
            landmark_address = landmark_addresses[0] if results[0][1] > 89 else ''
            self.is_landmark = True if landmark_address else False
            self.landmark_address = landmark_address
            self.landmark_name = lname
        except:
            pass


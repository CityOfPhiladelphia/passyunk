import os, sys
import csv
import re
import string
from fuzzywuzzy import process, fuzz
from .namestd import StandardName


class Landmark:
    def __init__(self, item):
        self.item = item
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
                    rlist = rlist[1:] if rlist[0].lower() == 'the' else rlist
                    # lname = row[0].lower()
                    lname = ' '.join(rlist).lower()
                    if lname[0] != first_letter:
                        continue
                    landmark_dict[lname] = row[1]
        except IOError:
            print('Error opening ' + path, sys.exc_info()[0])
        return landmark_dict

    def landmark_check(self):
        tmp = self.item.strip()
        # Name standardization:
        tmp_list = re.sub('[' + string.punctuation + ']', '', tmp).split()
        std = StandardName(tmp_list, False).output
        # Don't match on 'the' if first word
        tmp = ' '.join(std[1:]) if std[0].lower() in ('the', 'teh') else ' '.join(std)
        # Fuzzy matching:
        first_letter = tmp[0].lower()
        landmark_dict = self.list_landmarks(first_letter)
        landmark_list = [x.lower()[1:] for x in landmark_dict.keys()]
        results = process.extract(tmp.lower()[1:], landmark_list, limit=3)
        results = sorted(results, key=lambda r: r[1], reverse=True)
        try:
            lname = tmp[0].lower() + results[0][0]
            landmark_address = landmark_dict[lname] if results[0][1] > 85 else ''
            self.is_landmark = True if landmark_address else False
            self.landmark_address = landmark_address
        except:
            pass


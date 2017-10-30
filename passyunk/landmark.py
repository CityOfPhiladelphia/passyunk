import os, sys
import csv
import re
import string
from fuzzywuzzy import process
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

    def list_landmarks(self):
        path = self.csv_path('landmarks')
        landmark_dict = {}
        try:
            with open(path, 'r') as f:
                reader = csv.reader(f)
                for row in reader:
                    lname = row[0].lower()
                    landmark_dict[lname] = row[1]
        except IOError:
            print('Error opening ' + path, sys.exc_info()[0])
        return landmark_dict

    def landmark_check(self):
        tmp = self.item.strip()
        # Name standardization:
        tmp_list = re.sub('[' + string.punctuation + ']', '', tmp).split()
        std = StandardName(tmp_list, False).output
        tmp =  ' '.join(std)
        # Fuzzy matching:
        landmark_dict = self.list_landmarks()
        landmark_list = [x.lower()[1:] for x in landmark_dict.keys()]
        result = process.extract(tmp.lower()[1:],landmark_list,limit=1)
        lname = tmp[0].lower() + result[0][0]
        landmark_address = landmark_dict[lname] if result[0][1] > 95 else ''
        self.is_landmark = True if landmark_address else False
        self.landmark_address = landmark_address

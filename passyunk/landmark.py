import os, sys
import csv

class Landmark:
    def __init__(self, item):
        self.item = item
        self.landmark_address = ''
        self.is_landmark = False

    def csv_path(self, file_name):
        cwd = os.path.dirname(__file__)
        cwd += '/pdata'
        return os.path.join(cwd, file_name + '.csv')

    def landmark_check(self):
        tmp = self.item.strip()
        path = self.csv_path('landmarks')
        f = open(path, 'r')
        try:
            reader = csv.reader(f)
            landmark_address = ''
            for row in reader:
                landmark_name = row[0]
                if tmp.lower() == landmark_name.lower():
                    landmark_address = row[1]
                    break
            self.is_landmark = True if landmark_address else False
            self.landmark_address = landmark_address
            # return laddress
        except IOError:
            print('Error opening ' + path, sys.exc_info()[0])
        f.close()
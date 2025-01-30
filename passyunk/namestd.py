import os, sys
import csv
from .parser_addr import namestd_lookup

class StandardName:
    def __init__(self, tokens, do_ordinal):
        # print(' '.join(self.name_std(tokens, False)))
        # self.tokens = tokens
        self.output = self.name_std(tokens, do_ordinal)


    class Namestd:
        def __init__(self, row):
            self.correct = row[0]
            self.common = row[1]


    class AddrOrdinal:
        def __init__(self, row):
            self.ordigit = row[0]
            self.orsuffix = row[1]


    def csv_path(self, file_name):
        cwd = os.path.dirname(__file__)
        cwd += '/pdata'
        return os.path.join(cwd, file_name + '.csv')

    # This is run on parser initialization and imported above as namestd_lookup
    def createnamestdlookup(self):
        path = self.csv_path('std')
        with open(path, 'r') as f:
            lookup = {}
            try:
                reader = csv.reader(f)
                for row in reader:
                    r = self.Namestd(row)
                    lookup[r.common] = r
            except IOError:
                print('Error opening ' + path, sys.exc_info()[0])
        return lookup


    def is_name_std(self, test):
        try:
            nstd = namestd_lookup[test]
        except KeyError:
            row = ['', test]
            nstd = self.Namestd(row)
        # print("nstd: ", nstd.common)
        return nstd


    def create_ordinal_lookup(self):
        lookup = {}
        r = self.AddrOrdinal(['1', 'ST'])
        lookup[r.ordigit] = r
        r = self.AddrOrdinal(['11', 'TH'])
        lookup[r.ordigit] = r
        r = self.AddrOrdinal(['2', 'ND'])
        lookup[r.ordigit] = r
        r = self.AddrOrdinal(['12', 'TH'])
        lookup[r.ordigit] = r
        r = self.AddrOrdinal(['3', 'RD'])
        lookup[r.ordigit] = r
        r = self.AddrOrdinal(['13', 'TH'])
        lookup[r.ordigit] = r
        r = self.AddrOrdinal(['4', 'TH'])
        lookup[r.ordigit] = r
        r = self.AddrOrdinal(['5', 'TH'])
        lookup[r.ordigit] = r
        r = self.AddrOrdinal(['6', 'TH'])
        lookup[r.ordigit] = r
        r = self.AddrOrdinal(['7', 'TH'])
        lookup[r.ordigit] = r
        r = self.AddrOrdinal(['8', 'TH'])
        lookup[r.ordigit] = r
        r = self.AddrOrdinal(['9', 'TH'])
        lookup[r.ordigit] = r
        r = self.AddrOrdinal(['0', 'TH'])
        lookup[r.ordigit] = r

        return lookup


    def add_ordinal(self, string):
        if string == '0' or string == '00' or string == '000':
            return string

        if len(string[0]) > 1:
            lastchar = string[0][-2:]
            try:
                ordinal = self.add_ordinal_lookup[lastchar]
                if len(string) > 1 and ordinal.orsuffix == string[1]:
                    string.pop()
                string[0] = string[0] + ordinal.orsuffix
                return string
            except Exception:
                pass

        lastchar = string[0][-1:]

        try:
            ordinal = self.add_ordinal_lookup[lastchar]
            string[0] = string[0] + ordinal.orsuffix
            return string
        except Exception:
            pass

        return string


    def name_std(self, tokens, do_ordinal):
        i = len(tokens)
        while i > 0:
            j = 0
            while j + i <= len(tokens):
                nstd = self.is_name_std(' '.join(tokens[j:j + i]))
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
            temp = self.add_ordinal(temp)
            temp = self.name_std(temp, True)

        return temp

# test = ['1234', 'MKT', 'ST']
# std = StandardName(test, False).output
# print(std)
import csv,sys,os
import time
from passyunk.parser import PassyunkParser

import csv
import sys
import os
import re

__author__ = 'tom.swanson'
infile = 'uspszip4'
outfile = 'uspszip4c'

cwd = os.path.dirname(__file__)


def csv_path(file_name):
    return os.path.join(cwd, file_name + '.csv')

zip4_list = []

class Zip4s:
    def __init__(self, row):
        self.base = row[0]
        self.pre = row[1]
        self.name = row[2]
        self.suffix = row[3]
        self.post = row[4]
        self.low = row[5]
        self.high = row[6]
        self.oeb = row[7]
        self.unit = row[8]
        self.unitlow = row[9]
        self.unithigh = row[10]
        self.unitoeb = row[11]
        self.buildingorfirm = row[12]
        self.recordtype = row[13]
        self.zipcode = row[14]
        self.zip4 = row[15]

def read_zip4():
    path = csv_path(infile)
    f = open(path, 'r')
    i = 0

    try:
        reader = csv.reader(f)

        for row in reader:
            if i == 0:
                i+=1
                continue
            r = Zip4s(row)
            parse_me = '%s %s %s %s %s' % (r.low,r.pre,r.name,r.suffix,r.post)
            try:
                p = parser.parse(parse_me)
                r.pre = p['components']['street']['predir']
                r.name = p['components']['street']['name']
                r.suffix = p['components']['street']['suffix']
                r.post = p['components']['street']['postdir']
                if r.pre == None:
                    r.pre =''
                if r.name == None:
                    r.name =''
                if r.suffix == None:
                    r.suffix =''
                if r.post == None:
                    r.post =''

            except:
                print('Parser Error: ' + parse_me)
                continue

            zip4_list.append(r)

            i += 1

    except IOError:
        print('Error opening ' + path, sys.exc_info()[0])
    f.close()
    return

def write_zip4s():
    path = csv_path(outfile)
    f = open(path, 'w')
    i = 0

    try:
        for self in zip4_list:
            tmp = '%s %s %s %s' % (self.pre,self.name,self.suffix,self.post)
            tmp = ' '.join(tmp.split())
            out = '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' %   (tmp,self.pre,self.name,self.suffix,
                                                                           self.post,self.low,self.high,self.oeb,self.unit,
                                                                           self.unitlow,self.unithigh,self.unitoeb,
                                                                           self.buildingorfirm,self.recordtype,self.zipcode,self.zip4)
            f.writelines(out)
            i += 1

    except IOError:
        print('Error opening ' + path, sys.exc_info()[0])
    f.close()
    return

parser = PassyunkParser()
read_zip4()
write_zip4s()
"""
USPS ZIP4 and CityState table parser and export to csv

Author: Tom Swanson

Created: 12/26/2014
Last Updated: 6/20/2016


Version: 1.0

Arguments: none
"""

# where each month's data is located.
import re
import csv
import os
from collections import OrderedDict
import petl as etl
import cx_Oracle
import boto3
from passyunk.parser import PassyunkParser
from config import get_dsn

month = '2018_01'
parser = PassyunkParser()

# Input locations
loc = r'C:/Projects/etl/data/usps/'
csbyst = '/pa.txt'
zip4 = '/pa'

# Output params
s3_bucket = 'elasticbeanstalk-us-east-1-676612114792'
alias_outfile_path = 'usps_alias.csv'
cityzip_outfile_path = 'usps_cityzip.csv'
zip4_outfile_path = 'uspszip4.csv'
temp_zip4_outfile_path = 't_uspszip4.csv'
dsn = get_dsn('ais_dev')
connection = cx_Oracle.Connection(dsn)
#####################################
# Meta:

zip3s = ['190', '191', '192']
zips = ['19019',
        '19092',
        '19093',
        '19101',
        '19102',
        '19103',
        '19104',
        '19105',
        '19106',
        '19107',
        '19108',
        '19109',
        '19110',
        '19111',
        '19112',
        '19113',
        '19114',
        '19115',
        '19116',
        '19118',
        '19119',
        '19120',
        '19121',
        '19122',
        '19123',
        '19124',
        '19125',
        '19126',
        '19127',
        '19128',
        '19129',
        '19130',
        '19131',
        '19132',
        '19133',
        '19134',
        '19135',
        '19136',
        '19137',
        '19138',
        '19139',
        '19140',
        '19141',
        '19142',
        '19143',
        '19144',
        '19145',
        '19146',
        '19147',
        '19148',
        '19149',
        '19150',
        '19151',
        '19152',
        '19153',
        '19154',
        '19155',
        '19160',
        '19161',
        '19162',
        '19170',
        '19171',
        '19172',
        '19175',
        '19176',
        '19178',
        '19181',
        '19182',
        '19187',
        '19188',
        '19190',
        '19191',
        '19192',
        '19195',
        '19196',
        '19197',
        '19244',
        '19255',
        ]

alias_header = ['objectid', 'zipcode', 'aliaspre', 'aliasname', 'aliassuff', 'aliaspost', 'streetpre', 'streetname',
                'street', 'post', 'aliastype', 'aliasdate', 'aliasrangelow', 'aliasrangehigh', 'aliasoeb', 'alias_unknown']

cityzip_header = ['objectid', 'zipcode', 'citystate_key', 'zipclassificationcode', 'cityname', 'cityabbrname', 'faccode',
                  'mailingindicator', 'prefcitystatekey', 'prefcityname', 'citydelivery', 'crsortindicator', 'uniq',
                  'financenum', 'state', 'fips', 'county']

zip4_header = ['objectid', 'zipcode', 'updatekey', 'actioncode', 'recordtype', 'pcr', 'streetpre',
               'streetname', 'streetsuff', 'streetpost', 'addrlow', 'addrhigh', 'addroeb', 'buildingorfirm',
               'addrsecondaryabbr', 'addrsecondarylow', 'addrsecondaryhigh', 'adrsecondaryoeb', 'zip4low',
               'zip4high', 'basealt', 'lacs', 'govtbldg', 'financeno', 'state', 'countyfips', 'congressno',
               'munikey', 'urbankey', 'preflastline']

zip4_mapping = OrderedDict([
    ('base', 'basealt'),
    ('pre', 'streetpre'),
    ('name', 'streetname'),
    ('suffix', 'streetsuff'),
    ('post', 'streetpost'),
    ('low', 'addrlow'),
    ('high', 'addrhigh'),
    ('oeb', 'addroeb'),
    ('unit', 'addrsecondaryabbr'),
    ('unitlow', 'addrsecondarylow'),
    ('unithigh', 'addrsecondaryhigh'),
    ('unitoeb', 'adrsecondaryoeb'),
    ('buildingorfirm', 'buildingorfirm'),
    ('recordtype', 'recordtype'),
    ('zipcode', 'zipcode'),
    ('zip4', 'zip4low')
])
#################################################
# Utils:

def standardize_nulls(val):
    if type(val) == str:
        return None if val.strip() == '' else val
    else:
        return None if val == 0 else val


class CursorProxy(object):
    def __init__(self, cursor):
        self._cursor = cursor

    def executemany(self, statement, parameters, **kwargs):
        # convert parameters to a list
        parameters = list(parameters)
        # pass through to proxied cursor
        return self._cursor.executemany(statement, parameters, **kwargs)

    def __getattr__(self, item):
        return getattr(self._cursor, item)


def get_cursor():
    return CursorProxy(connection.cursor())

###################################################
# Declarations:
alias_id = 0
city_id = 0
zip4_id = 0
alias_rows = []
cityzip_rows = []
zip4_rows = []
###################################################
# Start:
csbyst_f = open(loc + month + csbyst, 'r')
while True:
    ch = csbyst_f.read(129)
    if not ch:
        break
    # Copyright record
    if ch[0] == 'C':
        print(ch[19:24])
    # Alias
    if ch[0] == 'A' and ch[1:6] in zips:
        zipcode = ch[1:6]
        aliaspre = ch[6:8].strip()
        aliasname = ch[8:36].strip()
        aliassuff = ch[36:40].strip()
        aliaspost = ch[40:42].strip()
        streetpre = ch[42:44].strip()
        streetname = ch[44:72].strip()
        street = ch[72:76].strip()
        post = ch[76:78].strip()
        aliastype = ch[78].strip()
        aliasdate = ch[79:87].strip()
        aliasrangelow = ch[87:97].strip()
        aliasrangehigh = ch[97:107].strip()
        aliasoeb = ch[107].strip()
        alias_unknown = ch[108].strip()
        alias_id += 1

        row = {'objectid': alias_id, 'zipcode': zipcode, 'aliaspre': aliaspre, 'aliasname': aliasname, 'aliassuff': aliassuff,
               'aliaspost': aliaspost, 'streetpre': streetpre, 'streetname': streetname, 'street': street, 'post': post,
               'aliastype': aliastype, 'aliasdate': aliasdate, 'aliasrangelow': aliasrangelow.lstrip('0'), 'aliasrangehigh': aliasrangehigh.lstrip('0'),
               'aliasoeb': aliasoeb, 'alias_unknown': alias_unknown}

        alias_rows.append(row)

    # Detail
    if ch[0] == 'D':
        if ch[104:129].strip() == 'PHILADELPHIA' or ch[41:54].strip() == 'PHILADELPHIA' or ch[62:90].strip() == \
                'PHILADELPHIA' or ch[104:129].strip() == 'PHILA' or ch[41:54].strip() == 'PHILA' or ch[62:90].strip() == \
                'PHILA':
            zipcode = ch[1:6]
            citystate_key = ch[6:12].strip()
            zipclassificationcode = ch[12].strip()
            cityname = ch[13:41].strip()
            cityabbrname = ch[41:54].strip()
            faccode = ch[54].strip()
            mailingindicator = ch[55].strip()
            prefcitystatekey = ch[56:62].strip()
            prefcityname = ch[62:90].strip()
            citydelivery = ch[90].strip()
            crsortindicator = ch[91].strip()
            uniq = ch[92].strip()
            financenum = ch[93:99].strip()
            state = ch[99:101].strip()
            fips = ch[101:104].strip()
            county = ch[104:129].strip()
            city_id += 1

            row = {'objectid': city_id, 'zipcode': zipcode, 'citystate_key': citystate_key,
                   'zipclassificationcode': zipclassificationcode,
                   'cityname': cityname, 'cityabbrname': cityabbrname, 'faccode': faccode,
                   'mailingindicator': mailingindicator, 'prefcitystatekey': prefcitystatekey,
                   'prefcityname': prefcityname, 'citydelivery': citydelivery, 'crsortindicator': crsortindicator,
                   'uniq': uniq, 'financenum': financenum, 'state': state, 'fips': fips, 'county': county}

            cityzip_rows.append(row)

    # Seasonal
    if ch[0] == 'N' and ch[1:6] in zips:
        print(ch)
    # PO ZIPCodes
    if ch[0] == 'P' and ch[1:6] in zips:
        print(ch)
    # Zone Splits
    if ch[0] == 'Z' and ch[1:6] in zips:
        print("Zone Split")
        print(ch)

conv_dict = {'one': 1, 'two': 2}

for zip3 in zip3s:
    print(loc + month + zip4 + '/' + zip3 + '.txt')
    f = open(loc + month + zip4 + '/' + zip3 + '.txt', 'r')

    while True:
        ch = f.read(182)
        if not ch:
            break
        if ch[0] == 'C':
            print(ch[19:24])
        if ch[0] == 'D' and ch[1:6] in zips:
            zipcode = ch[1:6]
            updatekey = ch[6:16].strip()
            actioncode = ch[16].strip()
            recordtype = ch[17].strip()
            pcr = ch[18:22].strip()
            streetpre = ch[22:24].strip()
            streetname = ch[24:52].strip()
            streetsuff = ch[52:56].strip()
            streetpost = ch[56:58].strip()
            addrlow = ch[58:68].strip()
            addrhigh = ch[68:78].strip()
            addroeb = ch[78].strip()
            buildingorfirm = ch[79:119].strip()
            addrsecondaryabbr = ch[119:123].strip()
            addrsecondarylow = ch[123:131].strip()
            addrsecondaryhigh = ch[131:139].strip()
            addrsecondaryoeb = ch[139].strip()
            zip4low = ch[140:144].strip()
            zip4high = ch[144:148].strip()
            basealt = ch[148].strip()
            lacs = ch[149].strip()
            govtbldg = ch[150].strip()
            financeno = ch[151:157].strip()
            state = ch[157:159].strip()
            countyfips = ch[159:162].strip()
            congressno = ch[162:164].strip()
            munikey = ch[164:170].strip()
            urbankey = ch[170:176].strip()
            preflastline = ch[176:182].strip()

            zip4_id += 1
            if addrlow in conv_dict:
                addrlow = conv_dict

            if addrhigh in conv_dict:
                addrhigh = conv_dict

            addrlow = re.sub('\D', '', addrlow)
            addrhigh = re.sub('\D', '', addrhigh)

            row = {'objectid': zip4_id, 'zipcode': zipcode, 'updatekey': updatekey, 'actioncode': actioncode,
                   'recordtype': recordtype, 'pcr': pcr, 'streetpre': streetpre, 'streetname': streetname,
                   'streetsuff': streetsuff, 'streetpost': streetpost, 'addrlow': addrlow.lstrip('0'),
                   'addrhigh': addrhigh.lstrip('0'), 'addroeb': addroeb, 'buildingorfirm': buildingorfirm,
                   'addrsecondaryabbr': addrsecondaryabbr, 'addrsecondarylow': addrsecondarylow.lstrip('0'),
                   'addrsecondaryhigh': addrsecondaryhigh.lstrip('0'), 'adrsecondaryoeb': addrsecondaryoeb,
                   'zip4low': zip4low, 'zip4high': zip4high, 'basealt': basealt, 'lacs': lacs, 'govtbldg': govtbldg,
                   'financeno': financeno, 'state': state, 'countyfips': countyfips, 'congressno': congressno,
                   'munikey': munikey, 'urbankey': urbankey, 'preflastline': preflastline}

            zip4_rows.append(row)


csbyst_f.close()
f.close()
########################################
# Write:
with open(alias_outfile_path, 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=alias_header)
    writer.writeheader()
    for row in alias_rows:
        writer.writerow(row)

with open(cityzip_outfile_path, 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=cityzip_header)
    writer.writeheader()
    for row in cityzip_rows:
        writer.writerow(row)

with open(temp_zip4_outfile_path, 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=zip4_header)
    writer.writeheader()
    for row in zip4_rows:
        writer.writerow(row)

#####################################
# Create zip4 address standardization report:
print("Writing address standardization report")
zip4_table = etl.fromcsv(temp_zip4_outfile_path)
processed_rows = zip4_table.fieldmap(zip4_mapping) \
    .addfield('addr_comps', lambda a: [a['low'], a['pre'], a['name'], a['suffix'], a['post']]) \
    .addfield('concat', lambda c: ' '.join(filter(None, c['addr_comps']))) \
    .addfield('parsed_comps', lambda p: parser.parse(p['concat'])) \
    .addfield('street_full', lambda a: a['parsed_comps']['components']['street']['full']) \
    .addfield('std_base', lambda a: a['parsed_comps']['components']['base_address']) \
    .addfield('std_pre', lambda a: a['parsed_comps']['components']['street']['predir']) \
    .addfield('std_name', lambda a: a['parsed_comps']['components']['street']['name']) \
    .addfield('std_suffix', lambda a: a['parsed_comps']['components']['street']['suffix']) \
    .addfield('std_post', lambda a: a['parsed_comps']['components']['street']['postdir']) \
    .addfield('std_low', lambda a: a['parsed_comps']['components']['address']['low']) \
    .addfield('std_high', lambda a: a['parsed_comps']['components']['address']['high']) \
    .addfield('std_unit', lambda a: a['parsed_comps']['components']['address_unit']['unit_type']) \
    .addfield('change_pre', lambda a: 1 if str(standardize_nulls(a['pre'])) != str(
    standardize_nulls(a['std_pre'])) else None) \
    .addfield('change_name', lambda a: 1 if str(standardize_nulls(a['name'])) != str(
    standardize_nulls(a['std_name'])) else None) \
    .addfield('change_suffix', lambda a: 1 if str(standardize_nulls(a['suffix'])) != str(
    standardize_nulls(a['std_suffix'])) else None) \
    .addfield('change_post', lambda a: 1 if str(standardize_nulls(a['post'])) != str(
    standardize_nulls(a['std_post'])) else None) \
    .addfield('change_low', lambda a: 1 if str(standardize_nulls(a['low'])) != str(
    standardize_nulls(a['std_low'])) else None) \
    .addfield('change_high', lambda a: 1 if str(standardize_nulls(a['high'])) != str(
    standardize_nulls(a['std_high'])) else None) \
    .addfield('change_unit', lambda a: 1 if str(standardize_nulls(a['unit'])) != str(
    standardize_nulls(a['std_unit'])) else None) \
    .cutout('addr_comps', 'parsed_comps', 'concat')

print(etl.look(processed_rows))
# Write address standardization report to DB:
etl.todb(processed_rows, get_cursor, 'USPS_ZIP4_ADDRESS_CHECK')

# Write processed_rows to uspszip4.csv:
print("Writing cleaned_usps output to uspszip4.csv")
etl.cutout(processed_rows, 'base', 'pre', 'name', 'suffix', 'post', 'change_pre', 'change_name', 'change_suffix', 'change_post') \
        .rename({'std_base': 'base', 'std_pre': 'pre', 'std_name': 'name', 'std_suffix': 'suffix', 'std_post': 'post'}) \
        .cut('street_full', 'pre', 'name', 'suffix', 'post', 'low', 'high', 'oeb', 'unit', 'unitlow', 'unithigh', 'unitoeb', 'buildingorfirm', 'recordtype', 'zipcode',	'zip4') \
        .convert('low', int) \
        .select("{low} is not None") \
        .sort(key=['name', 'pre', 'suffix', 'post', 'low', 'high', 'unit', 'unitlow', 'unithigh']) \
        .tocsv(zip4_outfile_path, write_header=False)

# Write processed_rows to s3:
print("Writing uspszip4.csv to s3")
# s3 = boto3.resource('s3', config=Config(proxies={'http': os.environ['HTTP_PROXY'], 'https': os.environ['HTTPS_PROXY']}))
s3 = boto3.resource('s3')
s3.meta.client.upload_file(zip4_outfile_path, s3_bucket, 'static files/' + zip4_outfile_path)

# Clean up:
os.remove(temp_zip4_outfile_path)
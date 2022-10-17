from collections import OrderedDict

# Input locations
ZIP_FOLDER = 'zip4byst.tar'
FOLDER = 'zip4byst'
CSBYST = FOLDER + '/csbyst/pa'
ZIP4 = FOLDER + '/zip4/pa'

# Output locations
ZIP4_WRITE_TABLE_NAME = 'USPS_ZIP4S'
CITYZIP_WRITE_TABLE_NAME = 'USPS_CITYZIP'
ALIAS_WRITE_TABLE_NAME = 'USPS_ALIAS'
ADDRESS_STANDARDIZATION_REPORT_TABLE_NAME = 'USPS_ZIP4_ADDRESS_CHECK'
ALIAS_OUTFILE_PATH = ALIAS_WRITE_TABLE_NAME.lower() + '.csv'
CITYZIP_OUTFILE_PATH = CITYZIP_WRITE_TABLE_NAME.lower() + '.csv'
ZIP4_OUTFILE_PATH = ZIP4_WRITE_TABLE_NAME.lower() + '.csv'
TEMP_ZIP4_OUTFILE_PATH = 'T_' + ZIP4_OUTFILE_PATH
S3_BUCKET = 'ais-static-files'

# Meta:
ZIP3S = ['190', '191', '192']
ZIPS = ['19019',
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

ALIAS_HEADER = ['objectid', 'zipcode', 'aliaspre', 'aliasname', 'aliassuff', 'aliaspost', 'streetpre', 'streetname',
                'street', 'post', 'aliastype', 'aliasdate', 'aliasrangelow', 'aliasrangehigh', 'aliasoeb', 'alias_unknown']

CITYZIP_HEADER = ['objectid', 'zipcode', 'citystate_key', 'zipclassificationcode', 'cityname', 'cityabbrname', 'faccode',
                'mailingindicator', 'prefcitystatekey', 'prefcityname', 'citydelivery', 'crsortindicator', 'uniq',
                'financenum', 'state', 'fips', 'county']

ZIP4_HEADER = ['objectid', 'zipcode', 'updatekey', 'actioncode', 'recordtype', 'pcr', 'streetpre',
            'streetname', 'streetsuff', 'streetpost', 'addrlow', 'addrhigh', 'addroeb', 'buildingorfirm',
            'addrsecondaryabbr', 'addrsecondarylow', 'addrsecondaryhigh', 'addrsecondaryoeb', 'zip4low',
            'zip4high', 'basealt', 'lacs', 'govtbldg', 'financeno', 'state', 'countyfips', 'congressno',
            'munikey', 'urbankey', 'preflastline']

ZIP4_MAPPING = OrderedDict([
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
    ('unitoeb', 'addrsecondaryoeb'),
    ('buildingorfirm', 'buildingorfirm'),
    ('recordtype', 'recordtype'),
    ('zipcode', 'zipcode'),
    ('zip4', 'zip4low')
])

# Miscellaneous
CONV_DICT = {'one': 1, 'two': 2}
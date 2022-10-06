import re
import csv
import os
import sys
import petl as etl
import boto3
import zipfile
import tarfile
import click
# CityGeo:
import oracle_code
import usps_epf
import utils as util
import config as conf
from passyunk.parser import PassyunkParser

def get_zip_file(creds: dict): 
    with usps_epf.Usps_Epf(creds['user'], creds['password']) as epf: 
        print(epf.get_list())
        epf.set_status('7108662', 'N') # Don't forget to remove this
        newest = epf.get_newest()
        if newest == None: 
            print('No new files found, exiting')
            sys.exit()
    
    with open(conf.ZIP_FOLDER, 'wb') as f: 
        f.write(newest.content)

def extract_files(creds: dict):
    with tarfile.open(conf.ZIP_FOLDER, 'r') as tar: 
        tar.extractall()

    folder_password = bytes(creds['folder_password'], encoding='utf-8') # Must be bytes
    with zipfile.ZipFile(conf.CSBYST + '.zip', 'r') as zip: 
        zip.extractall(path=conf.CSBYST, pwd=folder_password)
    with zipfile.ZipFile(conf.ZIP4 + '.zip', 'r') as zip: 
        zip.extractall(path=conf.ZIP4, pwd=folder_password)

def write_csv(filename: str, fieldnames: str, data: list): 
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)

def todb_loop(all_data, db_conn, tablename, commit): 
    # Without using this function, was receiving error: DPI-1015: array size of 157971 is too large
    start_pos = 0
    batch_size = 15000

    while start_pos < len(all_data):
        data = all_data[start_pos:start_pos + batch_size]
        start_pos += batch_size
        etl.todb(table=data, dbo=util.get_cursor(db_conn), 
            tablename=tablename, commit=commit)

def process_csbyst(): 
    alias_id = 0
    city_id = 0
    alias_rows = []
    cityzip_rows = []

    with open(conf.CSBYST + '/pa.txt', 'r') as csbyst_f: 
        while True:
            ch = csbyst_f.read(129)
            if not ch:
                break
            # Copyright record
            if ch[0] == 'C':
                print(ch[19:24])
            # Alias
            if ch[0] == 'A' and ch[1:6] in conf.ZIPS:
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
            if ch[0] == 'N' and ch[1:6] in conf.ZIPS:
                print(ch)
            # PO ZIPCodes
            if ch[0] == 'P' and ch[1:6] in conf.ZIPS:
                print(ch)
            # Zone Splits
            if ch[0] == 'Z' and ch[1:6] in conf.ZIPS:
                print("Zone Split")
                print(ch)
    # Why bother writing the list to CSV when you could write each row automatically or read the list into PETL?
    write_csv(conf.ALIAS_OUTFILE_PATH, conf.ALIAS_HEADER, alias_rows)
    write_csv(conf.CITYZIP_OUTFILE_PATH, conf.CITYZIP_HEADER, cityzip_rows)

def process_zip4(): 
    zip4_id = 0
    zip4_rows = []
    
    for zip3 in conf.ZIP3S:
        print(conf.ZIP4 + '/' + zip3 + '.txt')
        with open(conf.ZIP4 + '/' + zip3 + '.txt', 'r') as f: 
            while True:
                ch = f.read(182)
                if not ch:
                    break
                if ch[0] == 'C':
                    print(ch[19:24])
                if ch[0] == 'D' and ch[1:6] in conf.ZIPS:
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
                    if addrlow in conf.CONV_DICT:
                        addrlow = conf.CONV_DICT

                    if addrhigh in conf.CONV_DICT:
                        addrhigh = conf.CONV_DICT

                    addrlow = re.sub('\D', '', addrlow)
                    addrhigh = re.sub('\D', '', addrhigh)

                    row = {'objectid': zip4_id, 'zipcode': zipcode, 'updatekey': updatekey, 'actioncode': actioncode,
                        'recordtype': recordtype, 'pcr': pcr, 'streetpre': streetpre, 'streetname': streetname,
                        'streetsuff': streetsuff, 'streetpost': streetpost, 'addrlow': addrlow.lstrip('0'),
                        'addrhigh': addrhigh.lstrip('0'), 'addroeb': addroeb, 'buildingorfirm': buildingorfirm,
                        'addrsecondaryabbr': addrsecondaryabbr, 'addrsecondarylow': addrsecondarylow.lstrip('0'),
                        'addrsecondaryhigh': addrsecondaryhigh.lstrip('0'), 'addrsecondaryoeb': addrsecondaryoeb,
                        'zip4low': zip4low, 'zip4high': zip4high, 'basealt': basealt, 'lacs': lacs, 'govtbldg': govtbldg,
                        'financeno': financeno, 'state': state, 'countyfips': countyfips, 'congressno': congressno,
                        'munikey': munikey, 'urbankey': urbankey, 'preflastline': preflastline}

                    zip4_rows.append(row)

    write_csv(conf.TEMP_ZIP4_OUTFILE_PATH, conf.ZIP4_HEADER, zip4_rows)

def zip4_address_standardization(
    db_creds_filepath: str, standardize_addr: bool, commit: bool): 

    db_creds = util.get_creds(db_creds_filepath, ['GIS_AIS'])
    db_conn = oracle_code.connect_to_db(db_creds) 
    parser = PassyunkParser()
    print("Making address standardization report...")
    zip4_table = etl.fromcsv(conf.TEMP_ZIP4_OUTFILE_PATH)
    processed_rows = zip4_table.fieldmap(conf.ZIP4_MAPPING) \
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
        .addfield('change_pre', 
            lambda a: 1 
            if str(util.standardize_nulls(a['pre'])) != str(util.standardize_nulls(a['std_pre'])) 
            else None) \
        .addfield('change_name', 
			lambda a: 1 
			if str(util.standardize_nulls(a['name'])) != str(util.standardize_nulls(a['std_name'])) 
			else None) \
        .addfield('change_suffix', 
			lambda a: 1 
			if str(util.standardize_nulls(a['suffix'])) != str(util.standardize_nulls(a['std_suffix'])) 
			else None) \
        .addfield('change_post', 
			lambda a: 1 
			if str(util.standardize_nulls(a['post'])) != str(util.standardize_nulls(a['std_post'])) 
			else None) \
        .addfield('change_low', 
			lambda a: 1 
			if str(util.standardize_nulls(a['low'])) != str(util.standardize_nulls(a['std_low'])) 
			else None) \
        .addfield('change_high', 
			lambda a: 1 
			if str(util.standardize_nulls(a['high'])) != str(util.standardize_nulls(a['std_high'])) 
			else None) \
        .addfield('change_unit', 
			lambda a: 1 
			if str(util.standardize_nulls(a['unit'])) != str(util.standardize_nulls(a['std_unit'])) 
			else None) \
        .cutout('addr_comps', 'parsed_comps', 'concat')

    print(etl.look(processed_rows))
    print(f"{'' if (standardize_addr and commit) else 'NOT '}Writing Standardization Report to Databridge...")
    if standardize_addr: 
        todb_loop(
            all_data=processed_rows, db_conn=db_conn, 
            tablename=conf.ADDRESS_STANDARDIZATION_REPORT_TABLE_NAME, 
            commit=commit)
    
    # Write processed_rows to uspszip4.csv:
    print(f"Writing cleaned_usps output to {conf.ZIP4_OUTFILE_PATH}")
    etl.cutout(processed_rows, 'base', 'pre', 'name', 'suffix', 'post', 'change_pre', 'change_name', 'change_suffix', 'change_post') \
            .rename({'std_base': 'base', 'std_pre': 'pre', 'std_name': 'name', 'std_suffix': 'suffix', 'std_post': 'post'}) \
            .cut('street_full', 'pre', 'name', 'suffix', 'post', 'low', 'high', 'oeb', 'unit', 'unitlow', 'unithigh', 'unitoeb', 'buildingorfirm', 'recordtype', 'zipcode',	'zip4') \
            .convert('low', int) \
            .select("{low} is not None") \
            .sort(key=['name', 'pre', 'suffix', 'post', 'low', 'high', 'unit', 'unitlow', 'unithigh']) \
            .tocsv(conf.ZIP4_OUTFILE_PATH, write_header=False)

    # Write processed_rows to s3:
    print(f"Writing {conf.ZIP4_OUTFILE_PATH} to s3")
    s3 = boto3.resource('s3')
    s3.meta.client.upload_file(conf.ZIP4_OUTFILE_PATH, conf.S3_BUCKET, conf.ZIP4_OUTFILE_PATH)

def write_out(db_creds_filepath: str, commit: bool): 
    print("Writing tables to Databridge...")
    db_creds = util.get_creds(db_creds_filepath, ['GIS_AIS_SOURCES'])
    db_conn = oracle_code.connect_to_db(db_creds) 
    
    # zip4:
    zip4 = etl.fromcsv(conf.TEMP_ZIP4_OUTFILE_PATH)
    todb_loop(all_data=zip4, db_conn=db_conn, 
        tablename=conf.ZIP4_WRITE_TABLE_NAME, commit=commit)
    # cityzip:
    cityzip = etl.fromcsv(conf.CITYZIP_OUTFILE_PATH)
    todb_loop(all_data=cityzip, db_conn=db_conn, 
        tablename=conf.CITYZIP_WRITE_TABLE_NAME, commit=commit)
    # alias:
    alias = etl.fromcsv(conf.ALIAS_OUTFILE_PATH)
    todb_loop(all_data=alias, db_conn=db_conn, 
        tablename=conf.ALIAS_WRITE_TABLE_NAME, commit=commit)
    
    print(f"Tables {'' if commit else 'NOT '}committed")

@click.command()
@click.option('--api_creds_filepath', help='USPS EPF API JSON Credentials Path')
@click.option('--db_creds_filepath', help='Database JSON Credentials Path')
@click.option('--no_download', is_flag=True, default=False, help='Skip downloading files (must be present and extracted locally)')
@click.option('--standardize_addr', is_flag=True, default=False, show_default=True, 
    help='Write Address Standardization Report to Databridge')
@click.option('--commit/--no_commit', default=True, show_default=True, 
    help='Commit tables to Databridge')
def main(api_creds_filepath, db_creds_filepath, no_download, standardize_addr, commit): 
    if not no_download: 
        api_creds = util.get_creds(api_creds_filepath, ['USPS_EPF'])
        get_zip_file(api_creds)
        extract_files(api_creds)

    process_csbyst()
    process_zip4()
    zip4_address_standardization(db_creds_filepath, standardize_addr, commit)
    write_out(db_creds_filepath, commit)
    
    # Clean up:
    for file in [conf.TEMP_ZIP4_OUTFILE_PATH, conf.FOLDER, conf.ZIP_FOLDER]: 
        os.remove(file)

if __name__ == '__main__': 
    main()
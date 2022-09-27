'''
This refreshes the centerline.csv and centerline_streets.csv from scratch (no alias).
Author: Alex Waldman
Revisions: James Midkiff
'''
import re
import string
import petl as etl
import utils as util
import oracle_code
from passyunk.namestd import StandardName

db_creds = util.get_creds("/scripts/passyunk_automation/passyunk/pdata/oracle.json", ['GIS_STREETS'])
dbo = oracle_code.connect_to_db(db_creds) 
street_centerline_table_name = 'gis_streets.street_centerline'
centerline_csv = 'centerline.csv'
centerline_streets_csv = 'centerline_streets.csv'

def concat_streetname(row):
    predir = row['PRE_DIR']
    st_name = row['ST_NAME']
    st_type = row['ST_TYPE']
    postdir = row['POST_DIR']

    stnam_list = filter(None, [predir, st_name, st_type, postdir])
    return ' '.join(stnam_list)

def standardize_name(name):
    tmp = name.strip()
    # Name standardization:
    tmp_list = re.sub('[' + string.punctuation + ']', '', tmp).split()
    std = StandardName(tmp_list, False).output
    std_name = ' '.join(std)
    return std_name

centerline_stmt = f'''
select trim(PRE_DIR) AS PRE_DIR, trim(ST_NAME) AS ST_NAME, trim(ST_TYPE) AS ST_TYPE, 
    trim(SUF_DIR) AS POST_DIR, L_F_ADD, L_T_ADD, R_F_ADD, R_T_ADD, ST_CODE, SEG_ID, 
    trim(RESPONSIBL) AS RESPONSIBL 
from {street_centerline_table_name} 
order by st_name, st_type, pre_dir, suf_dir, l_f_add, l_t_add, r_f_add, r_t_add, 
    st_code, seg_id
'''

centerline_rows = etl.fromdb(dbo, centerline_stmt).convert('ST_NAME', lambda s: standardize_name(s))

print(etl.look(centerline_rows))
centerline_rows.tocsv(centerline_csv)

# Centerline_streets
centerline_street_rows = centerline_rows.cut('PRE_DIR', 'ST_NAME', 'ST_TYPE', 'POST_DIR') \
    .addfield('STREET_FULL', lambda a: concat_streetname(a)) \
    .cut('STREET_FULL', 'PRE_DIR', 'ST_NAME', 'ST_TYPE', 'POST_DIR') \
    .distinct() \
    .sort(key=['ST_NAME', 'ST_TYPE', 'PRE_DIR', 'POST_DIR'])

print(etl.look(centerline_street_rows))
centerline_street_rows.tocsv(centerline_streets_csv, write_header=False)

'''
This refreshes the centerline.csv and centerline_streets.csv from scratch with alias'.
Author: Alex Waldman
'''
import re
import string
import petl as etl
import cx_Oracle
from passyunk.config import get_dsn
from passyunk.namestd import StandardName

dsn = get_dsn('ais_sources')
dbo = cx_Oracle.connect(dsn)
alias_table_name = 'alias_list_ais'
street_centerline_table_name = 'gis_streets.street_centerline'
centerline_csv = 'centerline.csv'
centerline_streets_csv = 'centerline_streets.csv'

def concat_streetname(row):
    predir = row['PRE_DIR']
    st_name = row['ST_NAME']
    st_type = row['ST_TYPE']

    stnam_list = filter(None, [predir, st_name, st_type])
    return ' '.join(stnam_list)

def standardize_name(name):
    tmp = name.strip()
    # Name standardization:
    tmp_list = re.sub('[' + string.punctuation + ']', '', tmp).split()
    std = StandardName(tmp_list, False).output
    std_name = ' '.join(std)
    return std_name


centerline_stmt = '''select trim(PRE_DIR) AS PRE_DIR,trim(ST_NAME) AS ST_NAME,trim(ST_TYPE) AS ST_TYPE,trim(SUF_DIR) AS SUF_DIR,
            L_F_ADD,L_T_ADD,R_F_ADD,R_T_ADD,ST_CODE,SEG_ID,trim(RESPONSIBL) AS RESPONSIBL from {} 
           order by st_name, pre_dir, st_type, suf_dir, l_f_add, l_t_add, r_f_add, r_t_add, st_code, seg_id'''.format(street_centerline_table_name)

centerline_rows = etl.fromdb(dbo, centerline_stmt).convert('ST_NAME', lambda s: standardize_name(s))

print(etl.look(centerline_rows))
centerline_rows.tocsv(centerline_csv)

# Centerline_streets
centerline_street_rows = centerline_rows.cut('PRE_DIR', 'ST_NAME', 'ST_TYPE') \
    .addfield('STREET_FULL', lambda a: concat_streetname(a)) \
    .addfield('POST_DIR', '') \
    .cut('STREET_FULL', 'PRE_DIR', 'ST_NAME', 'ST_TYPE', 'POST_DIR') \
    .distinct() \
    .sort(key=['ST_NAME', 'PRE_DIR', 'ST_TYPE', 'POST_DIR'])

print(etl.look(centerline_street_rows))
centerline_street_rows.tocsv(centerline_streets_csv, write_header=False)

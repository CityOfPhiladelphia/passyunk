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


centerline_stmt = '''select PRE_DIR,ST_NAME,ST_TYPE,SUF_DIR,L_F_ADD,L_T_ADD,R_F_ADD,R_T_ADD,ST_CODE,SEG_ID,RESPONSIBL from {} 
           order by st_name, pre_dir, st_type, suf_dir, l_f_add, l_t_add, r_f_add, r_t_add, st_code, seg_id'''.format(street_centerline_table_name)

alias_stmt = '''
    select ala.pre_dir, ala.name as st_name, ala.type_ as st_type, ala.suf_dir, sc.l_f_add, sc.l_t_add, sc.r_f_add,
    sc.r_t_add, sc.st_code, ala.seg_id, sc.responsibl 
    from {alias_table} ala 
    inner join {cl_table} sc on sc.seg_id = ala.seg_id
    order by st_name, pre_dir, st_type, suf_dir, l_f_add, l_t_add, r_f_add, r_t_add, st_code, seg_id
'''.format(cl_table = street_centerline_table_name, alias_table = alias_table_name)

# Get street centerlines with standardizations
centerline_rows = etl.fromdb(dbo, centerline_stmt).convert('ST_NAME', lambda s: standardize_name(s))
alias_rows = etl.fromdb(dbo, alias_stmt).convert('SEG_ID', int)
centerline_rows.tocsv(centerline_csv)
alias_rows.appendcsv(centerline_csv)

# unioned_rows = centerline_rows.cat(alias_rows)
# unioned_rows.tocsv(centerline_csv)

# Centerline_streets
centerline_street_rows = centerline_rows.cut('PRE_DIR', 'ST_NAME', 'ST_TYPE') \
    .addfield('STREET_FULL', lambda a: concat_streetname(a)) \
    .addfield('POST_DIR', '') \
    .cut('STREET_FULL', 'PRE_DIR', 'ST_NAME', 'ST_TYPE', 'POST_DIR')

print(etl.look(centerline_street_rows))

alias_centerline_street_rows = alias_rows.cut('PRE_DIR', 'ST_NAME', 'ST_TYPE') \
    .addfield('STREET_FULL', lambda a: concat_streetname(a)) \
    .cut('STREET_FULL', 'PRE_DIR', 'ST_NAME', 'ST_TYPE') \
    .addfield('POST_DIR', '')

new_centerline_street_rows = etl.cat(centerline_street_rows, alias_centerline_street_rows).distinct().sort(key=['ST_NAME', 'ST_TYPE', 'PRE_DIR'])

print(etl.look(new_centerline_street_rows))
new_centerline_street_rows.tocsv(centerline_streets_csv, write_header=False)

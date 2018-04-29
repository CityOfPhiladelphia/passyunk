'''
This refreshes the alias.csv and alias_streets.csv from scratch.
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
alias_csv = 'alias.csv'
alias_streets_csv = 'alias_streets.csv'

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


alias_stmt = '''
    select trim(ala.pre_dir) as PRE_DIR, trim(ala.name) as ST_NAME, trim(ala.type_) as ST_TYPE, trim(ala.suf_dir) as SUF_DIR, sc.l_f_add, sc.l_t_add, sc.r_f_add,
    sc.r_t_add, sc.st_code, ala.seg_id, trim(sc.responsibl) as RESPONSIBL, trim(sc.pre_dir) as CL_PRE_DIR, trim(sc.name) as CL_ST_NAME, trim(sc.type_) as CL_ST_TYPE, trim(sc.suf_dir) as CL_SUF_DIR
    from {alias_table} ala 
    inner join {cl_table} sc on sc.seg_id = ala.seg_id
    order by st_name, pre_dir, st_type, suf_dir, l_f_add, l_t_add, r_f_add, r_t_add, st_code, seg_id
'''.format(cl_table = street_centerline_table_name, alias_table = alias_table_name)

alias_rows = etl.fromdb(dbo, alias_stmt).convert('SEG_ID', int).convert('ST_NAME', lambda s: standardize_name(s)) \
    .addfield('STREET_FULL', lambda a: concat_streetname(a))
alias_rows.tocsv(alias_csv)

alias_centerline_street_rows = alias_rows.cut('PRE_DIR', 'ST_NAME', 'ST_TYPE') \
    .addfield('STREET_FULL', lambda a: concat_streetname(a)) \
    .cut('STREET_FULL', 'PRE_DIR', 'ST_NAME', 'ST_TYPE') \
    .addfield('POST_DIR', '')

alias_centerline_street_rows.tocsv(alias_streets_csv, write_header=False)
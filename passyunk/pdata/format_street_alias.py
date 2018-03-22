import petl as etl
import cx_Oracle
from config import get_dsn

dsn = get_dsn('ais_sources')
alias_table_name = 'alias_list_ais'
street_centerline_table_name = 'gis_streets.street_centerline'
centerline_csv = 'centerline.csv'
centerline_streets_csv = 'centerline_streets.csv'

stmt = '''
    select ala.pre_dir, ala.name as st_name, ala.type_ as st_type, ala.suf_dir, sc.l_f_add, sc.l_t_add, sc.r_f_add,
    sc.r_t_add, sc.st_code, ala.seg_id, sc.responsibl 
    from alias_list_ais ala 
    inner join gis_streets.street_centerline sc on sc.seg_id = ala.seg_id
    order by st_name, pre_dir, st_type, suf_dir, l_f_add, l_t_add, r_f_add, r_t_add, st_code
'''

db = cx_Oracle.connect(dsn)

alias_rows = etl.fromdb(db, stmt).convert('SEG_ID', int)
print(etl.look(alias_rows))
# alias_rows.appendcsv(centerline_csv)


def concat_streetname(row):
    predir = row['PRE_DIR']
    st_name = row['ST_NAME']
    st_type = row['ST_TYPE']

    stnam_list = filter(None, [predir, st_name, st_type])
    return ' '.join(stnam_list)

centerline_street_rows = etl.fromcsv(centerline_streets_csv).pushheader(['STREET_FULL', 'PRE_DIR', 'ST_NAME', 'ST_TYPE', 'POST_DIR'])
print(etl.look(centerline_street_rows))

alias_centerline_street_rows = alias_rows.cut('PRE_DIR', 'ST_NAME', 'ST_TYPE') \
    .addfield('STREET_FULL', lambda a: concat_streetname(a)) \
    .cut('STREET_FULL', 'PRE_DIR', 'ST_NAME', 'ST_TYPE') \
    .addfield('POST_DIR', '')

new_centerline_street_rows = etl.cat(centerline_street_rows, alias_centerline_street_rows).distinct().sort(key=['ST_NAME', 'ST_TYPE', 'PRE_DIR'])

print(etl.look(new_centerline_street_rows))
new_centerline_street_rows.tocsv(centerline_streets_csv, write_header=False)
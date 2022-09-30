'''
This refreshes the centerline.csv and centerline_streets.csv from scratch (no alias).
Author: Alex Waldman
Revisions: James Midkiff
'''
import re
import string
import os
import petl as etl
import click
import utils as util
import oracle_code
import passyunk
from passyunk.namestd import StandardName

db_creds = util.get_creds("/scripts/passyunk_automation/passyunk/pdata/oracle.json", ['GIS_STREETS'])
dbo = oracle_code.connect_to_db(db_creds) 
street_centerline_table_name = 'gis_streets.street_centerline'
centerline_csv = 'centerline.csv'
centerline_streets_csv = 'centerline_streets.csv'
pdata = os.path.dirname(passyunk.__file__) + '/pdata'
error_threshold = 0.05 # Fail if more than x% of the rows between two CSVs are different

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

def check_errors(new, name, error_threshold=error_threshold): 
    print(f'Checking for errors in {name} with error threshold {error_threshold:.1%}')
    match name: # A Case-When, or If-Else statement
        case 'centerline_rows': 
            csv = centerline_csv
            header = None
        case 'centerline_street_rows': 
            csv = centerline_streets_csv
            header = ['STREET_FULL', 'PRE_DIR', 'ST_NAME', 'ST_TYPE', 'POST_DIR']
        case _: 
            raise NameError(f'{name} not recognized for comparing old and new CSV files')
    old = (etl
        .fromcsv(pdata + '/' + csv, header=header)) 
    old_nrows = etl.nrows(old)
    # petl only reads in as string, so need to convert new to fully string format
    t1 = etl.replaceall(new, None, '')
    new_check = etl.convertall(t1, str)

    added, subtracted = etl.recorddiff(old, new_check)
    added_nrows = etl.nrows(added)
    subtracted_nrows = etl.nrows(subtracted)
    if added_nrows / old_nrows >= error_threshold: 
        print(f'Added Rows Look: (total of {added_nrows} new rows compared to {old_nrows} old rows)')
        print(added.look())
        raise ValueError(f'There are more than {error_threshold:.1%} new entries in new file')
    if subtracted_nrows / old_nrows >= error_threshold: 
        print(f'Subtracted Rows Look: (total of {subtracted_nrows} deleted rows compared to {old_nrows} old rows)')
        print(subtracted.look())
        raise ValueError(f'There are more than {error_threshold:.1%} deleted entries in new file')

@click.command()
@click.option('--bypass', '-b', is_flag=True, show_default=True, default=False, 
    help='Flag to bypass error checking')
def main(bypass): 
    '''
    \b
    Refreshes the centerline.csv and centerline_streets.csv in the passyunk module 
    by pulling from the relevant database, applying transformations, and writing to CSV. 
    
    Will check that fewer than x% of the rows are different unless the bypass flag 
    "-b" is passed. 
    '''

    centerline_stmt = f'''
    select trim(PRE_DIR) AS PRE_DIR, trim(ST_NAME) AS ST_NAME, trim(ST_TYPE) AS ST_TYPE, 
        trim(SUF_DIR) AS POST_DIR, L_F_ADD, L_T_ADD, R_F_ADD, R_T_ADD, ST_CODE, SEG_ID, 
        trim(RESPONSIBL) AS RESPONSIBL 
    from {street_centerline_table_name} 
    order by st_name, st_type, pre_dir, suf_dir, l_f_add, l_t_add, r_f_add, r_t_add, 
        st_code, seg_id
    '''

    centerline_rows = (etl
        .fromdb(dbo, centerline_stmt)
        .convert('ST_NAME', lambda s: standardize_name(s)))
    if not bypass: 
        check_errors(centerline_rows, 'centerline_rows')

    print(etl.look(centerline_rows))
    centerline_rows.tocsv(centerline_csv)

    # Centerline_streets
    centerline_street_rows = centerline_rows.cut('PRE_DIR', 'ST_NAME', 'ST_TYPE', 'POST_DIR') \
        .addfield('STREET_FULL', lambda a: concat_streetname(a)) \
        .cut('STREET_FULL', 'PRE_DIR', 'ST_NAME', 'ST_TYPE', 'POST_DIR') \
        .distinct() \
        .sort(key=['ST_NAME', 'ST_TYPE', 'PRE_DIR', 'POST_DIR'])
    if not bypass: 
        check_errors(centerline_street_rows, 'centerline_street_rows')
    else: 
        print('Bypassing error checking')

    print(etl.look(centerline_street_rows))
    centerline_street_rows.tocsv(centerline_streets_csv, write_header=False)

if __name__ == '__main__': 
    main()
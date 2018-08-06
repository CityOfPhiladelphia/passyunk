import os
import petl as etl
from passyunk.parser import PassyunkParser

cwd = os.path.abspath(os.curdir)
cwd = os.path.dirname(cwd)
cwd += '/pdata/'
centerline_file = 'centerline_shape.csv'
centerline_file_path = cwd + centerline_file
output_csv = 'test_streets_results.csv'
parser = PassyunkParser()

etl.fromcsv(centerline_file_path) \
    .cut('PRE_DIR', 'ST_NAME', 'ST_TYPE', 'SUF_DIR', 'ST_CODE') \
    .addfield('ST_FULL', lambda s: ' '.join([s.PRE_DIR, s.ST_NAME, s.ST_TYPE, s.SUF_DIR]).strip()) \
    .unique('ST_FULL') \
    .addfield('DIR_NAME', lambda d: ' '.join([d.PRE_DIR, d.ST_NAME]).strip()) \
    .addfield('NAME_TYPE', lambda l: ' '.join([l.ST_NAME, l.ST_TYPE]).strip()) \
    .addfield('st_code_st_full', lambda f: parser.parse(f.ST_FULL)['components']['street']['street_code']) \
    .addfield('st_code_dir_name', lambda f: parser.parse(f.DIR_NAME)['components']['street']['street_code']) \
    .addfield('st_code_name_type', lambda f: parser.parse(f.NAME_TYPE)['components']['street']['street_code']) \
    .addfield('match_st_full', lambda m: 1 if m.st_code_st_full and m.st_code_st_full == m.ST_CODE else 0) \
    .addfield('match_dir_name', lambda m: 1 if m.st_code_dir_name and m.st_code_dir_name == m.ST_CODE else 0) \
    .addfield('match_name_type', lambda m: 1 if m.st_code_name_type and m.st_code_name_type == m.ST_CODE else 0) \
    .progress(1000) \
    .tocsv(output_csv)

# print(etl.look(rows))
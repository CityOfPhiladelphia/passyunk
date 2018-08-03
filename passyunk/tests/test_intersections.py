import petl as etl
import psycopg2
from passyunk.config import get_dsn
from passyunk.parser import PassyunkParser

engine_intersections_table = 'street_intersection'
output_csv = 'test_intersections_results.csv'
dsn = get_dsn('ais_engine')
db_user = dsn[dsn.index("//") + 2:dsn.index(":", dsn.index("//"))]
db_pw = dsn[dsn.index(":",dsn.index(db_user)) + 1:dsn.index("@")]
db_name = dsn[dsn.index("/", dsn.index("@")) + 1:]
pg_db = psycopg2.connect('dbname={db_name} user={db_user} password={db_pw} host=localhost'.format(db_name=db_name, db_user=db_user, db_pw=db_pw))

parser = PassyunkParser()

read_intersections_stmt = '''
    select * from {}
'''.format(engine_intersections_table)

engine_intersections = etl.fromdb(pg_db, read_intersections_stmt)
print(etl.look(engine_intersections))

engine_intersections \
    .addfield('full_intersection_name_fwd', lambda f: ' and '.join([f.street_1_full, f.street_2_full])) \
    .addfield('full_intersection_name_bkwd', lambda f: ' and '.join([f.street_2_full, f.street_1_full])) \
    .addfield('base_intersection_name_fwd', lambda f: ' and '.join([f.street_1_name, f.street_2_name])) \
    .addfield('base_intersection_name_bkwd', lambda f: ' and '.join([f.street_2_name, f.street_1_name])) \
    .addfield('node_id_full_fwd', lambda f: parser.parse(f.full_intersection_name_fwd)['components']['node_id']) \
    .addfield('node_id_full_bkwd', lambda f: parser.parse(f.full_intersection_name_bkwd)['components']['node_id']) \
    .addfield('node_id_base_fwd', lambda f: parser.parse(f.base_intersection_name_fwd)['components']['node_id']) \
    .addfield('node_id_base_bkwd', lambda f: parser.parse(f.base_intersection_name_bkwd)['components']['node_id']) \
    .addfield('match_full_fwd', lambda m: 1 if m.node_id_full_fwd and int(m.node_id_full_fwd) == m. node_id else 0) \
    .addfield('match_full_bdwd', lambda m: 1 if m.node_id_full_bkwd and int(m.node_id_full_bkwd) == m. node_id else 0) \
    .addfield('match_base_fwd', lambda m: 1 if m.node_id_base_fwd and int(m.node_id_base_fwd) == m. node_id else 0) \
    .addfield('match_base_bdwd', lambda m: 1 if m.node_id_base_bkwd and int(m.node_id_base_bkwd) == m. node_id else 0) \
    .progress(1000) \
    .tocsv(output_csv)


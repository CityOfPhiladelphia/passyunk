import petl as etl
import psycopg2
from passyunk.config import get_dsn

dsn = get_dsn('ais_engine')
intersections_engine_table = 'street_intersection'
intersection_csv = 'intersections.csv'
db_user = dsn[dsn.index("//") + 2:dsn.index(":", dsn.index("//"))]
db_pw = dsn[dsn.index(":",dsn.index(db_user)) + 1:dsn.index("@")]
db_name = dsn[dsn.index("/", dsn.index("@")) + 1:]
pg_db = psycopg2.connect('dbname={db_name} user={db_user} password={db_pw} host=localhost'.format(db_name=db_name, db_user=db_user, db_pw=db_pw))

etl.fromdb(pg_db, 'select node_id, int_id, street_1_code, street_2_code, st_astext(geom) as shape from {}'.format(intersections_engine_table)) \
    .tocsv(intersection_csv)


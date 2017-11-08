import petl as etl
import cx_Oracle
from passyunk.config import get_dsn
from functools import partial
from pyproj import Proj, transform as pyproj_transform
from shapely.ops import transform
from shapely.wkt import loads

project = partial(
    pyproj_transform,
    Proj(init='epsg:2272', preserve_units=True),  # source coordinate system
    Proj(init='epsg:4326', preserve_units=True)  # destination coordinate system
)

dsn = get_dsn('streets')
dbo = cx_Oracle.connect(dsn)
table = 'street_centerline'
etl.fromdb(dbo,
           'select PRE_DIR,ST_NAME,ST_TYPE,SUF_DIR,L_F_ADD,L_T_ADD,R_F_ADD,R_T_ADD,ST_CODE,SEG_ID,RESPONSIBL,sde.st_astext(shape) as "SHAPE" from STREET_CENTERLINE order by st_name, pre_dir, st_type, suf_dir, l_f_add, l_t_add, r_f_add, r_t_add, st_code') \
    .convert('SHAPE', lambda t: transform(project, loads(t.read())).wkt) \
    .progress(1000) \
    .tocsv('centerline_shape.csv')

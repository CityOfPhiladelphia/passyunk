import petl as etl
import cx_Oracle
from passyunk.namestd import StandardName
from passyunk.parser import PassyunkParser
from passyunk.config import get_dsn

parser = PassyunkParser()
outfile = "landmarks.csv"
dsn = get_dsn('gsg')
dbo = cx_Oracle.connect(dsn)

def standardize(tmp):
    tmp = tmp.strip().upper()
    # Name standardization:
    # tmp_list = re.sub('[' + string.punctuation + ']', '', tmp).split()
    tmp_list = tmp.split()
    std = StandardName(tmp_list, False).output
    # Don't match on 'the' if first word
    tmp = ' '.join(std)
    return tmp

stmt = '''
with places as 
(
select name, address, globalid from namedplaces_polygons where address is not null and substr(name,1,1) NOT IN ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9') and public_ = 'Y'
union
select name, address, globalid from namedplaces_points where address is not null and substr(name,1,1) NOT IN ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9') and public_ = 'Y'
)
,
union_alias as
(
select p.name, p.address
from places p
union
(select alias as name, p.address
from namedplaces_alias npa
left join places p on p.globalid = npa.foreign_key
)
)
select * from union_alias where address is not null
order by name
'''

rows = etl.fromdb(dbo, stmt) \
    .addfield('std_name', lambda s: standardize(s.NAME)) \
    .addfield('std_addr', lambda s: parser.parse(s.ADDRESS)['components']['output_address']) \
    .cutout('NAME', 'ADDRESS') \
    .progress(500) \
    .tocsv(outfile, write_header=False)

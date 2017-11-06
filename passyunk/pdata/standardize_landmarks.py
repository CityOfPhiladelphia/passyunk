import petl as etl
from passyunk.namestd import StandardName
from passyunk.parser import PassyunkParser

parser = PassyunkParser()
infile = "landmarks.csv"
outfile = "stdandardize_landmarks.csv"

def standardize(tmp):
    tmp = tmp.strip().upper()
    # Name standardization:
    # tmp_list = re.sub('[' + string.punctuation + ']', '', tmp).split()
    tmp_list = tmp.split()
    std = StandardName(tmp_list, False).output
    # Don't match on 'the' if first word
    tmp = ' '.join(std)
    return tmp

# TODO: Read infile as rows from db
# stmt = '''select name, address from city_landmarks where address is not null and substr(name,1,1) NOT IN ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '"')
# union
# select name, address from city_landmarks_pts where address is not null and substr(name,1,1) NOT IN ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '"');
# '''
# etl.fromdb(dbo, stmt) \
etl.fromcsv(infile)\
    .pushheader('name', 'address') \
    .addfield('std_name', lambda s: standardize(s.name)) \
    .addfield('std_addr', lambda s: parser.parse(s.address)['components']['output_address']) \
    .cutout('name', 'address') \
    .progress(500) \
    .tocsv(outfile, write_header=False)

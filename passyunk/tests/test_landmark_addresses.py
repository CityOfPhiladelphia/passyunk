import os
import petl as etl
from passyunk.parser import PassyunkParser

parser = PassyunkParser()
cwd = os.path.abspath(os.curdir)
cwd = os.path.dirname(cwd)
cwd += '/pdata/'
landmarks_file = 'landmarks.csv'
landmarks_file_path = cwd + landmarks_file
output_csv = 'test_landmarks_results.csv'

etl.fromcsv(landmarks_file_path).pushheader('name', 'address').select(lambda s: s.address) \
    .addfield('matched_address', lambda m: parser.parse(m.name)['components']['output_address']) \
    .addfield('correct_match', lambda c: 1 if c.matched_address == c.address else 0) \
    .progress(1000) \
    .tocsv(output_csv)

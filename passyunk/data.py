# dict to standardize predirs/postdirs
DIRS_STD = {
    'N':        'N',
    'NO':       'N',
    'NORTH':    'N',
    'S':        'S',
    'SO':       'S',
    'SOUTH':    'S',
    'E':        'E',
    'EAST':     'E',
    'W':        'W',
    'WEST':     'W'
}

# dict to standardize suffixes
SUFFIXES_STD = {}

with open('./pdata/suffix.csv') as f:
    for line in f.readlines():
        cols = line.split(',')
        common = cols[1]
        std = cols[2]
        SUFFIXES_STD[common] = std

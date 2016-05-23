import sys
from pprint import pprint
from passyunk.parser import PassyunkParser

p = PassyunkParser()
try:
    a = sys.argv[1]
except IndexError:
    print('No address specified')

r = p.parse(a)
pprint(r)



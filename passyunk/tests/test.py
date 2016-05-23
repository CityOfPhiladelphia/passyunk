import sys
import json
from passyunk.parser import PassyunkParser

parser = PassyunkParser()

parsed = parser.parse('3400 E FALLS LN')
# print(parsed)

print(json.dumps(parsed, sort_keys=True, indent=2))
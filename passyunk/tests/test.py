import sys
import json
from passyunk.parser import PassyunkParser

parser = PassyunkParser()

parsed = parser.parse('9038 AYRDALECRESCENT ST')
# print(parsed)

print(json.dumps(parsed, sort_keys=True, indent=2))
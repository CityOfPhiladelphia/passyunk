import sys
import json
from passyunk.parser import PassyunkParser

parser = PassyunkParser()

parsed = parser.parse('253 PORT ROYAL')
#parsed = parser.parse('PHILAREDEVELOPMENTAUTHORITYSOPHILLY')
# print(parsed)

print(json.dumps(parsed, sort_keys=True, indent=2))

##53109644,09/09/2016 00:00:00,"ASSIGNMENT OF MORTGAGE","","SHELLPOINT MORTGAGE SERVICING","","",6311,"","","REGENT","ST","",""

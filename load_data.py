import json
import os
from pprint import pprint

import requests


os.chdir('./scrap/json')
files = os.listdir()

for fn in files:
    data = json.load(open(fn))
    pprint(data)
    id = fn.replace('.json', '')
    url = 'http://localhost:9200/brazil4export/company/%s' % id
    try:
        r = requests.post(url, data=data)
    except:
        print(id)
    break

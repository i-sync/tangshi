# -*- utf-8 -*-

import os
import json
from getproxy import GetProxy

g = GetProxy()
g.init()
g.load_plugins()
g.grab_web_proxies()
g.validate_web_proxies()

print('availble count:{}'.format(len(g.valid_proxies)))

#proxys = json.dumps(g.valid_proxies)

filename= 'proxy.json'

if os.path.exists(filename):
    os.remove(filename)

with open(filename, 'w', encoding = 'utf-8') as f:
    #f.write(proxys)
    json.dump(g.valid_proxies, f)

print('OK')
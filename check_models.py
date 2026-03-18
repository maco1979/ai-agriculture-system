import urllib.request
import json

try:
    r = urllib.request.urlopen('http://localhost:8001/api/models', timeout=5)
    data = json.loads(r.read())
    print('Models count:', len(data.get('data', [])))
    for m in data.get('data', []):
        print('  - id:', repr(m.get('id')), 'name:', m.get('name'))
except Exception as e:
    print('Error:', e)

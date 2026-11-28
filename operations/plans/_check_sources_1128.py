import json
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse
p='operations/plans/pak_vincent-2026-11-28.json'
d=json.load(open(p))
now=datetime.now(timezone.utc)
print('now',now.isoformat())
for s in d['trend_sources']:
    url=urlparse(s.get('url',''))
    try:
        stamp=datetime.fromisoformat(s.get('observed_at','').replace('Z','+00:00'))
    except Exception as e:
        print('BADSTAMP',e); continue
    print(url.scheme, url.hostname, stamp.tzinfo, (now-stamp).total_seconds()/3600, bool(s.get('evidence')), bool(s.get('title')))

"""Update presentation only; no refresh, source imports, or publication."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from navigation import render_navigation, render_tracker
from validate_site import check_bytes

ROOT=Path(__file__).resolve().parents[1]

def build():
    site=ROOT/'site'
    files={p.relative_to(site).as_posix():p.read_bytes() for p in site.rglob('*') if p.is_file() and p.name!='manifest.json'}
    files['index.html']=render_navigation(files['index.html'].decode('utf-8')).encode('utf-8')
    files['tracker/index.html']=render_tracker(files['tracker/index.html'].decode('utf-8')).encode('utf-8')
    checked=check_bytes(files)
    previous=json.loads((site/'manifest.json').read_text(encoding='utf-8'))
    manifest={**previous,'packagedAt':datetime.now(timezone.utc).isoformat(),'files':[{'path':n,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()} for n,b in sorted(files.items())]}
    for name in ['index.html','tracker/index.html']:(site/name).write_bytes(files[name])
    (site/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8',newline='\n')
    print(json.dumps({'navigationUpdated':True,'relativeLinksChecked':checked,'marketDataRefreshed':False,'published':False}))

if __name__=='__main__':build()

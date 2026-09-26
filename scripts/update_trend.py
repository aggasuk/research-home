"""Scoped publication of saved Rates Trend alerts; no model or market requests."""
import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from navigation import PAYLOAD, render_navigation
from validate_site import check_bytes

ROOT = Path(__file__).resolve().parents[1]


def build(source):
    data = json.loads((source/'action-status.json').read_text(encoding='utf-8'))
    page = (source/'trend.html').read_text(encoding='utf-8').encode('utf-8')
    if data['checked_at'][:16].replace('T',' ') not in page.decode('utf-8'):
        raise ValueError('Tracker page/status timestamp mismatch')
    files = {p.relative_to(ROOT/'site').as_posix(): p.read_bytes() for p in (ROOT/'site').rglob('*')
             if p.is_file() and p.name != 'manifest.json'}
    before = {k:v for k,v in files.items() if k.startswith('rv/') or k == 'india.html'}
    files['tracker/index.html'] = page
    files['tracker/status.json'] = json.dumps(data,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode('utf-8')
    revision = hashlib.sha256(page).hexdigest()[:16]
    shell = files['index.html'].decode('utf-8'); match=PAYLOAD.search(shell)
    payload = json.loads(match[1])
    payload['tracker'] = {k:data[k] for k in ['checked_at','status','activated_at','policy']}
    payload['trackerDates'] = sorted({r['source_date'] for r in data['records'].values()})
    payload['trackerUrl'] = 'tracker/index.html?v='+revision
    payload['builtAt'] = data['checked_at']
    methods = re.search(r'<details><summary>Methodology and timing</summary>(.*?)</details>',page.decode('utf-8'),re.S)[1]
    method = {'id':'rates-trend-methodology','title':'Rates Trend · methodology and immediate alerts',
              'category':'Frameworks','date':data['activated_at'][:10],
              'badge':'Frozen models · immediate alerts', 'dataDate':max(payload['trackerDates'],default=None),
              'description':'Five markets, pullback/trend/breakout signals, immediate observed alerts and preserved next-close paper history.',
              'source':'reports/rates-trend-methodology.html','resources':[],
              'html':methods.replace('../index.html#','#')}
    payload['reports']=[r for r in payload['reports'] if r['id'] != method['id']]+[method]
    packed=json.dumps(payload,ensure_ascii=False).replace('<','\\u003c').replace('\u2028','\\u2028').replace('\u2029','\\u2029')
    files['index.html']=render_navigation(shell[:match.start(1)]+packed+shell[match.end(1):]).encode('utf-8')
    files[method['source']]=('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Rates Trend methodology</title><link rel="stylesheet" href="../rv/workspace.css"><main><a href="../index.html#rates-trend">Rates Trend</a><h1>Rates Trend methodology</h1>'+methods+'</main></html>').encode('utf-8')
    assert all(files[k]==v for k,v in before.items()), 'Unrelated RV/India changed'
    check_bytes(files)
    manifest=json.loads((ROOT/'site/manifest.json').read_text(encoding='utf-8'))
    manifest.update(packagedAt=datetime.now(timezone.utc).isoformat(),libraryBuiltAt=payload['builtAt'],reports=len(payload['reports']),
                    files=[{'path':k,'bytes':len(v),'sha256':hashlib.sha256(v).hexdigest()} for k,v in sorted(files.items())])
    changed=[]
    for k,v in files.items():
        target=ROOT/'site'/k
        if target.exists() and target.read_bytes()==v:continue
        target.parent.mkdir(parents=True,exist_ok=True)
        temp=target.with_suffix(target.suffix+'.tmp');temp.write_bytes(v);temp.replace(target);changed.append(k)
    (ROOT/'site/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({'packaged':True,'changed':changed,'checked_at':data['checked_at'],'status':data['status']}))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--tracker-root',type=Path,required=True)
    build(parser.parse_args().tracker_root.resolve())

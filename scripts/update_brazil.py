"""Publish only the reviewed Brazil HTML and public ledgers; no data refresh or network."""
import argparse,hashlib,json,re
from datetime import datetime,timezone
from pathlib import Path
from navigation import render_navigation
from validate_site import check_bytes

ROOT=Path(__file__).resolve().parents[1]

def build(source):
    site=ROOT/'site'
    files={p.relative_to(site).as_posix():p.read_bytes() for p in site.rglob('*') if p.is_file() and p.name!='manifest.json'}
    before=dict(files)
    # Explicit allowlist: no reference images, browser profiles, archives or market files.
    page=(source/'brazil-runoff.html').read_text(encoding='utf-8')
    assert 'Scenario win probability' in page and 'uncalibrated' in page
    page=page.replace('https://aggasuk.github.io/research-home/#','../index.html#')
    page=page.replace('<a class="active" href="#overview">Research</a>','<a href="../index.html#research">Research</a><a class="active" aria-current="page" href="#overview">Brazil polls</a>')
    page=page.replace('Local preview<br>No live data requests','Saved polling snapshot<br>No automatic refresh')
    page=page.replace('Local preview · no publication or automatic refresh','Saved snapshot · no automatic refresh')
    # Keep selected-poll export accessible on phones.
    page=page.replace('.export{display:none}', '.export{display:block;margin-left:0;padding:7px 0}.page-tabs{flex-wrap:wrap;gap:8px 16px}')
    assert 'Local preview' not in page
    files['brazil-runoff/index.html']=page.encode('utf-8')
    for name in ['polls.json','polls.csv']:files['brazil-runoff/'+name]=(source/name).read_bytes()
    files['index.html']=render_navigation(files['index.html'].decode('utf-8')).encode('utf-8')
    # Existing report payload and every unrelated static asset must stay byte-identical.
    pattern=r'const DATA = (.*?);\r?\nconst \$'
    assert re.search(pattern,before['index.html'].decode(),re.S).group(1)==re.search(pattern,files['index.html'].decode(),re.S).group(1)
    changed=[n for n,b in files.items() if before.get(n)!=b]
    assert set(changed)<= {'index.html','brazil-runoff/index.html','brazil-runoff/polls.json','brazil-runoff/polls.csv'},changed
    links=check_bytes(files)
    previous=json.loads((site/'manifest.json').read_text(encoding='utf-8'))
    manifest={**previous,'packagedAt':datetime.now(timezone.utc).isoformat(),'files':[{'path':n,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()} for n,b in sorted(files.items())]}
    for name in changed:
        target=site/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(files[name])
    (site/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8',newline='\n')
    print(json.dumps({'changed':changed,'relativeLinksChecked':links,'unrelatedAssetsPreserved':True,'dataRefreshed':False,'published':False}))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,required=True);args=parser.parse_args();build(args.source)

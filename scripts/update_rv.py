"""Update only RV content and its navigation in the existing published package."""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import re
from validate_site import check_bytes

ROOT=Path(__file__).resolve().parents[1]
PATTERN=re.compile(r'const DATA = (.*?);\r?\nconst \$',re.S)


def build(source):
    site=ROOT/'site'
    old_html=(site/'index.html').read_text(encoding='utf-8')
    old=json.loads(PATTERN.search(old_html).group(1))
    new_html=(source/'index.html').read_text(encoding='utf-8')
    match=PATTERN.search(new_html)
    local=json.loads(match.group(1))
    reports=[copy.deepcopy(r) for r in local['reports'] if r['id'].startswith('rates-rv')]
    assert {r['id'] for r in reports}=={'rates-rv','rates-rv-models','rates-rv-review'}
    data=copy.deepcopy(old)
    data['reports']=[r for r in old['reports'] if not r['id'].startswith('rates-rv')]+reports
    data['reports'].sort(key=lambda r:r['date'],reverse=True)
    data['rv']=local['rv']; data['builtAt']=local['builtAt']
    files={p.relative_to(site).as_posix():p.read_bytes() for p in site.rglob('*') if p.is_file() and p.name!='manifest.json'}
    style=re.search(r'<style>(.*?)</style>',new_html,re.S).group(1)
    for report in reports:
        embedded=report.get('embeddedUrl')
        if embedded:
            assert embedded in ['rv/models.html','rv/trade-review.html']
            files[embedded]=(source/embedded).read_bytes()
            report['source']=embedded
        else:
            report['source']='reports/rates-rv.html'
            body=report['html'].replace('href="#report/','href="../index.html#report/')
            files[report['source']]=('<!doctype html><meta charset="utf-8"><title>Rates RV discovery</title><style>'+style+'</style><main><a href="../index.html#report/rates-rv">Research Home</a><h1>'+html.escape(report['title'])+'</h1><article class="article">'+body+'</article></main>').encode()
    packed=json.dumps(data,ensure_ascii=False).replace('<','\\u003c').replace('\u2028','\\u2028').replace('\u2029','\\u2029')
    page=new_html[:match.start(1)]+packed+new_html[match.end(1):]
    page=page.replace('Original file ↗','Open report ↗')
    page=page.replace('The existing daily process rebuilds this library from saved outputs; reload the page to see the latest build.','RV is updated after the daily dashboard refresh and published here. Other reports retain their saved publication dates; reload to see the latest published version.')
    files['index.html']=page.encode('utf-8')
    # Scope assertion: other published content and metadata are not refreshed.
    assert [r for r in data['reports'] if not r['id'].startswith('rates-rv')]==sorted([r for r in old['reports'] if not r['id'].startswith('rates-rv')],key=lambda r:r['date'],reverse=True)
    links=check_bytes(files)
    previous=json.loads((site/'manifest.json').read_text())
    manifest={**previous,'packagedAt':datetime.now(timezone.utc).isoformat(),'libraryBuiltAt':data['builtAt'],
        'reports':len(data['reports']),'files':[{'path':name,'bytes':len(blob),'sha256':hashlib.sha256(blob).hexdigest()} for name,blob in sorted(files.items())]}
    changed=[]
    for name,blob in files.items():
        target=site/name
        if target.exists() and target.read_bytes()==blob:continue
        assert name in ['index.html','reports/rates-rv.html','rv/models.html','rv/trade-review.html']
        target.parent.mkdir(parents=True,exist_ok=True)
        temporary=target.with_suffix('.tmp');temporary.write_bytes(blob);temporary.replace(target);changed.append(name)
    (site/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8',newline='\n')
    print(json.dumps({'changed':changed,'reports':len(data['reports']),'relativeLinksChecked':links,'otherPublishedReportsPreserved':True}))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,required=True)
    build(parser.parse_args().source.resolve())

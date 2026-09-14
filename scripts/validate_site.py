"""Offline checks for the exact static files to publish; requires standard Python only."""
import hashlib, html, json, posixpath, re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote,urlsplit
ROOT=Path(__file__).resolve().parents[1]
class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[];self.ids=[]
    def handle_starttag(self,tag,attrs):
        for k,v in attrs:
            if k in ['href','src'] and v:self.links.append(v)
            if k=='id':self.ids.append(v)
def check_bytes(files):
    checked=0
    for name,blob in files.items():
        if name.endswith(('.pkl','.zip','.env')):raise ValueError('Unexpected private/archive format: '+name)
        if not name.endswith(('.html','.json','.csv')):continue
        text=blob.decode('utf-8-sig')
        for pattern in [r'file:///',r'http://(?:127\.0\.0\.1|localhost)',r'[A-Z]:[/\\](?:Users|Windows)',r'gh[pousr]_[A-Za-z0-9]{20,}',r'github_pat_[A-Za-z0-9_]{20,}',r'-----BEGIN .*PRIVATE KEY-----']:
            if re.search(pattern,text):raise ValueError('Non-public reference or credential pattern in '+name)
        if not name.endswith('.html'):continue
        parser=Links();parser.feed(text)
        if len(parser.ids)!=len(set(parser.ids)):raise ValueError('Duplicate HTML IDs in '+name)
        links=parser.links[:]
        if name=='index.html':
            match=re.search(r'const DATA = (.*?);\r?\nconst \$',text,re.S)
            if not match:raise ValueError('Missing library payload')
            data=json.loads(match.group(1));links.append(data['trackerUrl'])
            for r in data['reports']:
                links.append(r['source']);links.extend(x['url'] for x in r.get('resources',[]))
                report=Links();report.feed(r['html']);links.extend(report.links)
            if 'india.html' not in text:raise ValueError('India navigation missing')
        for url in links:
            u=urlsplit(html.unescape(url))
            if u.scheme or u.netloc or not u.path:continue
            if u.path.startswith('/research-home/'):path=u.path.removeprefix('/research-home/') or 'index.html'
            elif u.path.startswith('/'):raise ValueError('Root-absolute link incompatible with project Pages: '+url)
            else:path=posixpath.normpath(posixpath.join(posixpath.dirname(name),unquote(u.path)))
            if path not in files:raise ValueError('Missing target '+path+' from '+name)
            checked+=1
    india=files.get('india.html',b'').decode('utf-8')
    for required in ['Net reserves','Balance of payments','panel-inflation']:
        if required not in india:raise ValueError('India section missing '+required)
    match=re.search(r'window.INDIA_DATA=(.*?);</script>',india,re.S)
    if not match:raise ValueError('India data missing')
    snapshot=json.loads(match.group(1));latest=snapshot['reserves']['latest']
    if abs(latest['adjusted']-latest['fca']-latest['forwards'])>1e-8:raise ValueError('Adjusted FCA does not reconcile')
    if latest['forwardDate']>latest['date'] or latest['fcaDate']>latest['date']:raise ValueError('Invalid reserves dates')
    return checked
def validate():
    site=ROOT/'site';files={p.relative_to(site).as_posix():p.read_bytes() for p in site.rglob('*') if p.is_file()}
    links=check_bytes(files);manifest=json.loads(files['manifest.json'])
    for r in manifest['files']:
        if hashlib.sha256(files[r['path']]).hexdigest()!=r['sha256']:raise ValueError('Manifest mismatch '+r['path'])
    print(json.dumps({'status':'PASS','files':len(files),'relativeLinksChecked':links,'reports':manifest['reports'],'totalBytes':sum(map(len,files.values()))}))
if __name__=='__main__':validate()

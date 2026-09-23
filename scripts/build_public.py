"""Package the existing saved Research Home for public static hosting. No network."""
import argparse, copy, hashlib, html, json, re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/'site'
PAYLOAD=re.compile(r'const DATA = (.*?);\r?\nconst \$',re.S)

def read(path):return path.read_text(encoding='utf-8')
def file_path(url):
    value=unquote(urlsplit(html.unescape(url)).path)
    if re.match(r'^/[A-Za-z]:/',value):value=value[1:]
    return Path(value)
def build(source):
    source=source.resolve();original=read(source/'index.html')
    match=PAYLOAD.search(original)
    if not match:raise ValueError('Research Home data block not found')
    data=json.loads(match.group(1));original_data=copy.deepcopy(data)
    files={};mapping={};omitted=[]
    # Resources are explicitly linked deliverables. Do not recursively copy any folder.
    for report in data['reports']:
        kept=[]
        for resource in report.get('resources',[]):
            url=resource['url']
            if not url.startswith('file:'):
                kept.append(resource);continue
            path=file_path(url)
            if path.suffix.lower() not in {'.png','.jpg','.jpeg','.webp','.csv'}:
                omitted.append({'report':report['id'],'resource':resource['label'],'reason':'Working archive or non-presentation input'});continue
            if 'outputs' not in path.parts or not path.is_file():raise ValueError('Missing/unexpected linked resource: '+path.name)
            dest='assets/'+report['id']+'/'+path.name
            files[dest]=path.read_bytes();mapping[url]=dest
            kept.append({**resource,'url':dest})
        report['resources']=kept
    def portable_body(body):
        def anchor(m):
            url=html.unescape(m.group(2))
            if url in mapping:return '<a'+m.group(1)+'href="'+html.escape(mapping[url],quote=True)+'"'+m.group(3)+'>'+m.group(4)+'</a>'
            # Local diagnostic files have no public counterpart; retain the report text.
            return m.group(4)
        body=re.sub(r'<a\b([^>]*?)href="((?:file:|http://(?:localhost|127\.0\.0\.1))[^\"]*)"([^>]*)>(.*?)</a>',anchor,body,flags=re.S|re.I)
        # Remove machine-specific filesystem prefixes from displayed code references.
        body=re.sub(r'(?<![\w])(?:file:///)?[A-Za-z]:[/\\][^\s<>"\']+',lambda m:re.split(r'[/\\]',m.group(0))[-1],body)
        return body
    style=re.search(r'<style>(.*?)</style>',original,re.S).group(1)
    for report in data['reports']:
        report['html']=portable_body(report['html'])
        if report.get('embeddedUrl'):
            embedded=report['embeddedUrl']
            if embedded not in ['rv/models.html','rv/trade-review.html']:
                raise ValueError('Unexpected embedded research page: '+embedded)
            files[embedded]=(source/embedded).read_bytes()
            report['source']=embedded
            continue
        report['source']='reports/'+report['id']+'.html'
        # The download is the rendered report, with embedded figures and working web links.
        body=re.sub(r'(href|src)="(assets/[^\"]+)"',r'\1="../\2"',report['html'])
        title=html.escape(report['title']);meta=html.escape(' · '.join(str(report.get(k,'')) for k in ['category','date','badge'] if report.get(k)))
        doc='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+title+' · Research Home</title><style>'+style+'main{max-width:1100px;margin:auto}</style></head><body><main><a href="../index.html#report/'+report['id']+'">← Research Home</a><h1>'+title+'</h1><p class="reader-meta">'+meta+'</p><div class="reader-card"><article class="article">'+body+'</article></div></main></body></html>'
        files[report['source']]=doc.encode('utf-8')
    tracker=source.parent/'rates-paper-tracker/index.html'
    files['tracker/index.html']=read(tracker).encode('utf-8')
    data['trackerUrl']='tracker/index.html'
    serialized=json.dumps(data,ensure_ascii=False).replace('<','\\u003c').replace('\u2028','\\u2028').replace('\u2029','\\u2029')
    page=original[:match.start(1)]+serialized+original[match.end(1):]
    page=page.replace('Original file ↗','Open report ↗')
    page=page.replace('The existing daily process rebuilds this library from saved outputs; reload the page to see the latest build.','Saved updates are prepared locally and published on demand; reload to see the latest published version.')
    page=page.replace('This library build is over 24 hours old. Reload after the next scheduled update; the dates below describe the saved snapshot.','This saved library snapshot is over 24 hours old. The dates below describe its data; refreshing your browser does not fetch new observations.')
    page=page.replace('Bookmark this page for a stable way back.','Bookmark this page for a stable way back.')
    files['index.html']=page.encode('utf-8')
    files['india.html']=(source/'india.html').read_bytes()
    files['.nojekyll']=b''
    # A simple static 404 keeps project-relative navigation correct under /research-home/.
    files['404.html']=b'<!doctype html><html lang="en"><meta charset="utf-8"><title>Page not found</title><h1>Page not found</h1><p><a href="/research-home/">Return to Research Home</a></p></html>'
    manifest={'packagedAt':datetime.now(timezone.utc).isoformat(),'libraryBuiltAt':data['builtAt'],'reports':len(data['reports']),'omittedResources':omitted,'files':[{'path':n,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()} for n,b in sorted(files.items())]}
    # Validate before touching the existing package. Unknown files require review, not deletion.
    from validate_site import check_bytes
    check_bytes(files)
    SITE.mkdir(exist_ok=True)
    allowed=set(files)|{'manifest.json'}
    unknown=[p.relative_to(SITE).as_posix() for p in SITE.rglob('*') if p.is_file() and p.relative_to(SITE).as_posix() not in allowed]
    if unknown:raise ValueError('Review obsolete package files before replacing: '+', '.join(unknown))
    for name,content in files.items():
        target=SITE/name;target.parent.mkdir(parents=True,exist_ok=True)
        temp=target.with_suffix(target.suffix+'.tmp');temp.write_bytes(content);temp.replace(target)
    (SITE/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps({'reports':len(data['reports']),'files':len(files),'bytes':sum(map(len,files.values())),'omittedResources':omitted},indent=2))
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,required=True)
    build(parser.parse_args().source)

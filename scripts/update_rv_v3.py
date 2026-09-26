"""Package committed v3 results into one workspace; never runs models or fetches data."""
import argparse, hashlib, html, json, re, sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from navigation import render_navigation, PAYLOAD
from validate_site import check_bytes

ROOT=Path(__file__).resolve().parents[1]
TEMPLATE=ROOT/'scripts'/'rv_workspace'

def encode(value):
    return json.dumps(value,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode('utf-8')

def build(rvroot):
    state=json.loads((rvroot/'state.json').read_text())
    result=json.loads((rvroot/state['latest_run']).read_text())
    if result['state']!=state:raise ValueError('Run is not the committed state')
    research=result if result['mode']=='research' else json.loads((rvroot/state['latest_research_run']).read_text()) if state.get('latest_research_run') else None
    research_rows={r['id']:r for r in research['rows']} if research else {}
    sys.path.insert(0,str(rvroot.parents[1]))
    from outputs.rates_rv_v3.cache import HistoryReader, DEFAULT_CACHE
    from outputs.rates_rv_v3.universe import universe, frame
    from outputs.rates_rv_v3.models import Fit
    from outputs.rates_rv_v3.qualification import qualify, reconcile_selection, POLICY
    from zoneinfo import ZoneInfo
    selection_path=rvroot/'selection_state.json'
    previous_selection=json.loads(selection_path.read_text()) if selection_path.exists() else None
    selection=reconcile_selection(result['rows'],state.get('ledger',{}),previous_selection,
                                  datetime.now(ZoneInfo('Asia/Singapore')).isoformat())
    admissions=selection['records']
    import numpy as np
    reader=HistoryReader(DEFAULT_CACHE,result['cutoff']); series={}
    for key,record in result['source_manifest'].items():
        if record.get('status')=='ok':
            series[key]=reader.read(key,result['specification']['usd_start'])
            if reader.manifest[key].get('sha256')!=record.get('sha256'):raise ValueError('Cache changed since model run: '+key)
    candidates={c.id:c for c in universe()}
    records=state.get('ledger',{}).get('records',{})
    episodes=state.get('ledger',{}).get('model_episodes',{})
    per_candidate=defaultdict(list)
    for ep in episodes.values():per_candidate[ep['candidate_id']].append(ep)
    groups=defaultdict(list)
    for r in result['rows']:groups[r['structure_id']].append(r)
    files={p.relative_to(ROOT/'site').as_posix():p.read_bytes() for p in (ROOT/'site').rglob('*') if p.is_file() and p.name!='manifest.json'}
    summaries=[]; details={}
    for sid,rows in groups.items():
        first=rows[0]; item={k:first[k] for k in ['structure_id','name','family','ccys','quote_exposure','exposure_note']}
        item['models']=[]; detail={**item,'models':[]}
        for r in rows:
            hist=r.get('historical') or {}; close=hist.get('current'); check=r.get('current_check') or {}
            active=[e for e in per_candidate[r['id']] if e['status'] in ['open','entry_pending','exit_pending']]
            observed=[e for e in records.values() if e['candidate_id']==r['id']]
            compact={k:r.get(k) for k in ['id','model','data_status','active_observed_signal']}
            compact['qualification']={str(d):qualify(r.get('evidence'),d) for d in [1,-1]}
            compact['admissions']={sid:a for sid,a in admissions.items() if a['candidate_id']==r['id']}
            compact.update(close={k:v for k,v in (close or {}).items() if k not in ['fit','scanner_fit']},
                current={k:v for k,v in check.items() if k not in ['fit']},
                episodes=[{k:e.get(k) for k in ['signal_id','model_signal_date','first_observed_at','direction','status']} for e in active],
                observed=[{k:e.get(k) for k in ['signal_id','first_observed_at','first_quote_bp','direction','status','exit_reason','exit_observed_at','tracking_issue']} for e in observed])
            live=next((e for e in observed if e['status']=='active'),None)
            if live:
                mark=live['marks'][-1] if live['marks'] else live['snapshot_provenance']
                compact['tracking']={k:mark.get(k) for k in ['quote_bp','z','target_bp','gross_indication_change_bp']}
                compact['tracking'].update(direction=live['direction'],opportunity_bp=live['direction']*(mark['target_bp']-mark['quote_bp']))
            elif close and active:
                d=active[0]['direction']; target=close['fair_bp']-d*result['specification']['exit_z']*close['sigma_bp']
                compact['tracking']={**compact['close'],'direction':d,'target_bp':target,'opportunity_bp':d*(target-close['quote_bp'])}
            item['models'].append(compact)
            research_row=research_rows.get(r['id'],{})
            model={**compact,'evidence':r.get('evidence'),'bootstrap':research_row.get('bootstrap'),
                'sensitivities':research_row.get('sensitivities'),'unfiltered_diagnostic':research_row.get('unfiltered_diagnostic'),
                'max_drawdown_bp':hist.get('max_drawdown_bp'),'walkforward_start':hist.get('walkforward_start'),
                'history_start':hist.get('history_start'),'observations':hist.get('observations'),
                'trades':[{k:v for k,v in t.items() if k!='fit'} for t in hist.get('trades',[])],
                'timeline':[{k:e.get(k) for k in ['model_signal_date','first_observed_at','direction','status']} for e in per_candidate[r['id']]],
                'observed_history':observed,
                'tickers':r['tickers'],'keys':r['keys'],'fit':(close or {}).get('fit')}
            if hist and close:
                c=candidates[r['id']]; data=frame(c,series).loc[:result['cutoff']].tail(504)
                fitted=Fit(**close['fit']); x=data.to_numpy(float)
                model['diagnostic_chart']={'dates':[str(d.date()) for d in data.index],
                    'quote_bp':np.round(fitted.quote(x),4).tolist(),'fair_bp':np.round(fitted.fair(x),4).tolist(),
                    'z':np.round(fitted.z(x),4).tolist(),
                    'note':'Latest frozen fit applied retrospectively to the last 504 observations. Diagnostic only; this is not the rolling backtest fair-value history.'}
                model['equity_chart']={'dates':hist['daily_dates'],'gross_bp':np.round(np.cumsum(hist['daily_gross_bp']),4).tolist()}
            detail['models'].append(model)
        summaries.append(item); details[sid]=detail
        files['rv/structures/'+sid+'.json']=encode(detail)
    reader.verify()
    index={k:result[k] for k in ['version','accounting','observed_at','cutoff','mode','summary','specification']}
    index['structures']=summaries
    index['selection_policy']=POLICY
    index['selection_evaluated_at']=selection['last_evaluated_at']
    index['selection_summary']={'admitted_episodes':len(admissions),
        'qualified_close_readings':sum(bool((r.get('historical') or {}).get('current',{}).get('eligible') and
             (r.get('historical') or {}).get('current',{}).get('state') in ['open','entry_pending'] and
             qualify(r.get('evidence'),(r.get('historical') or {}).get('current',{}).get('direction'))['passed']) for r in result['rows'])}
    index['research_observed_at']=research['observed_at'] if research else None
    index['held_sources']=[{k:r.get(k) for k in ['ticker','status','last']} for r in result['source_manifest'].values() if r.get('last')!=result['cutoff']]
    files['rv/index.json']=encode(index)
    for name in ['workspace.html','workspace.css','workspace.js']:
        files['rv/'+name]=(TEMPLATE/name).read_bytes()
    page=files['index.html'].decode('utf-8');match=PAYLOAD.search(page); data=json.loads(match[1])
    before=[r for r in data['reports'] if not r['id'].startswith('rates-rv')]
    methodology=(TEMPLATE/'methodology.html').read_text(encoding='utf-8')
    rv={'id':'rates-rv','title':'Rates RV','category':'Monitors','date':result['observed_at'][:10],
        'dataDate':result['cutoff'],'badge':'v3 · gross · 5bp minimum','description':'Daily discovery, persistent tracking and searchable structure reviews.',
        'html':'','source':'reports/rates-rv.html','embeddedUrl':'rv/workspace.html','resources':[]}
    method={'id':'rates-rv-methodology','title':'Rates RV · framework and methodology','category':'Frameworks',
        'date':result['observed_at'][:10],'dataDate':result['cutoff'],'badge':'v3 · 246 structures / 614 models',
        'description':'Universe, calculated forwards, three models, entry rules, gross backtests and persistent tracking.',
        'html':methodology,'source':'reports/rates-rv-methodology.html',
        'resources':[{'label':'Legacy v2 model research (cost-inclusive)','url':'rv/models.html'},
                     {'label':'Legacy v2 original-six study (cost-inclusive)','url':'rv/trade-review.html'}]}
    data['reports']=[rv,method]+before
    data['rv']={**result['summary'],'cutoff':result['cutoff'],'version':'3.0','observed_at':result['observed_at']}
    data['builtAt']=result['observed_at']
    packed=json.dumps(data,ensure_ascii=False).replace('<','\\u003c').replace('\u2028','\\u2028').replace('\u2029','\\u2029')
    files['index.html']=render_navigation(page[:match.start(1)]+packed+page[match.end(1):]).encode('utf-8')
    files['reports/rates-rv.html']=b'<!doctype html><meta charset="utf-8"><title>Rates RV</title><meta http-equiv="refresh" content="0; url=../index.html#report/rates-rv"><a href="../index.html#report/rates-rv">Open Rates RV in Research Home</a>'
    files['reports/rates-rv-methodology.html']=('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Rates RV methodology</title><link rel="stylesheet" href="../rv/workspace.css"><main><a href="../index.html#report/rates-rv-methodology">Research Home</a><h1>Rates RV methodology</h1>'+methodology+'</main></html>').encode('utf-8')
    # No local paths, raw input histories, credentials or cache manifests are exported.
    check_bytes(files)
    manifest=json.loads((ROOT/'site/manifest.json').read_text())
    manifest.update(packagedAt=datetime.now(timezone.utc).isoformat(),libraryBuiltAt=data['builtAt'],reports=len(data['reports']),
        files=[{'path':n,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()} for n,b in sorted(files.items())])
    for name,blob in files.items():
        path=ROOT/'site'/name
        if path.exists() and path.read_bytes()==blob:continue
        path.parent.mkdir(exist_ok=True,parents=True); tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_bytes(blob);tmp.replace(path)
    (ROOT/'site/manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8',newline='\n')
    tmp=selection_path.with_suffix('.tmp');tmp.write_text(json.dumps(selection,indent=2),encoding='utf-8');tmp.replace(selection_path)
    print(json.dumps({'packaged':True,'structures':len(summaries),'bytes':sum(map(len,files.values())),'largest_structure_bytes':max(len(files['rv/structures/'+s+'.json']) for s in details),'published':False}))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--rv-root',type=Path,required=True);build(parser.parse_args().rv_root.resolve())

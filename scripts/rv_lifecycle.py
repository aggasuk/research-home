"""Presentation of admitted episodes from saved ledgers; no model calculation."""
def lifecycle_rows(admissions, episodes, observed, spec):
    rows = []
    for sid, admission in admissions.items():
        ep = observed.get(sid) or episodes.get(sid)
        if not ep:
            continue
        live = sid in observed
        row = {k: ep.get(k) for k in ['signal_id', 'direction', 'status']}
        row.update(first_qualified_at=admission['first_qualified_at'],
                   trigger_date=ep.get('model_signal_date') or ep.get('historical_model_alert'),
                   basis='observed indication' if live else 'reference simulation')
        if live:
            mark = (ep.get('marks') or [ep.get('snapshot_provenance', {})])[-1]
            row.update(entry_at=ep.get('first_observed_at'), entry_quote_bp=ep.get('first_quote_bp'),
                       end_at=ep.get('exit_observed_at') or mark.get('observed_at'),
                       end_quote_bp=mark.get('quote_bp'), gross_bp=mark.get('gross_indication_change_bp'),
                       exit_reason=ep.get('exit_reason'), completed=ep['status']=='exited')
        elif ep.get('trade'):
            t = ep['trade']
            row.update(entry_at=t.get('entry_date'), end_at=t.get('exit_date'),
                       entry_quote_bp=t.get('entry_quote_bp'), end_quote_bp=t.get('exit_quote_bp'),
                       gross_bp=t.get('gross_bp'), exit_reason=t.get('exit_reason'), completed=True)
        else:
            c = ep.get('latest') or {}
            gross, quote, d = c.get('open_gross_bp'), c.get('quote_bp'), ep['direction']
            why = None
            if ep['status']=='exit_pending' and c.get('z') is not None:
                signed = d*c['z']
                why = 'convergence' if signed >= -spec['exit_z'] else 'stop' if signed <= -spec['stop_z'] else 'time'
            if ep['status'].startswith('cancelled'):
                why = ep['status']
            row.update(entry_at=c.get('entry_date'), end_at=c.get('date'),
                       entry_quote_bp=quote-d*gross if quote is not None and gross is not None else None,
                       end_quote_bp=quote, gross_bp=gross, exit_reason=why, completed=False)
        rows.append(row)
    return rows

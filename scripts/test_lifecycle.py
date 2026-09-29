import unittest
from rv_lifecycle import lifecycle_rows

class Lifecycle(unittest.TestCase):
 def rows(self,ep,live=False):
  return lifecycle_rows({'s':{'first_qualified_at':'2026-09-29'}},{} if live else {'s':ep},{'s':ep} if live else {},{'exit_z':.25,'stop_z':3.5})[0]
 def test_closed_uses_own_saved_trade(self):
  r=self.rows(dict(signal_id='s',direction=-1,status='closed',model_signal_date='2026-08-01',trade=dict(entry_date='2026-08-02',exit_date='2026-09-01',entry_quote_bp=10,exit_quote_bp=4,gross_bp=6,exit_reason='convergence'),latest=dict(quote_bp=999,open_gross_bp=-999)))
  self.assertEqual((r['gross_bp'],r['entry_quote_bp'],r['end_quote_bp'],r['completed']),(6,10,4,True))
 def test_pending_stop_is_mark_not_exit(self):
  r=self.rows(dict(signal_id='s',direction=-1,status='exit_pending',latest=dict(z=4,quote_bp=12,open_gross_bp=-2,entry_date='2026-09-25',date='2026-09-28')))
  self.assertEqual((r['exit_reason'],r['gross_bp'],r['entry_quote_bp'],r['completed']),('stop',-2,10,False))
 def test_pending_convergence_and_time(self):
  for z,reason in [(.2,'convergence'),(2,'time')]:
   self.assertEqual(self.rows(dict(signal_id='s',direction=-1,status='exit_pending',latest=dict(z=z)))['exit_reason'],reason)
 def test_cancelled_entry_has_no_performance(self):
  r=self.rows(dict(signal_id='s',direction=1,status='cancelled_data_gap'))
  self.assertIsNone(r['gross_bp']);self.assertFalse(r['completed'])
 def test_observed_is_not_simulated_or_executed(self):
  r=self.rows(dict(signal_id='s',direction=1,status='exited',first_observed_at='2026-09-26',first_quote_bp=10,exit_observed_at='2026-09-29',exit_reason='convergence',marks=[dict(quote_bp=12,gross_indication_change_bp=2)]),True)
  self.assertEqual((r['basis'],r['gross_bp']),('observed indication',2))
 def test_unadmitted_raw_history_excluded(self):
  self.assertEqual(lifecycle_rows({}, {'raw':dict(status='closed')},{},{}),[])

if __name__=='__main__':unittest.main()

import copy,importlib.util,json,unittest,tempfile
from types import SimpleNamespace
from unittest.mock import patch
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('daily_pipeline',ROOT/'automation/pipeline.py');pipeline=importlib.util.module_from_spec(spec);spec.loader.exec_module(pipeline)
INDEX=json.loads((ROOT/'curriculum-index.json').read_text());CONFIG=json.loads((ROOT/'automation/config.json').read_text())
class DailyPlanTests(unittest.TestCase):
 def test_one_upcoming_target_per_batch(self):
  p=pipeline.plan(INDEX,CONFIG,'2026-11-21')
  self.assertEqual(len(p['targets']),3)
  self.assertEqual(len({t['batch'] for t in p['targets']}),3)
  for t in p['targets']:
   self.assertGreaterEqual(t['scheduled_date'],'2026-11-21');self.assertIn(t['duration_minutes'],[90,120]);self.assertFalse(t.get('curriculum_review_required'))
 def test_pending_targets_are_skipped(self):
  first=pipeline.plan(INDEX,CONFIG,'2026-11-21')['targets'];pending={t['path'] for t in first}
  second=pipeline.plan(INDEX,CONFIG,'2026-11-21',pending)['targets']
  self.assertFalse(pending & {t['path'] for t in second})
 def test_ready_and_conflicted_sessions_are_skipped(self):
  idx=copy.deepcopy(INDEX);first=pipeline.plan(idx,CONFIG,'2026-11-21')['targets'][0]
  session=next(s for b in idx['batches'] for m in b['modules'] for s in m['sessions'] if s['path']==first['path']);session['status']='ready'
  result=pipeline.plan(idx,CONFIG,'2026-11-21')
  self.assertNotIn(first['path'],[t['path'] for t in result['targets']])
  session['status']='scaffold';session['curriculum_review_required']=True
  result=pipeline.plan(idx,CONFIG,'2026-11-21');self.assertNotIn(first['path'],[t['path'] for t in result['targets']]);self.assertTrue(result['skipped'])
 def test_empty_and_disabled_do_not_plan_model_calls(self):
  cfg=copy.deepcopy(CONFIG);cfg['enabled']=False
  self.assertEqual(pipeline.plan(INDEX,cfg,'2026-11-21')['targets'],[])
  self.assertEqual(pipeline.plan(INDEX,CONFIG,'2030-01-01')['targets'],[])
 def test_pending_pr_marker(self):
  prs=[{'body':pipeline.MARKER+'["A/path"] -->'},{'body':'unrelated'}]
  self.assertEqual(pipeline.pending_paths(prs),{'A/path'})
 def test_scope_rejects_rules_status_and_traversal_changes(self):
  targets=[{'path':'B/module/lecture'}]
  pipeline.assert_scoped(['B/module/lecture/pre-read.md','B/module/lecture/data/orders.csv'],targets)
  for p in ['AGENTS.md','curriculum-index.json','B/module/lecture/../../bad','B/module/lecture/script.py','/tmp/file']:
   with self.assertRaises(ValueError):pipeline.assert_scoped([p],targets)
 def test_partial_ready_pair_can_still_be_selected(self):
  idx=copy.deepcopy(INDEX);first=pipeline.plan(idx,CONFIG,'2026-11-21')['targets'][0]
  s=next(s for b in idx['batches'] for m in b['modules'] for s in m['sessions'] if s['path']==first['path']);s['pre_read_status']='ready';s['status']='partial'
  self.assertIn(first['path'],[t['path'] for t in pipeline.plan(idx,CONFIG,'2026-11-21')['targets']])
 def test_collect_refuses_to_overwrite_ready_artifact(self):
  with tempfile.TemporaryDirectory() as tmp:
   target={'path':'B/module/lecture','pre_read_status':'ready'}
   (Path(tmp)/'plan.json').write_text(json.dumps({'targets':[target]}))
   with patch.object(pipeline,'changed_paths',return_value=['B/module/lecture/pre-read.md']):
    with self.assertRaisesRegex(ValueError,'already-ready'):
     pipeline.collect(SimpleNamespace(out=tmp))
if __name__=='__main__':unittest.main()

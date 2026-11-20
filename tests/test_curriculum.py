"""Curriculum coverage, export fidelity, and authoring-context regression checks."""
import importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,ROOT/path)
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
sync=load('curriculum_exports','tools/sync_curriculum.py')
context=load('curriculum_context','lecture/tools/curriculum_context.py')
resolver=load('session_resolver','preread/scripts/resolve_session.py')
INDEX=json.loads((ROOT/'curriculum-index.json').read_text())
def sessions(batch):return [(m,s) for m in INDEX['batches'][batch]['modules'] for s in m['sessions']]
class CurriculumTests(unittest.TestCase):
 def test_complete_source_counts(self):
  self.assertEqual([len(sessions(i)) for i in range(3)],[61,56,55])
  self.assertEqual([len(b['modules']) for b in INDEX['batches']],[9,8,10])
 def test_all_paths_unique_and_both_artifacts_exist(self):
  paths=[]
  for i in range(3):
   for m,s in sessions(i):
    paths.append(s['path']);self.assertTrue(s['path'].startswith(m['path']+'/'))
    for artifact in ['pre-read','lecture-script']:self.assertTrue((ROOT/s['path']/(artifact+'.md')).is_file())
    self.assertTrue(s['source']['document']);self.assertTrue(s['source']['pages'])
  self.assertEqual(len(paths),len(set(paths)))
 def test_dsai_module_migration_and_missing_coverage(self):
  batch=INDEX['batches'][1]['batch']
  for sid in ['1.1','10.2','12.2','14.2','16.2','21.2','26.2','28.2']:
   self.assertTrue(Path(resolver.resolve(ROOT,batch,sid)['output_path']).is_file())
  self.assertFalse((ROOT/batch/'module-02-numpy-and-pandas').exists())
  self.assertIn('module-02-data-analysis-with-numpy-and-pandas',resolver.resolve(ROOT,batch,'6.1')['output_path'])
 def test_source_ids_and_duplicates_are_preserved(self):
  batch=INDEX['batches'][0]['batch']
  with self.assertRaisesRegex(ValueError,'Ambiguous'):resolver.resolve(ROOT,batch,'27.1')
  with self.assertRaisesRegex(ValueError,'not found'):resolver.resolve(ROOT,batch,'10.2')
  agent=resolver.resolve(ROOT,batch,'27.1','08');capstone=resolver.resolve(ROOT,batch,'27.1','capstone')
  self.assertNotEqual(agent['output_path'],capstone['output_path'])
  self.assertEqual(resolver.resolve(ROOT,batch,'11.1')['session_name'],'Cleaning Data I: Missing Values and Duplicates')
 def test_metadata_is_available_to_authoring_helpers(self):
  batch=INDEX['batches'][1]['batch'];r=resolver.resolve(ROOT,batch,'25.2')
  self.assertEqual(r['duration_minutes'],120);self.assertIn('RAG',r['topics']);self.assertEqual(len(r['learning_objectives']),4)
  rows=context.read_index(ROOT/'curriculum-index.json',batch)
  target=context.context(rows,context.find_target(rows,session_id='25.2'))
  self.assertEqual(target['target']['objectives'],r['learning_objectives'])
  self.assertEqual(target['target']['duration_minutes'],120);self.assertEqual(target['completed_count'],0)
 def test_unspecified_capstones_are_not_invented(self):
  for i in [0,1]:
   caps=[s for m,s in sessions(i) if m['module_id']=='capstone']
   self.assertEqual(len(caps),4)
   for s in caps:self.assertIsNone(s['duration_minutes']);self.assertEqual(s['learning_objectives'],[])
  self.assertTrue(all(s['scheduled_date'] is None for m,s in sessions(1) if m['module_id']=='capstone'))
 def test_ba_tracker_conflicts_checkbox_and_retained_capstones(self):
  ba={s['source_session']:s for _,s in sessions(2)}
  self.assertEqual(sum(len(s.get('source_learning_objectives',[])) for s in ba.values()),159)
  self.assertTrue(ba['2']['curriculum_review_required']);self.assertIn('KPIs',ba['2']['learning_objectives'][0])
  for s in ba.values():
   self.assertEqual(s['duration_minutes'],90);self.assertEqual(s['delivery_status'],'unknown')
   for lo in s.get('source_learning_objectives',[]):self.assertIs(lo['covered'],False)
  self.assertEqual(len(ba['13']['learning_objectives']),1);self.assertEqual(len(ba['13']['supplemental_learning_objectives']),3)
  self.assertEqual(ba['46']['source']['pages'],[4,5])
  for sid in range(47,56):
   self.assertIn('Calendar.pdf',ba[str(sid)]['source']['document']);self.assertEqual(ba[str(sid)]['learning_objectives'],[])
 def test_generated_exports_match_index_and_csv_is_readable(self):
  for name,text in sync.exports(INDEX).items():self.assertEqual((ROOT/name).read_bytes().decode('utf-8'),text,name)
  for i,b in enumerate(INDEX['batches']):
   _,_,rows=context.read_csv(ROOT/b['batch']/'curriculum.csv')
   self.assertEqual(len(rows),len(sessions(i)))
   self.assertEqual(rows[0]['objectives'],sessions(i)[0][1]['learning_objectives'])
   self.assertEqual(rows[0]['module_id'],b['modules'][0]['module_id'])
   self.assertEqual(context.context(rows,len(rows)-1)['completed_count'],0)
if __name__=='__main__':unittest.main()

import copy,datetime,importlib.util,json,tempfile,unittest,zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
pipeline=load('pipeline','automation/pipeline.py');releases=load('releases','automation/releases.py')
CONFIG=json.loads((ROOT/'automation/config.json').read_text())
def fixture():
 rows=[]
 for sid,date in [('1','2026-11-22'),('2','2026-11-23'),('3','2026-11-27'),('4','2026-11-29'),('5','2026-11-30')]:
  rows.append(dict(source_session=sid,title='Session '+sid,path='B/module/lecture-'+sid,scheduled_date=date,duration_minutes=90,learning_objectives=['One','Two','Three','Four'],topics=[],pre_read_status='scaffold',lecture_script_status='scaffold',status='scaffold'))
 return {'batches':[{'batch':'B','modules':[{'module_id':'01','title':'Module','sessions':rows}]}]}
def config():
 c=copy.deepcopy(CONFIG);c['batches']=['B'];return c
class SchedulingTests(unittest.TestCase):
 def test_pre_read_targets_only_two_days_ahead(self):
  p=pipeline.plan(fixture(),config(),'2026-11-20')
  self.assertEqual([t['source_session'] for t in p['targets']],['1'])
  self.assertEqual(p['targets'][0]['pre_read_release_date'],'2026-11-21')
 def test_manual_date_catchup(self):
  p=pipeline.plan(fixture(),config(),'2026-11-20',session_date='2026-11-23')
  self.assertEqual([t['source_session'] for t in p['targets']],['2'])
 def test_friday_weekly_covers_all_following_week_sessions(self):
  p=pipeline.plan(fixture(),config(),'2026-11-20',mode='lecture-script')
  self.assertEqual([t['source_session'] for t in p['targets']],['2','3','4'])
  self.assertEqual((p['window_start'],p['window_end']),('2026-11-23','2026-11-29'))
 def test_week_boundary_and_year_boundary(self):
  self.assertEqual(pipeline.next_week('2026-11-22'),('2026-11-23','2026-11-29'))
  self.assertEqual(pipeline.next_week('2026-12-31'),('2027-01-04','2027-01-10'))
 def test_readiness_is_per_artifact(self):
  idx=fixture();idx['batches'][0]['modules'][0]['sessions'][1]['pre_read_status']='ready'
  self.assertEqual(len(pipeline.plan(idx,config(),'2026-11-21')['targets']),0)
  self.assertIn('2',[t['source_session'] for t in pipeline.plan(idx,config(),'2026-11-20',mode='lecture-script')['targets']])
 def test_pending_pre_read_does_not_reserve_script(self):
  key='B/module/lecture-2#pre-read'
  self.assertEqual(pipeline.plan(fixture(),config(),'2026-11-21',{key})['targets'],[])
  self.assertIn('2',[t['source_session'] for t in pipeline.plan(fixture(),config(),'2026-11-20',{key},mode='lecture-script')['targets']])
 def test_pre_read_not_blocked_by_lecture_topic_count(self):
  idx=fixture();idx['batches'][0]['modules'][0]['sessions'][1]['learning_objectives']=['One','Two','Three']
  self.assertEqual(len(pipeline.plan(idx,config(),'2026-11-21')['targets']),1)
  self.assertNotIn('2',[t['source_session'] for t in pipeline.plan(idx,config(),'2026-11-20',mode='lecture-script')['targets']])
 def test_disabled_and_conflicts(self):
  cfg=config();cfg['enabled']=False
  self.assertEqual(pipeline.plan(fixture(),cfg,'2026-11-20')['targets'],[])
  idx=fixture();idx['batches'][0]['modules'][0]['sessions'][0]['curriculum_review_required']=True
  p=pipeline.plan(idx,config(),'2026-11-20');self.assertFalse(p['targets']);self.assertTrue(p['skipped'])
 def test_scope_separates_siblings_and_assets(self):
  p=[{'path':'B/module/lecture-1','artifact':'pre-read'}];l=[{'path':'B/module/lecture-1','artifact':'lecture-script'}]
  pipeline.assert_scoped(['B/module/lecture-1/pre-read.md'],p)
  pipeline.assert_scoped(['B/module/lecture-1/lecture-script.md','B/module/lecture-1/data/x.csv'],l)
  for path in ['B/module/lecture-1/lecture-script.md','B/module/lecture-1/data/x.csv','AGENTS.md','../x']:
   with self.assertRaises(ValueError):pipeline.assert_scoped([path],p)
 def test_collect_refuses_ready_artifact_overwrite(self):
  with tempfile.TemporaryDirectory() as tmp:
   t={'path':'B/module/lecture-1','artifact':'pre-read','pre_read_status':'ready'}
   (Path(tmp)/'plan.json').write_text(json.dumps({'targets':[t]}))
   with patch.object(pipeline,'changed_paths',return_value=[t['path']+'/pre-read.md']):
    with self.assertRaisesRegex(ValueError,'already-ready'):pipeline.collect(SimpleNamespace(out=tmp))
class ReleaseTests(unittest.TestCase):
 def test_release_due_day_before_calendar_date(self):
  now=datetime.datetime(2026,11,21,15,0,tzinfo=releases.ZONE)
  due,deadline=releases.preread_due(fixture(),config(),now)
  self.assertEqual([t['source_session'] for t in due],['1']);self.assertEqual(deadline.hour,15)
 def test_no_early_publication(self):
  now=datetime.datetime(2026,11,21,14,59,tzinfo=releases.ZONE)
  with self.assertRaisesRegex(ValueError,'before 15:00'):releases.publish_prereads(fixture(),config(),now,False)
 def test_naive_clock_rejected(self):
  with self.assertRaises(ValueError):releases.preread_due(fixture(),config(),datetime.datetime(2026,11,21,15))
 def test_unapproved_files_never_qualify(self):
  row=fixture()['batches'][0]['modules'][0]['sessions'][0];row['batch']='B'
  with self.assertRaisesRegex(ValueError,'not ready'):releases.ready_file(row,'pre-read')
 def test_pack_contains_calendar_week_not_fixed_count(self):
  start,end,groups=releases.weekly_groups(fixture(),config(),'2026-11-20')
  self.assertEqual(len(groups['B']),3);self.assertEqual(str(end),'2026-11-29')
 def test_late_week_can_be_explicitly_selected(self):
  start,end,groups=releases.weekly_groups(fixture(),config(),'2026-11-24',week_start='2026-11-23')
  self.assertEqual(len(groups['B']),3)
  with self.assertRaises(ValueError):releases.weekly_groups(fixture(),config(),'2026-11-24',week_start='2026-11-24')
 def test_published_release_is_not_overwritten(self):
  result=SimpleNamespace(returncode=0,stdout='{"isDraft":false}',stderr='')
  with patch.object(releases,'run',return_value=result) as mock:
   releases.release('tag','title',Path('asset'),Path('notes'),'sha',False)
   self.assertEqual(mock.call_count,1)
 def test_weekly_zip_preserves_script_assets_and_manifest(self):
  index=fixture();session_rows=index['batches'][0]['modules'][0]['sessions']
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)
   for row in session_rows[1:4]:
    row['lecture_script_status']='ready';lesson=root/row['path'];(lesson/'images').mkdir(parents=True);(lesson/'data').mkdir()
    (lesson/'lecture-script.md').write_text('# Approved lecture')
    (lesson/'images/chart.png').write_bytes(b'chart');(lesson/'data/table.csv').write_text('x\n1\n')
   observed=[]
   def inspect(tag,title,asset,notes,sha,dry_run):
    with zipfile.ZipFile(asset) as archive:
     names=archive.namelist();self.assertEqual(len(json.loads(archive.read('sessions.json'))),3)
     self.assertIn('01-session-2/images/chart.png',names);self.assertIn('01-session-3/data/table.csv',names)
     self.assertFalse(any('pre-read.md' in n for n in names));observed.append(tag)
   with patch.object(releases,'ROOT',root),patch.object(releases,'run',return_value=SimpleNamespace(stdout='sha')),patch.object(releases,'release',side_effect=inspect):
    releases.publish_weekly(index,config(),datetime.datetime(2026,11,20,6,tzinfo=releases.ZONE),True)
   self.assertEqual(len(observed),1)
 def test_weekly_pack_refuses_a_partial_batch(self):
  with patch.object(releases,'run',return_value=SimpleNamespace(stdout='sha')),patch.object(releases,'release') as publish:
   with self.assertRaisesRegex(ValueError,'not ready'):
    releases.publish_weekly(fixture(),config(),datetime.datetime(2026,11,20,6,tzinfo=releases.ZONE),False)
   publish.assert_not_called()
if __name__=='__main__':unittest.main()

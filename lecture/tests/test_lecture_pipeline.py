"""Offline regression checks. Recorded example outputs are not re-executed."""
import contextlib,importlib.util,io,json,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
ctx=load('lecture_context',ROOT/'lecture/tools/curriculum_context.py')
checker=load('lecture_checker',ROOT/'lecture/tools/check_script.py')
resolver=load('session_router',ROOT/'preread/scripts/resolve_session.py')
class ContextTests(unittest.TestCase):
 def test_schedule_and_artifact_ready_are_not_delivery(self):
  rows=[{'title':'One','topics':['A'],'status':''},{'title':'Two','topics':['B'],'status':'ready'},{'title':'Three','topics':['C'],'status':'completed'},{'title':'Target','topics':[]}]
  result=ctx.context(rows,3)
  self.assertEqual(result['completed_count'],1);self.assertEqual(result['all_completed_topics'],['C']);self.assertEqual(len(result['earlier_scheduled_unconfirmed']),2)
 def test_fuzzy_title_is_not_silently_selected(self):
  with self.assertRaisesRegex(ValueError,'exact'): ctx.find_target([{'title':'Selecting data'}],title='Selecting dat')
 def test_duplicate_titles_require_disambiguation(self):
  rows=[{'title':'Capstone','session':'27.1','module_id':'08'},{'title':'Capstone','session':'27.1','module_id':'capstone'}]
  with self.assertRaisesRegex(ValueError,'Ambiguous'): ctx.find_target(rows,title='Capstone')
  self.assertEqual(ctx.find_target(rows,session_id='27.1',module='capstone'),1)
 def test_ambiguous_columns_rejected(self):
  with self.assertRaisesRegex(ValueError,'Ambiguous'): ctx.map_columns(['Title','Session Title','Topics'])
 def test_real_index_status_is_not_course_delivery(self):
  rows=ctx.read_index(ROOT/'curriculum-index.json','IITREICT-AIML-EN-II-2608')
  idx=ctx.find_target(rows,session_id='11.1');self.assertEqual(ctx.context(rows,idx)['completed_count'],0)
 def test_routing_preserves_both_artifacts(self):
  for artifact in ['pre-read','lecture-script']:
   result=resolver.resolve(ROOT,'IITREICT-AIML-EN-II-2608','11.1',artifact=artifact)
   self.assertEqual(Path(result['output_path']).name,artifact+'.md')
 def test_csv_requires_explicit_completion(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'c.csv';p.write_text('Session,Title,Topics\n1,First,Arrays\n2,Second,DataFrames\n')
   _,_,rows=ctx.read_csv(p);self.assertEqual(ctx.context(rows,1)['completed_count'],0)
 def test_columns_work_even_when_required_names_are_missing(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'c.csv';p.write_text('Unknown Header,Other\nA,B\n')
   output=io.StringIO()
   with contextlib.redirect_stdout(output): code=ctx.main([str(p),'--columns'])
   self.assertEqual(code,0);self.assertEqual(json.loads(output.getvalue())['header'],['Unknown Header','Other'])
 def test_cli_missing_match_exits_two(self):
  result=subprocess.run([sys.executable,'-I',str(ROOT/'lecture/tools/curriculum_context.py'),'--index',str(ROOT/'curriculum-index.json'),'--batch','IITREICT-AIML-EN-II-2608','--session-id','999'],capture_output=True,text=True)
  self.assertEqual(result.returncode,2);self.assertIn('ASK:',result.stdout)
class CheckerTests(unittest.TestCase):
 def check(self,path,extra=None):
  output=io.StringIO()
  with contextlib.redirect_stdout(output): code=checker.main(['check_script.py',str(path),*(extra or [])])
  return code,output.getvalue()
 def test_all_three_pack_examples_have_no_structural_failures(self):
  for p in (ROOT/'lecture/examples').glob('*/lecture_script.md'):
   code,output=self.check(p);self.assertEqual(code,0,output)
 def test_missing_output_is_a_failure(self):
  source=ROOT/'lecture/examples/Example_1_Probability_Distributions/lecture_script.md'
  with tempfile.TemporaryDirectory(dir=source.parent) as tmp:
   p=Path(tmp)/'script.md';p.write_text(source.read_text().replace('**Output**','**Recorded result**',1))
   _,output=self.check(p);self.assertIn('block is not followed by **Output**',output)
 def test_nonagenda_numeric_rows_do_not_change_pacing(self):
  source=ROOT/'lecture/examples/Example_1_Probability_Distributions/lecture_script.md'
  # Reuse the example directory so valid sibling assets resolve.
  p=source.parent/'test-script-temporary.md'
  try:
   p.write_text(source.read_text().replace('### <font color=\'purple\'>Quiz 1', '| 1 | Observed items | 7 |\n\n### <font color=\'purple\'>Quiz 1',1))
   code,output=self.check(p);self.assertEqual(code,0,output)
  finally: p.unlink(missing_ok=True)
 def test_lo_matches_whole_agenda_item_not_substring(self):
  source=ROOT/'lecture/examples/Example_1_Probability_Distributions/lecture_script.md';p=source.parent/'test-script-temporary.md'
  lo='Classify a random variable as discrete or continuous'
  try:
   p.write_text(source.read_text().replace('Compute a binomial probability for a stated number of successes','Explain how to '+lo,1))
   code,output=self.check(p,['--los',lo]);self.assertEqual(code,0,output)
  finally: p.unlink(missing_ok=True)
 def test_duplicate_quiz_option_label_fails(self):
  source=ROOT/'lecture/examples/Example_1_Probability_Distributions/lecture_script.md';p=source.parent/'test-script-temporary.md'
  try:
   p.write_text(source.read_text().replace('- B) ','- A) ',1))
   _,output=self.check(p);self.assertIn('needs unique options A to D',output)
  finally: p.unlink(missing_ok=True)
 def test_wrong_duration_and_announcement_flag_fail(self):
  source=ROOT/'lecture/examples/Example_1_Probability_Distributions/lecture_script.md'
  p=source.parent/'test-script-temporary.md'
  try:
   p.write_text(source.read_text().replace('| 15 |','| 16 |',1))
   _,output=self.check(p,['--announcements','no']);self.assertIn('Agenda minutes',output);self.assertIn('Announcements = No',output)
  finally: p.unlink(missing_ok=True)
class RegistrationTests(unittest.TestCase):
 def test_codex_roles_have_required_string_fields(self):
  for name in ['agent_lecture_creator','agent_lecture_verifier']:
   values={k.strip():json.loads(v.strip()) for k,v in (line.split('=',1) for line in (ROOT/'.codex/agents'/f'{name}.toml').read_text().splitlines())}
   self.assertEqual(set(values),{'name','description','developer_instructions'});self.assertEqual(values['name'],name)
if __name__=='__main__': unittest.main()

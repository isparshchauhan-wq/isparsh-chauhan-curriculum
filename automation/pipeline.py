#!/usr/bin/env python3
"""Plan a daily curriculum run and publish only its scoped lesson changes."""
import argparse,datetime,importlib.util,json,os,re,subprocess,sys
from pathlib import Path
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parents[1]
MARKER='<!-- daily-curriculum-targets: '
def command(*args,check=True):
 return subprocess.run(args,cwd=ROOT,text=True,capture_output=True,check=check)
def read(path):return json.loads(Path(path).read_text())
def save(path,value):
 p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def pending_paths(prs):
 result=set()
 for pr in prs:
  match=re.search(re.escape(MARKER)+r'(.*?) -->',pr.get('body') or '')
  if match:result.update(json.loads(match[1]))
 return result
def next_week(today):
 d=datetime.date.fromisoformat(today)
 start=d+datetime.timedelta(days=7-d.weekday())
 return start.isoformat(),(start+datetime.timedelta(days=6)).isoformat()
def artifact_key(target):return target['path']+'#'+target.get('artifact','pre-read')
def plan(index,config,today,pending=(),mode='pre-read',session_date=None):
 if mode not in ('pre-read','lecture-script'):raise ValueError('Unsupported generation mode')
 targets=[];skipped=[]
 if not config['enabled']:return dict(date=today,mode=mode,targets=[],skipped=['Automation disabled'])
 if session_date:datetime.date.fromisoformat(session_date)
 if mode=='pre-read':
  start=end=session_date or (datetime.date.fromisoformat(today)+datetime.timedelta(days=config['pre_read']['generation_lead_days'])).isoformat()
 else:start,end=next_week(today)
 for b in index['batches']:
  if b['batch'] not in config['batches']:continue
  for m in b['modules']:
   for row in m['sessions']:
    if not row.get('scheduled_date') or not start<=row['scheduled_date']<=end:continue
    target=dict(batch=b['batch'],module_id=m['module_id'],module=m['title'],artifact=mode,**row)
    if row.get('pre_read_status' if mode=='pre-read' else 'lecture_script_status')=='ready':continue
    if artifact_key(target) in pending or row['path'] in pending:continue
    reason=None
    if row.get('curriculum_review_required'):reason='Unresolved source title/objective alignment'
    elif not row.get('learning_objectives'):reason='Source objectives missing'
    elif mode=='lecture-script' and row.get('duration_minutes') not in (90,120):reason='Missing or unsupported source duration'
    elif mode=='lecture-script' and not 4<=len(row['learning_objectives'])<=8:reason='Four-topic LO grouping needs an explicit coverage plan'
    if reason:
     skipped.append(dict(batch=b['batch'],session=row['source_session'],reason=reason));continue
    target['pre_read_release_date']=(datetime.date.fromisoformat(row['scheduled_date'])-datetime.timedelta(days=config['pre_read']['release_lead_days'])).isoformat()
    targets.append(target)
 return dict(date=today,mode=mode,window_start=start,window_end=end,targets=targets,skipped=skipped)
def assert_scoped(paths,targets):
 for name in paths:
  p=Path(name)
  if p.is_absolute() or '..' in p.parts:raise ValueError('Unsafe changed path: '+name)
  def allowed(t):
   artifact=t.get('artifact','pre-read')
   return name==t['path']+'/'+artifact+'.md' or (artifact=='lecture-script' and (name.startswith(t['path']+'/images/') or name.startswith(t['path']+'/data/')))
  if not any(allowed(t) for t in targets):raise ValueError('Unexpected change outside the selected artifact: '+name)
def changed_paths():
 tracked=command('git','diff','--name-only','HEAD','-z').stdout.split('\0')
 untracked=command('git','ls-files','--others','--exclude-standard','-z').stdout.split('\0')
 return [p for p in tracked+untracked if p]
def check_target(t):
 problems=[]
 for filename in [t.get('artifact','pre-read')+'.md']:
  p=ROOT/t['path']/filename
  if not p.is_file() or 'Status: scaffold' in p.read_text():problems.append(filename+' remains a scaffold');continue
  if filename=='pre-read.md':args=[sys.executable,'-I',str(ROOT/'preread/scripts/check_preread.py'),'--file',str(p),'--setup','No','--root',str(ROOT)]
  else:args=[sys.executable,'-I',str(ROOT/'lecture/tools/check_script.py'),str(p),'--los',';'.join(t['learning_objectives']),'--announcements','no','--module',t['module'],'--session',t['title'],'--duration',str(t['duration_minutes'])]
  r=command(*args,check=False)
  if r.returncode:problems.append(filename+' checker failed: '+r.stdout[-4000:]+r.stderr[-1000:])
 return problems
def prepare(args):
 config=read(ROOT/'automation/config.json');index=read(ROOT/'curriculum-index.json')
 today=args.date or datetime.datetime.now(ZoneInfo(config['timezone'])).date().isoformat()
 prs=json.loads(command('gh','pr','list','--state','open','--limit','1000','--json','body,headRefName').stdout)
 branch='content/'+args.mode+'-'+today
 existing_branch=command('git','ls-remote','--heads','origin',branch).stdout.strip()
 if any(p['headRefName']==branch for p in prs) or existing_branch:
  p=dict(date=today,mode=args.mode,targets=[],skipped=['A run pull request or remote branch already exists; inspect it before retrying'])
 elif args.mode=='lecture-script' and os.environ.get('REQUESTED_MODE','auto')=='auto' and datetime.date.fromisoformat(today).weekday()!=4:
  p=dict(date=today,mode=args.mode,targets=[],skipped=['Weekly lecture generation runs on Friday; use manual lecture-script mode to override'])
 else:p=plan(index,config,today,pending_paths(prs),args.mode,args.session_date)
 p['branch']=branch;p['base_sha']=command('git','rev-parse','HEAD').stdout.strip()
 out=Path(args.out);out.mkdir(parents=True,exist_ok=True);save(out/'plan.json',p)
 instructions=(ROOT/'automation/prompt.md').read_text()
 (out/'prompt.md').write_text(instructions+'\n\n## Exact run plan\n\n```json\n'+json.dumps(p,ensure_ascii=False,indent=2)+'\n```\n')
 if os.environ.get('GITHUB_OUTPUT'):
  with open(os.environ['GITHUB_OUTPUT'],'a') as f:f.write('has_work='+str(bool(p['targets'])).lower()+'\n')
 print(json.dumps(p,ensure_ascii=False,indent=2))
def collect(args):
 out=Path(args.out);p=read(out/'plan.json');paths=changed_paths();assert_scoped(paths,p['targets'])
 for t in p['targets']:
  for artifact,key in [('pre-read.md','pre_read_status'),('lecture-script.md','lecture_script_status')]:
   if t.get(key)=='ready' and t['path']+'/'+artifact in paths:raise ValueError('An already-ready artifact was changed')
  if t.get('lecture_script_status')=='ready' and any(x.startswith(t['path']+'/images/') or x.startswith(t['path']+'/data/') for x in paths):raise ValueError('Already-ready lecture assets were changed')
 for name in paths:
  if (ROOT/name).is_symlink():raise ValueError('Symlinks are not supported in generated assets')
 report_path=out/'review.json'
 if not report_path.is_file():raise ValueError('Agent did not provide the required review report')
 report=read(report_path)
 if set(report)!=set(t['path'] for t in p['targets']):raise ValueError('Report targets differ from run plan')
 for t in p['targets']:
  item=report[t['path']]
  if item.get('status') not in ('accepted','needs_verification','blocked'):raise ValueError('Invalid review status')
  failures=check_target(t)
  if failures:item['status']='needs_verification';item.setdefault('unverified_checks',[]).extend(failures)
  if item.get('status')=='accepted' and (item.get('unverified_checks') or not item.get('evidence')):
   item['status']='needs_verification';item.setdefault('unverified_checks',[]).append('Acceptance evidence incomplete')
 save(report_path,report)
 paths=changed_paths()
 if not paths:raise ValueError('No lesson changes produced; see review report')
 command('git','add','--',*paths)
 patch=command('git','diff','--cached','--binary','--full-index').stdout
 (out/'changes.patch').write_text(patch)
 # Do not publish secrets, prompts, environment files or caches in the artifact.
 (out/'prompt.md').unlink(missing_ok=True)
def publish(args):
 out=Path(args.out);p=read(out/'plan.json');report=read(out/'review.json')
 # Apply against the exact generation base; no force pushes or overwrites of main.
 command('git','checkout','--detach',p['base_sha'])
 command('git','apply','--index',str((out/'changes.patch').resolve()))
 paths=command('git','diff','--cached','--name-only','-z').stdout.split('\0')
 assert_scoped([x for x in paths if x],p['targets'])
 index=read(ROOT/'curriculum-index.json')
 for t in p['targets']:
  s=next(s for b in index['batches'] if b['batch']==t['batch'] for m in b['modules'] if m['module_id']==t['module_id'] for s in m['sessions'] if s['source_session']==t['source_session'])
  item=report[t['path']];accepted=item['status']=='accepted' and not item.get('unverified_checks') and bool(item.get('evidence'))
  problems=check_target(t)
  if problems:accepted=False;item['status']='needs_verification';item.setdefault('unverified_checks',[]).extend(problems)
  key='pre_read_status' if t['artifact']=='pre-read' else 'lecture_script_status'
  s[key]='ready' if accepted else 'needs_verification'
  s['status']='ready' if s.get('pre_read_status')==s.get('lecture_script_status')=='ready' else 'partial'
 save(ROOT/'curriculum-index.json',index)
 command(sys.executable,'tools/sync_curriculum.py')
 command('git','add','curriculum-index.json',*[b['batch'] for b in index['batches']])
 command('git','config','user.name','github-actions[bot]');command('git','config','user.email','41898282+github-actions[bot]@users.noreply.github.com')
 command('git','checkout','-b',p['branch'])
 command('git','commit','-m','Prepare '+p['mode']+' drafts for '+p['date'])
 existing=command('git','ls-remote','--heads','origin',p['branch']).stdout
 if existing:raise ValueError('Daily branch already exists; inspect it before retrying')
 command('git','push','origin',p['branch'])
 body=['Scheduled '+p['mode']+' drafts. Human review and merge are required before release.','',MARKER+json.dumps([artifact_key(t) for t in p['targets']])+' -->','']
 for t in p['targets']:
  item=report[t['path']];body.extend(['### '+t['batch']+' — '+t['source_session']+' — '+t['title'],f"Source duration: {t['duration_minutes']} minutes. Verification: {item['status']}.",'',json.dumps(item,ensure_ascii=False,indent=2),''])
 if p['skipped']:body.extend(['Skipped curriculum conflicts:','```json',json.dumps(p['skipped'],indent=2),'```'])
 bodyfile=out/'pr-body.md';bodyfile.write_text('\n'.join(body))
 r=command('gh','pr','create','--base',os.environ.get('DEFAULT_BRANCH','main'),'--head',p['branch'],'--draft','--title',p['mode']+' drafts — '+p['date'],'--body-file',str(bodyfile.resolve()))
 print(r.stdout)
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('stage',choices=['plan','collect','publish']);ap.add_argument('--out',required=True);ap.add_argument('--date');ap.add_argument('--mode',choices=['pre-read','lecture-script'],default='pre-read');ap.add_argument('--session-date');args=ap.parse_args()
 {'plan':prepare,'collect':collect,'publish':publish}[args.stage](args)
if __name__=='__main__':main()

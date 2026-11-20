#!/usr/bin/env python3
"""Release approved pre-reads at 15:00 IST; assemble approved weekly instructor packs."""
import argparse,datetime,hashlib,importlib.util,json,os,shutil,subprocess,tempfile,time,zipfile
from pathlib import Path
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parents[1]
ZONE=ZoneInfo('Asia/Kolkata')
def run(*args,check=True):return subprocess.run(args,cwd=ROOT,text=True,capture_output=True,check=check)
def load():return json.loads((ROOT/'curriculum-index.json').read_text()),json.loads((ROOT/'automation/config.json').read_text())
def week_window(today):
 d=datetime.date.fromisoformat(today);start=d+datetime.timedelta(days=7-d.weekday());return start,start+datetime.timedelta(days=6)
def rows(index,batches):
 return [dict(batch=b['batch'],module_id=m['module_id'],module=m['title'],**s) for b in index['batches'] if b['batch'] in batches for m in b['modules'] for s in m['sessions']]
def preread_due(index,config,now):
 if now.tzinfo is None:raise ValueError('A timezone-aware clock is required')
 local=now.astimezone(ZONE);target=(local.date()+datetime.timedelta(days=config['pre_read']['release_lead_days'])).isoformat()
 deadline=local.replace(hour=15,minute=0,second=0,microsecond=0)
 return [s for s in rows(index,config['batches']) if s.get('scheduled_date')==target],deadline

def weekly_groups(index,config,today,week_start=None):
 start,end=week_window(today)
 if week_start:
  start=datetime.date.fromisoformat(week_start)
  if start.weekday()!=0:raise ValueError('week-start must be a Monday')
  end=start+datetime.timedelta(days=6)
 groups={}
 for s in rows(index,config['batches']):
  if s.get('scheduled_date') and start.isoformat()<=s['scheduled_date']<=end.isoformat():groups.setdefault(s['batch'],[]).append(s)
 return start,end,groups

def release(tag,title,asset,notes,sha,dry_run):
 if dry_run:print('DRY RUN: '+tag+' / '+str(asset));return
 viewed=run('gh','release','view',tag,'--json','isDraft',check=False)
 if viewed.returncode:
  if not any(term in (viewed.stdout+viewed.stderr).lower() for term in ['release not found','404','not found']):raise RuntimeError(viewed.stderr)
  run('gh','release','create',tag,'--draft','--latest=false','--target',sha,'--title',title,'--notes-file',str(notes))
 elif not json.loads(viewed.stdout)['isDraft']:
  print('Already published: '+tag);return
 else:run('gh','release','edit',tag,'--title',title,'--notes-file',str(notes))
 run('gh','release','upload',tag,str(asset),'--clobber')
 run('gh','release','edit',tag,'--draft=false','--latest=false')
 print('Published: '+tag)
def ready_file(s,artifact):
 key='pre_read_status' if artifact=='pre-read' else 'lecture_script_status'
 p=ROOT/s['path']/(artifact+'.md')
 if s.get(key)!='ready':raise ValueError(s['batch']+' '+s['source_session']+': '+key+' is not ready on main')
 if not p.is_file() or 'Status: scaffold' in p.read_text():raise ValueError('Missing or scaffold content: '+str(p))
 return p

def publish_prereads(index,config,now,dry_run):
 due,deadline=preread_due(index,config,now)
 if now.astimezone(ZONE)<deadline and not dry_run:raise ValueError('Refusing to publish before 15:00 IST')
 sha=run('git','rev-parse','HEAD').stdout.strip();failures=[]
 for s in due:
  try:
   source=ready_file(s,'pre-read')
   check=run('python3','-I','preread/scripts/check_preread.py','--file',str(source),'--setup','No','--root',str(ROOT),check=False)
   if check.returncode:raise ValueError('Pre-read structural verification failed: '+check.stdout)
   with tempfile.TemporaryDirectory() as folder:
    base=Path(folder);asset=base/(s['batch']+'-session-'+s['source_session']+'-pre-read.md');shutil.copyfile(source,asset)
    notes=base/'notes.md';digest=hashlib.sha256(source.read_bytes()).hexdigest()
    notes.write_text(f"# {s['title']}\n\nBatch: {s['batch']}\n\nSession: {s['source_session']}\n\nClass date: {s['scheduled_date']}\n\nPlanned release: {deadline.isoformat()}\n\nRelease attempt: {now.astimezone(ZONE).isoformat()}\n\nApproved source commit: {sha}\n\nSHA-256: {digest}\n")
    tag=f"pre-read/{s['batch']}/{s['module_id']}/{s['source_session']}/{s['scheduled_date']}"
    release(tag,s['batch']+' '+s['source_session']+' — Pre-read',asset,notes,sha,dry_run)
  except (ValueError,RuntimeError,subprocess.CalledProcessError) as exc:failures.append(str(exc))
 if failures:raise ValueError('\n'.join(failures))
 print('Due pre-reads: '+str(len(due)))

def publish_weekly(index,config,now,dry_run,week_start=None):
 start,end,groups=weekly_groups(index,config,now.astimezone(ZONE).date().isoformat(),week_start)
 sha=run('git','rev-parse','HEAD').stdout.strip();failures=[]
 for batch,sessions in groups.items():
  try:
   # An instructor's pack is complete for the calendar week, never a silently partial subset.
   for s in sessions:ready_file(s,'lecture-script')
   with tempfile.TemporaryDirectory() as folder:
    base=Path(folder);asset=base/f'{batch}-instructor-pack-{start}.zip';manifest=[]
    with zipfile.ZipFile(asset,'w',zipfile.ZIP_DEFLATED) as package:
     for s in sessions:
      lesson=ROOT/s['path'];prefix=f"{s['module_id']}-session-{s['source_session']}"
      files=[lesson/'lecture-script.md']
      for sub in ['images','data']:
       if (lesson/sub).exists():files.extend(p for p in (lesson/sub).rglob('*') if p.is_file())
      for p in files:
       if p.is_symlink() or not p.resolve().is_relative_to(lesson.resolve()):raise ValueError('Unsafe pack asset path')
       package.write(p,prefix+'/'+str(p.relative_to(lesson)))
      manifest.append(dict(session=s['source_session'],title=s['title'],date=s['scheduled_date'],minutes=s.get('duration_minutes')))
     package.writestr('sessions.json',json.dumps(manifest,ensure_ascii=False,indent=2))
    notes=base/'notes.md';notes.write_text(f'# Instructor pack: {batch}\n\nTeaching week: {start} through {end}\n\nApproved source commit: {sha}\n\n'+json.dumps(manifest,ensure_ascii=False,indent=2))
    release(f'instructor-pack/{batch}/{start}',f'{batch} — Instructor pack {start}',asset,notes,sha,dry_run)
  except (ValueError,RuntimeError,subprocess.CalledProcessError) as exc:failures.append(str(exc))
 if failures:raise ValueError('\n'.join(failures))
 print('Batch packs considered: '+str(len(groups)))

def wait_for_release():
 now=datetime.datetime.now(ZONE);deadline=now.replace(hour=15,minute=0,second=0,microsecond=0)
 remaining=(deadline-now).total_seconds()
 if remaining>35*60:raise ValueError('Release wait starts at most 35 minutes before 15:00; use dry-run for earlier tests')
 while remaining>0:
  time.sleep(min(30,remaining));remaining=(deadline-datetime.datetime.now(ZONE)).total_seconds()

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mode',choices=['pre-read','weekly']);ap.add_argument('--dry-run',action='store_true');ap.add_argument('--wait',action='store_true');ap.add_argument('--week-start');args=ap.parse_args()
 if args.wait:
  wait_for_release()
  # Refresh approval/source state after waiting, so revoked readiness is not released.
  run('git','fetch','origin',os.environ.get('DEFAULT_BRANCH','main'))
  run('git','checkout','--detach','FETCH_HEAD')
 index,config=load()
 if not config['enabled']:print('Automation disabled');return
 now=datetime.datetime.now(ZONE)
 if args.mode=='pre-read':publish_prereads(index,config,now,args.dry_run)
 else:publish_weekly(index,config,now,args.dry_run,args.week_start)
if __name__=='__main__':main()

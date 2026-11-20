#!/usr/bin/env python3
"""Regenerate batch references from curriculum-index.json; never change lesson files."""
import argparse,csv,io,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def exports(index):
 result={}
 def write(path,text):result[str(path)]=text
 for b in index['batches']:
  batch=b['batch'];total=sum(len(m['sessions']) for m in b['modules'])
  batchlines=[f'# {batch}','',b['coverage'],'',f'Source: `{b["source"]}`. See [mapping decisions](../SOURCES.md).','',f'{total} session folders. Lesson files remain scaffolds until authored and verified. Source dates do not establish delivery.','', '[Curriculum detail](curriculum.md) · [JSON](curriculum.json) · [CSV](curriculum.csv)','']
  detail=[f'# {batch} — Source curriculum','', 'Source-aligned objectives and schedule metadata. This is an authoring reference; lesson scaffolds are not completed teaching material.','']
  flat=[]
  for m in b['modules']:
   mname=m['title'];mid=m['module_id'];mp=Path(m['path'])
   batchlines.extend([f'## Module {mid.upper()} — {mname}','','| Session | Lecture | Minutes | Source date | Pre-read | Lecture script |','| --- | --- | ---: | --- | --- | --- |'])
   modlines=[f'# {mname}','',f'- Batch: {batch}',f'- Module: {mid}',f'- Source: {b["source"]}','','| Session | Lecture |','| --- | --- |']
   detail.extend([f'## Module {mid.upper()} — {mname}',''])
   for s in m['sessions']:
    p=Path(s['path']);rel=p.relative_to(batch);lesson=p.name;dur=s['duration_minutes'];date=s['scheduled_date']
    title=s['title'].replace('|','\\|')
    batchlines.append(f'| {s["source_session"]} | {title} | {dur if dur is not None else "Unspecified"} | {date or "Unspecified"} | [Pre-read]({rel}/pre-read.md) | [Script]({rel}/lecture-script.md) |')
    modlines.append(f'| {s["source_session"]} | [{title}]({lesson}/) |')
    detail.extend([f'### {s["source_session"]} — {s["title"]}','',f'- Source: `{s["source"]["document"]}`, page(s) {", ".join(map(str,s["source"]["pages"]))}',f'- Scheduled date: {date or "Unspecified"}; duration: {str(dur)+" minutes" if dur else "Unspecified"}',f'- Delivery: {s["delivery_status"]}; material: {s["status"]}','', '**Source learning objectives**',''])
    detail.extend(['- '+x for x in s['learning_objectives']] or ['Unspecified in source.'])
    if s.get('supplemental_learning_objectives'):
     detail.extend(['','**User-supplied additional objectives**','']+['- '+x for x in s['supplemental_learning_objectives']])
    if s['topics']:detail.extend(['','**Source topics**','', '; '.join(s['topics'])])
    if s['authoring_notes']:detail.extend(['','**Authoring notes**','']+['- '+x for x in s['authoring_notes']])
    detail.append('')
    flat.append(dict(batch=batch,module_id=mid,module=mname,source_session=s['source_session'],title=s['title'],topics='; '.join(s['topics']),learning_objectives='; '.join(s['learning_objectives']),scheduled_date=date or '',duration_minutes=dur if dur is not None else '',delivery_status=s['delivery_status'],artifact_status=s['status'],path=s['path'],source_document=s['source']['document'],source_pages='; '.join(map(str,s['source']['pages'])),authoring_notes='; '.join(s['authoring_notes'])))
   batchlines.append('');write(mp/'README.md','\n'.join(modlines)+'\n')
  write(f'{batch}/README.md','\n'.join(batchlines)+'\n')
  write(f'{batch}/curriculum.md','\n'.join(detail)+'\n')
  write(f'{batch}/curriculum.json',json.dumps(b,ensure_ascii=False,indent=2)+'\n')
  out=io.StringIO(newline='');wr=csv.DictWriter(out,fieldnames=list(flat[0]));wr.writeheader();wr.writerows(flat)
  write(f'{batch}/curriculum.csv',out.getvalue())
 return result

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--check',action='store_true',help='Report outdated files without changing them')
 args=parser.parse_args()
 index=json.loads((ROOT/'curriculum-index.json').read_text())
 stale=[]
 for name,text in exports(index).items():
  path=ROOT/name
  current=path.read_bytes().decode('utf-8') if path.is_file() else None
  if current==text:continue
  stale.append(name)
  if not args.check:
   path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(text.encode('utf-8'))
 if args.check and stale:
  print('Outdated exports: '+', '.join(stale));return 1
 print(('Checked' if args.check else 'Refreshed')+' curriculum exports: '+str(len(stale))+' changed')
 return 0
if __name__=='__main__':raise SystemExit(main())

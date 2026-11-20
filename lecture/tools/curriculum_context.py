#!/usr/bin/env python3
"""Read exact curriculum context. Only explicit delivery status establishes completion; exit 2 requests clarification."""
import argparse,csv,difflib,json,re,sys
ALIASES={
 'title':['session title','session name','session_name','title','lecture title','lecture'],
 'topics':['topics covered','topics','subtopics','concepts','topic','description'],
 'objectives':['learning objectives','learning objective','lo_statement','los','objectives','objective'],
 'module':['module','module name','module number','module_name','module_id'],
 'session':['session','session number','session no','session_no','source_session','#'],
 'date':['date','session date'],
 'status':['delivery status','delivery_status','coverage status','status','state'],
 'batch':['batch','batch id','batch_id']}
DONE_WORDS={'done','completed','complete','covered','delivered','yes','taught'}
def norm(value): return re.sub(r'\s+',' ',str(value or '')).strip().lower()
def split_items(value): return [x.strip() for x in re.split(r'[;\n]',value or '') if x.strip()]
def map_columns(header):
 found={}
 for key,names in ALIASES.items():
  matches=[h for h in header if norm(h) in names]
  if len(matches)>1: raise ValueError('Ambiguous columns for '+key+': '+', '.join(matches))
  if matches: found[key]=matches[0]
 return found

def find_target(rows,title=None,session_id=None,module=None):
 matches=[i for i,r in enumerate(rows) if (title is None or norm(r.get('title'))==norm(title)) and (session_id is None or str(r.get('session',''))==session_id) and (module is None or norm(module) in [norm(r.get('module')),norm(r.get('module_id'))])]
 if len(matches)==1: return matches[0]
 if matches: raise ValueError('Ambiguous session; supply source session ID and module')
 suggestions=difflib.get_close_matches(norm(title),[norm(r.get('title')) for r in rows],n=3,cutoff=.4) if title else []
 raise ValueError('No exact session match.'+(' Possible titles: '+'; '.join(suggestions) if suggestions else ''))

def read_csv(path,validate=True):
 with open(path,newline='',encoding='utf-8-sig') as f:
  rd=csv.DictReader(f); header=[h for h in rd.fieldnames or [] if h is not None]; mapping=map_columns(header)
  if validate and not {'title','topics'}<=mapping.keys(): raise ValueError('CSV requires unambiguous title and topics columns')
  rows=[]
  for raw in rd:
   row={key:(raw.get(col) or '').strip() for key,col in mapping.items()}
   for key in ['topics','objectives']: row[key]=split_items(row.get(key))
   rows.append(row)
 return header,mapping,rows

def read_index(path,batch):
 if not batch: raise ValueError('--batch is required for an index')
 with open(path,encoding='utf-8') as f: data=json.load(f)
 matches=[b for b in data['batches'] if b['batch']==batch]
 if len(matches)!=1: raise ValueError('Unknown or ambiguous batch')
 return [{'batch':batch,'title':s['title'],'session':str(s['source_session']),'module':m['title'],'module_id':m['module_id'],'topics':s.get('topics',[]),'objectives':s.get('learning_objectives',[]),'status':s.get('delivery_status',''),'path':s['path']} for m in matches[0]['modules'] for s in m['sessions']]

def context(rows,idx,last=8):
 if last<0: raise ValueError('--last must be nonnegative')
 before=rows[:idx]; done=[r for r in before if norm(r.get('status')) in DONE_WORDS]
 return {'target':rows[idx],'completed_count':len(done),'completed_basis':'only earlier rows explicitly marked delivered/completed','most_recent_completed':done[-last:] if last else [],'all_completed_topics':list(dict.fromkeys(t for r in done for t in r.get('topics',[]))),'earlier_scheduled_unconfirmed':[r for r in before if norm(r.get('status')) not in DONE_WORDS],'next_session':rows[idx+1] if idx+1<len(rows) else None,'notes':['Scheduling and artifact readiness do not prove delivery. Missing topic/objective fields remain unknown.']}

def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('csv_path',nargs='?');p.add_argument('session_name',nargs='?')
 for key in ['index','batch','session-id','module']: p.add_argument('--'+key)
 p.add_argument('--columns',action='store_true');p.add_argument('--json',action='store_true');p.add_argument('--last',type=int,default=8)
 a=p.parse_args(argv)
 try:
  if bool(a.index)==bool(a.csv_path): raise ValueError('Supply exactly one CSV path or --index')
  if a.index:
   if a.columns: raise ValueError('--columns applies to CSV only')
   rows=read_index(a.index,a.batch); mapping=None
  else:
   header,mapping,rows=read_csv(a.csv_path,validate=not a.columns)
   if a.columns: print(json.dumps({'header':header,'mapping':mapping},indent=2));return 0
   if a.batch:
    if 'batch' not in mapping: raise ValueError('CSV has no batch column; confirm the intended batch')
    rows=[r for r in rows if r.get('batch')==a.batch]
   elif len({r.get('batch') for r in rows if r.get('batch')})>1: raise ValueError('CSV has multiple batches; supply --batch')
  if a.session_name is None and a.session_id is None: raise ValueError('Supply an exact session name or --session-id')
  report=context(rows,find_target(rows,a.session_name,a.session_id,a.module),a.last);report['column_mapping']=mapping
  print(json.dumps(report,indent=2,ensure_ascii=False));return 0
 except (OSError,ValueError,KeyError,TypeError) as e:
  print('ASK: '+str(e));return 2
if __name__=='__main__': sys.exit(main())

# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
"""ChronologySplice: source-attributed partial-order reconstruction."""
from genlayer import *
from dataclasses import dataclass
from urllib.parse import urlsplit,unquote
import hashlib,json

def clean(v,n=700):return str(v).strip()[:n]
def ident(v):
 k=clean(v,64).upper()
 if len(k)<3 or any(c not in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in k):raise gl.vm.UserError('[EXPECTED] normalized identifier required')
 return k
def addr(v):
 try:return Address(v)
 except:raise gl.vm.UserError('[EXPECTED] valid auditor address required')
def link(v):
 raw=clean(v,500);p=urlsplit(raw)
 if p.scheme.lower()!='https' or not p.hostname or p.username or p.password or p.fragment:raise gl.vm.UserError('[EXPECTED] normalized HTTPS source required')
 if any(x in ('.','..') for x in unquote(p.path or '/').split('/')):raise gl.vm.UserError('[EXPECTED] normalized source path required')
 return raw,p.hostname.lower().rstrip('.')
def obj(v):
 if isinstance(v,dict):return v
 s=str(v);a=s.find('{');b=s.rfind('}')
 if a<0 or b<=a:raise gl.vm.UserError('[LLM] JSON object required')
 try:return json.loads(s[a:b+1])
 except:raise gl.vm.UserError('[LLM] invalid JSON')
def fetch(u):
 r=gl.nondet.web.get(u)
 if r.status in (403,429) or r.status>=500:raise gl.vm.UserError('[TRANSIENT] source unavailable')
 if r.status!=200:raise gl.vm.UserError('[EXTERNAL] source unavailable')
 raw=r.body if isinstance(r.body,bytes) else str(r.body).encode();return clean(raw.decode(errors='replace'),14000),hashlib.sha256(raw).hexdigest()

@allow_storage
@dataclass
class Docket:
 examiner:Address;auditor:Address;question:str;events:str;sources:str;state:str;edges:str;layers:str;conflicts:str;digests:str

class ChronologySplice(gl.Contract):
 dockets:TreeMap[str,Docket]
 ids:DynArray[str]
 def __init__(self):pass
 def _get(self,i):
  k=ident(i)
  if k not in self.dockets:raise gl.vm.UserError('[EXPECTED] docket not found')
  return k,self.dockets[k]
 def _reconstruct(self,d):
  events=json.loads(d.events);sources=json.loads(d.sources)
  def run():
   evidence=[];digests=[]
   for s in sources:
    body,digest=fetch(s['url']);evidence.append({'label':s['label'],'body':body});digests.append(digest)
   prompt='Reconstruct only supported precedence between named events. Do not invent a total order. Return JSON only {"edges":[{"before_index":0,"after_index":1,"source_indexes":[0]}],"conflicts":[{"left_index":0,"right_index":1,"source_indexes":[0,1]}]}. Every source index must support that exact finding. No self edges, duplicates, or out-of-range indexes. QUESTION:'+d.question+' EVENTS:'+json.dumps(events)+' SOURCES:'+json.dumps(evidence)
   x=obj(gl.nondet.exec_prompt(prompt,response_format='json'));edges=x.get('edges');conflicts=x.get('conflicts')
   if not isinstance(edges,list) or not isinstance(conflicts,list):raise gl.vm.UserError('[LLM] edges and conflicts required')
   def indexes(row):
    raw=row.get('source_indexes')
    if not isinstance(raw,list) or not raw:raise gl.vm.UserError('[LLM] attributed source indexes required')
    vals=[]
    for z in raw:
     try:i=int(z)
     except:raise gl.vm.UserError('[LLM] numeric source index required')
     if i<0 or i>=len(sources) or i in vals:raise gl.vm.UserError('[LLM] bounded unique source index required')
     vals.append(i)
    vals.sort();return vals
   out=[];seen=[]
   for row in edges:
    try:a=int(row.get('before_index'));b=int(row.get('after_index'))
    except:raise gl.vm.UserError('[LLM] numeric event indexes required')
    key=str(a)+':'+str(b)
    if a<0 or b<0 or a>=len(events) or b>=len(events) or a==b or key in seen:raise gl.vm.UserError('[LLM] bounded unique precedence edge required')
    seen.append(key);out.append({'before_index':a,'after_index':b,'source_indexes':indexes(row)})
   disputes=[];pairs=[]
   for row in conflicts:
    try:a=int(row.get('left_index'));b=int(row.get('right_index'))
    except:raise gl.vm.UserError('[LLM] numeric conflict indexes required')
    pair=str(min(a,b))+':'+str(max(a,b))
    if a<0 or b<0 or a>=len(events) or b>=len(events) or a==b or pair in pairs:raise gl.vm.UserError('[LLM] bounded unique conflict required')
    pairs.append(pair);disputes.append({'left_index':min(a,b),'right_index':max(a,b),'source_indexes':indexes(row)})
   out.sort(key=lambda z:(z['before_index'],z['after_index']));disputes.sort(key=lambda z:(z['left_index'],z['right_index']));return {'edges':out,'conflicts':disputes,'digests':digests}
  def validate(leader):
   if not isinstance(leader,gl.vm.Return):return False
   try:return run()==leader.calldata
   except:return False
  return gl.vm.run_nondet_unsafe(run,validate)
 @gl.public.write
 def open_docket(self,docket_id:str,auditor:str,question:str,events_json:str)->None:
  key=ident(docket_id);watcher=addr(auditor)
  try:events=json.loads(events_json)
  except:raise gl.vm.UserError('[EXPECTED] event JSON required')
  normalized=[]
  if key in self.dockets or watcher==gl.message.sender_address or len(clean(question,300))<12 or not isinstance(events,list) or len(events)<3 or len(events)>12:raise gl.vm.UserError('[EXPECTED] unique docket, separate auditor, and 3..12 events required')
  for e in events:
   eid=ident(e.get('id'));label=clean(e.get('label'),120)
   if len(label)<4 or any(x['id']==eid for x in normalized):raise gl.vm.UserError('[EXPECTED] unique labeled events required')
   normalized.append({'id':eid,'label':label})
  self.dockets[key]=Docket(gl.message.sender_address,watcher,clean(question,300),json.dumps(normalized,separators=(',',':')),'[]','OPEN','[]','[]','[]','[]');self.ids.append(key)
 @gl.public.write
 def add_source(self,docket_id:str,label:str,source_url:str)->None:
  _,d=self._get(docket_id);url,origin=link(source_url);sources=json.loads(d.sources)
  if d.state!='OPEN' or gl.message.sender_address!=d.examiner or len(sources)>=6 or any(s['origin']==origin for s in sources) or len(clean(label,100))<3:raise gl.vm.UserError('[EXPECTED] examiner adds distinct authoritative source')
  sources.append({'label':clean(label,100),'url':url,'origin':origin});d.sources=json.dumps(sources,separators=(',',':'))
 @gl.public.write
 def seal(self,docket_id:str)->None:
  _,d=self._get(docket_id)
  if d.state!='OPEN' or gl.message.sender_address!=d.examiner or len(json.loads(d.sources))<2:raise gl.vm.UserError('[EXPECTED] examiner seals docket with at least two sources')
  d.state='SEALED'
 @gl.public.write
 def reconstruct(self,docket_id:str)->None:
  _,d=self._get(docket_id)
  if d.state!='SEALED' or gl.message.sender_address!=d.auditor:raise gl.vm.UserError('[EXPECTED] assigned auditor reconstructs sealed docket')
  result=self._reconstruct(d);events=json.loads(d.events);incoming=[0]*len(events);outgoing=[[] for _ in events]
  for edge in result['edges']:incoming[edge['after_index']]+=1;outgoing[edge['before_index']].append(edge['after_index'])
  layers=[];front=[i for i,x in enumerate(incoming) if x==0];seen=0
  while front:
   layer=sorted(front);layers.append([events[i]['id'] for i in layer]);front=[]
   for i in layer:
    seen+=1
    for target in outgoing[i]:incoming[target]-=1;front.append(target) if incoming[target]==0 else None
  d.edges=json.dumps(result['edges'],separators=(',',':'));d.conflicts=json.dumps(result['conflicts'],separators=(',',':'));d.digests=json.dumps(result['digests']);d.layers=json.dumps(layers,separators=(',',':'));d.state='CONFLICT' if seen!=len(events) or result['conflicts'] else 'RECONSTRUCTED'
 @gl.public.write
 def file(self,docket_id:str)->None:
  _,d=self._get(docket_id)
  if d.state!='RECONSTRUCTED' or gl.message.sender_address!=d.examiner:raise gl.vm.UserError('[EXPECTED] examiner files conflict-free reconstruction')
  d.state='FILED'
 @gl.public.view
 def get_docket(self,docket_id:str)->dict:
  key,d=self._get(docket_id);return {'id':key,'examiner':d.examiner.as_hex,'auditor':d.auditor.as_hex,'question':d.question,'events':json.loads(d.events),'sources':json.loads(d.sources),'state':d.state,'edges':json.loads(d.edges),'layers':json.loads(d.layers),'conflicts':json.loads(d.conflicts),'digests':json.loads(d.digests)}


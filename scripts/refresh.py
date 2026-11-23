#!/usr/bin/env python3
"""Build a dated, selected NYPL public-domain metadata edition. No API key."""
import argparse,csv,gzip,hashlib,io,json,os,re,tempfile,urllib.request
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE='https://raw.githubusercontent.com/NYPL-publicdomain/data-and-utilities/'
COLUMNS=['id','title','dates','start','end','genres','places','subjects','contributors','publisher','collection','image','notes','pages']
RIGHTS='NYPL public-domain release: no known U.S. copyright restrictions; metadata CC0 1.0. Check the original record for current rights information.'
UUID=re.compile(r'^[0-9a-f-]{36}$')
def parts(text):return [x.strip() for x in (text or '').split('|') if x.strip()]
def year(text):
 return int(text) if re.fullmatch(r'[1-2]\d{3}',text or '') else None
def config(path):
 d=json.loads(path.read_text())
 if not re.fullmatch(r'[0-9a-f]{40}',d.get('sourceCommit','')):raise ValueError('Pin sourceCommit to a complete Git commit SHA')
 if not d.get('sourceFiles') or any(not re.fullmatch(r'pd_items_[1-9]\d*\.csv',x) for x in d['sourceFiles']):raise ValueError('Invalid source file')
 if not isinstance(d.get('genres'),list) or any(not isinstance(x,str) or not x.strip() for x in d['genres']):raise ValueError('genres must contain nonempty strings')
 if not isinstance(d.get('collectionIds'),list) or any(not UUID.fullmatch(x) for x in d['collectionIds']):raise ValueError('Invalid collection UUID')
 if not d['genres'] and not d['collectionIds']:raise ValueError('Select at least one genre or collection')
 if not 1 <= d.get('maxRecords',0) <= 200000:raise ValueError('maxRecords must be 1–200000')
 return d
def normalize(row):
 if not UUID.fullmatch(row['UUID']):raise ValueError('Source item lacks a valid ID')
 image=row.get('First Image','')
 m=re.fullmatch(r'https?://images\.nypl\.org/index\.php\?id=([a-zA-Z0-9_-]+)&t=g',image)
 start,end=year(row['Date Start']),year(row['Date End'])
 if start is not None and end is not None and end<start:end=None
 return [row['UUID'],row['Title'].strip() or 'Title not recorded',parts(row['Date']),start,end,parts(row['Genre']),parts(row['Subject Geographic'])+parts(row['Place Of Publication']),parts(row['Subject Topical'])+parts(row['Subject Name']),parts(row['Contributor']),parts(row['Publisher']),row['Collection UUID'],m.group(1) if m else '',row.get('Description','') or row.get('Note',''),int(row.get('Number of Captures') or 0)]
def extract(paths,cfg):
 records=[];collections={};seen=set();total=0;genreset={x.casefold() for x in cfg['genres']};collectionset=set(cfg['collectionIds'])
 for path in paths:
  with path.open(newline='',encoding='utf-8-sig') as f:
   reader=csv.DictReader(f)
   required={'UUID','Title','Genre','Collection UUID','Collection Title','Date','Date Start','Date End','Subject Geographic','Place Of Publication','Subject Topical','Subject Name','Contributor','Publisher'}
   if not required.issubset(reader.fieldnames or []):raise ValueError('Source CSV schema changed')
   for row in reader:
    total+=1
    if not(genreset.intersection(x.casefold() for x in parts(row['Genre'])) or row['Collection UUID'] in collectionset):continue
    item=normalize(row)
    if item[0] in seen:raise ValueError('Duplicate item UUID')
    seen.add(item[0]);records.append(item)
    if row['Collection UUID']:collections[row['Collection UUID']]=row['Collection Title']
    if len(records)>cfg['maxRecords']:raise ValueError('Selection exceeds maxRecords; narrow genres/collections or increase documented limit')
 if not records:raise ValueError('Selected collection is empty; existing snapshot retained')
 records.sort(key=lambda x:((x[3] if x[3] is not None else 9999),x[1],x[0]))
 return records,collections,total
def fetch(url,target):
 req=urllib.request.Request(url,headers={'User-Agent':'CoolCode-EphemeraAtlas/1.0 (https://github.com/jsdyer/ephemeraatlas)'})
 with urllib.request.urlopen(req,timeout=90) as response,target.open('wb') as output:
  total=0
  while chunk:=response.read(1024*1024):
   total+=len(chunk)
   if total>110*1024*1024:raise ValueError('Source exceeds the 110 MB per-file bound')
   output.write(chunk)
def refresh(root=ROOT,use_cache=False):
 cfg=config(root/'web/config.json');cache=root/'.cache';cache.mkdir(exist_ok=True)
 sourceinfo=[];paths=[]
 for name in cfg['sourceFiles']:
  url=SOURCE+cfg['sourceCommit']+'/items/'+name;p=cache/name
  if not use_cache or not p.exists():
   tmp=p.with_suffix('.download');fetch(url,tmp);os.replace(tmp,p)
  digest=hashlib.sha256(p.read_bytes()).hexdigest()
  sourceinfo.append({'url':url,'sha256':digest,'bytes':p.stat().st_size});paths.append(p)
 records,collections,total=extract(paths,cfg)
 captured=datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z')
 data={'schema':'coolcode.ephemera.v1','capturedAt':captured,'sourceEdition':cfg['sourceEdition'],'sourceCommit':cfg['sourceCommit'],'rights':RIGHTS,'columns':COLUMNS,'collections':collections,'records':records}
 raw=json.dumps(data,ensure_ascii=False,separators=(',',':')).encode();compressed=gzip.compress(raw,mtime=0)
 if len(raw)>60*1024*1024:raise ValueError('Selected metadata exceeds 60 MB expanded browser bound')
 status={'schema':'coolcode.ephemera.status.v1','capturedAt':captured,'sourceEdition':cfg['sourceEdition'],'sourceCommit':cfg['sourceCommit'],'recordCount':len(records),'collectionCount':len(collections),'sourceRows':total,'selectedGenres':cfg['genres'],'selectedCollections':cfg['collectionIds'],'file':'catalogue.json.gz','expandedBytes':len(raw),'compressedBytes':len(compressed),'sha256':hashlib.sha256(compressed).hexdigest(),'sources':sourceinfo,'rights':RIGHTS}
 out=root/'web/data';out.mkdir(exist_ok=True)
 with tempfile.TemporaryDirectory(dir=out) as temp:
  stage=Path(temp);(stage/'catalogue.json.gz').write_bytes(compressed);(stage/'status.json').write_text(json.dumps(status,indent=2)+'\n')
  os.replace(stage/'catalogue.json.gz',out/'catalogue.json.gz');os.replace(stage/'status.json',out/'status.json')
 print(f'Captured {len(records):,} selected items from {total:,} source rows; {len(compressed):,} bytes compressed')
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--use-cache',action='store_true',help='Developer-only: reuse already downloaded exact source files');args=parser.parse_args();refresh(use_cache=args.use_cache)

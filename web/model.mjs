export const COLUMNS=['id','title','dates','start','end','genres','places','subjects','contributors','publisher','collection','image','notes','pages'];
export const UUID=/^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/;
const list=x=>Array.isArray(x)&&x.every(v=>typeof v==='string');
export function decodeCatalogue(data){
 if(!data||data.schema!=='coolcode.ephemera.v1'||JSON.stringify(data.columns)!==JSON.stringify(COLUMNS)||!Array.isArray(data.records)||!data.records.length||data.records.length>200000||!data.collections||Array.isArray(data.collections)||typeof data.collections!=='object'||typeof data.rights!=='string'||!Number.isFinite(Date.parse(data.capturedAt)))throw Error('Unrecognized collection file.');
 const seen=new Set();
 const records=data.records.map(row=>{
  if(!Array.isArray(row)||row.length!==COLUMNS.length)throw Error('Invalid record shape.');
  const r=Object.fromEntries(COLUMNS.map((k,i)=>[k,row[i]]));
  if(!UUID.test(r.id)||seen.has(r.id)||typeof r.title!=='string'||!r.title||![r.dates,r.genres,r.places,r.subjects,r.contributors,r.publisher].every(list)||![r.start,r.end].every(x=>x===null||(Number.isInteger(x)&&x>=1000&&x<=2999))||typeof r.collection!=='string'||typeof r.image!=='string'||typeof r.notes!=='string'||!Number.isInteger(r.pages)||r.pages<0)throw Error('Invalid or duplicate collection record.');
  seen.add(r.id);r.collectionTitle=data.collections[r.collection]||'Uncollected item';r.search=[r.title,...r.dates,...r.genres,...r.places,...r.subjects,...r.contributors,...r.publisher,r.collectionTitle,r.notes].join(' ').toLocaleLowerCase();return r;
 });return {...data,records};
}
export function selectRecords(records,{query='',genre='',place='',collection='',from='',to='',undated=true,sort='oldest'}={}){
 const words=query.toLocaleLowerCase().trim().split(/\s+/).filter(Boolean),p=place.toLocaleLowerCase().trim();
 const low=from===''?null:Number(from),high=to===''?null:Number(to);
 if((low!==null&&(!Number.isInteger(low)||low<1000||low>2999))||(high!==null&&(!Number.isInteger(high)||high<1000||high>2999))||(low!==null&&high!==null&&low>high))throw Error('Use years from 1000 to 2999, with the start no later than the end.');
 return records.filter(r=>words.every(w=>r.search.includes(w))&&(!genre||r.genres.includes(genre))&&(!collection||r.collection===collection)&&(!p||r.places.some(v=>v.toLocaleLowerCase().includes(p)))&&(r.start===null?undated:((low===null||(r.end??r.start)>=low)&&(high===null||r.start<=high)))).sort((a,b)=>sort==='title'?a.title.localeCompare(b.title):(a.start===null&&b.start===null?0:a.start===null?1:b.start===null?-1:(a.start-b.start)*(sort==='newest'?-1:1))||a.title.localeCompare(b.title));
}
export function timeline(records){
 const years=records.map(x=>x.start).filter(x=>x!==null);if(!years.length)return [];
 const min=Math.min(...years),max=Math.max(...years),step=max-min>300?50:max-min>180?25:10,counts=new Map();
 for(const year of years){const start=Math.floor(year/step)*step;counts.set(start,(counts.get(start)||0)+1);}
 return Array.from(counts,([year,count])=>({year,end:year+step-1,count})).sort((a,b)=>a.year-b.year);
}
export function sourceUrl(record){if(!UUID.test(record.id))throw Error('Invalid source ID');return `https://digitalcollections.nypl.org/items/${record.id}`;}
export function imageUrl(record){return /^[a-zA-Z0-9_-]+$/.test(record.image)?`https://images.nypl.org/index.php?id=${encodeURIComponent(record.image)}&t=r`:null;}
export function dateLabel(r){return r.dates.length?r.dates.join(' / '):r.start===null?'Date not recorded':r.end&&r.end!==r.start?`${r.start}–${r.end}`:String(r.start);}
export function receipt(r,data){return {schema:'coolcode.ephemera.receipt.v1',capturedAt:data.capturedAt,sourceEdition:data.sourceEdition,rights:data.rights,source:sourceUrl(r),record:Object.fromEntries(COLUMNS.map(k=>[k,r[k]])),collectionTitle:r.collectionTitle};}
export function csv(records){const quote=x=>{let v=String(x??'');if(/^[=+@\t\r-]/.test(v))v="'"+v;return '"'+v.replaceAll('"','""')+'"';};const lines=[['Title','Recorded date','Earliest year','Latest year','Genres','Places (source metadata)','Collection','Source','Rights']];for(const r of records)lines.push([r.title,dateLabel(r),r.start,r.end,r.genres.join(' | '),r.places.join(' | '),r.collectionTitle,sourceUrl(r),'NYPL 2015 public-domain metadata release; check original rights']);return '\uFEFF'+lines.map(row=>row.map(quote).join(',')).join('\r\n');}
export async function readBounded(stream,maxBytes){const reader=stream.getReader(),chunks=[];let size=0;try{for(;;){const {done,value}=await reader.read();if(done)break;size+=value.byteLength;if(size>maxBytes)throw Error('Collection exceeds its documented size limit.');chunks.push(value);}}finally{await reader.cancel().catch(()=>{});}const bytes=new Uint8Array(size);let offset=0;for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.byteLength;}return bytes;}

export async function fetchBounded(url,maxBytes,timeoutMs=30000,fetcher=globalThis.fetch){
 const controller=new AbortController();
 const timer=setTimeout(()=>controller.abort(),timeoutMs);
 try{const response=await fetcher(url,{signal:controller.signal});if(!response.ok)throw Error(`Archive request returned HTTP ${response.status}.`);return await readBounded(response.body,maxBytes);}
 catch(error){if(controller.signal.aborted)throw Error('The archive download timed out. Reload the page to try again.');throw error;}
 finally{clearTimeout(timer);}
}

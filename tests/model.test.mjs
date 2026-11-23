import test from 'node:test';import assert from 'node:assert/strict';import {readFileSync} from 'node:fs';import {gunzipSync} from 'node:zlib';import {createHash} from 'node:crypto';import {COLUMNS,decodeCatalogue,selectRecords,timeline,sourceUrl,imageUrl,dateLabel,receipt,csv,readBounded,fetchBounded} from '../web/model.mjs';
const id=n=>`${String(n).padStart(8,'0')}-1234-1234-1234-123456789abc`;
const row=(n,title,start,end,genre='Menus',places=[])=>[id(n),title,start===null?[]:[String(start)],start,end,[genre],places,['Travel'],[],[],'c','ps_rbk_701','Source note',1];
const raw=records=>({schema:'coolcode.ephemera.v1',capturedAt:'2026-11-23T12:00:00Z',sourceEdition:'2015-12-30',rights:'NYPL source release',columns:COLUMNS,collections:{c:'Collection'},records});
const fixture=()=>decodeCatalogue(raw([row(1,'Railroad supper',1890,1905),row(2,'Holiday in Canada',null,null,'Postcards',['Montreal']),row(3,'A poster',1920,null,'Posters')])).records;
test('metadata search accepts arbitrary words and genres beyond presets',()=>{assert.equal(selectRecords(fixture(),{query:'railroad travel'}).length,1);assert.equal(selectRecords(fixture(),{genre:'Posters'}).length,1);assert.equal(selectRecords(fixture(),{query:'Canada'}).length,1);assert.equal(selectRecords(fixture(),{query:'nonexistent'}).length,0);});
test('year ranges overlap and undated handling is explicit',()=>{assert.deepEqual(selectRecords(fixture(),{from:'1900',to:'1910',undated:false}).map(x=>x.id),[id(1)]);assert.equal(selectRecords(fixture(),{from:'1900',to:'1910'}).length,2);assert.throws(()=>selectRecords(fixture(),{from:'1910',to:'1900'}));assert.throws(()=>selectRecords(fixture(),{from:'banana'}));});
test('recorded place search does not infer a place from the title',()=>{assert.equal(selectRecords(fixture(),{place:'canada'}).length,0);assert.equal(selectRecords(fixture(),{place:'montreal'}).length,1);});
test('missing dates stay last in either chronological order',()=>{assert.equal(selectRecords(fixture(),{sort:'newest'}).at(-1).start,null);assert.equal(selectRecords(fixture(),{sort:'oldest'}).at(-1).start,null);assert.equal(dateLabel(fixture()[1]),'Date not recorded');});
test('chronology counts earliest years once, not every year in a range',()=>{assert.equal(timeline(fixture()).reduce((n,b)=>n+b.count,0),2);});
test('duplicate and invalid source identifiers are rejected',()=>{assert.throws(()=>decodeCatalogue(raw([row(1,'x',1900,null),row(1,'y',1901,null)])));const r=row(1,'x',1900,null);r[0]='javascript:alert(1)';assert.throws(()=>decodeCatalogue(raw([r])));assert.throws(()=>sourceUrl({id:'javascript:alert(1)'}));assert.equal(imageUrl({image:'x&url=evil'}),null);});
test('export retains provenance, source links, dates and quotes',()=>{const d=decodeCatalogue(raw([row(1,'A "quoted" title',1900,null)]));const result=receipt(d.records[0],d);assert.equal(result.sourceEdition,'2015-12-30');assert.match(result.source,/digitalcollections.nypl.org\/items\//);assert.match(csv(d.records),/A ""quoted"" title/);});
test('stream bounds reject an oversized expanded response',async()=>{const bytes=new Uint8Array(5);await assert.rejects(readBounded(new Blob([bytes]).stream(),4));assert.equal((await readBounded(new Blob([bytes]).stream(),5)).length,5);});
test('bundled real archive matches provenance and parser contract',()=>{const status=JSON.parse(readFileSync(new URL('../web/data/status.json',import.meta.url)));const packed=readFileSync(new URL('../web/data/catalogue.json.gz',import.meta.url));assert.equal(createHash('sha256').update(packed).digest('hex'),status.sha256);const unpacked=gunzipSync(packed);assert.equal(unpacked.length,status.expandedBytes);const d=decodeCatalogue(JSON.parse(unpacked));assert.equal(d.records.length,status.recordCount);assert.equal(d.sourceEdition,status.sourceEdition);assert.ok(d.records.length>0);});

test('CSV neutralizes spreadsheet formulas from metadata',()=>{const d=decodeCatalogue(raw([row(1,'=HYPERLINK("bad")',1900,null)]));assert.match(csv(d.records),/"'=HYPERLINK/);});

test('download deadline aborts a stalled response body rather than loading forever',async()=>{
 let aborted=false;
 const fetcher=async(url,{signal})=>({ok:true,body:new ReadableStream({start(controller){signal.addEventListener('abort',()=>{aborted=true;controller.error(new DOMException('Aborted','AbortError'));});}})});
 await assert.rejects(fetchBounded('./stalled.json',1024,15,fetcher),/timed out/);assert.equal(aborted,true);
});
test('bounded downloads reject HTTP errors and retain successful bytes',async()=>{
 await assert.rejects(fetchBounded('./bad',1024,100,async()=>({ok:false,status:503})),/HTTP 503/);
 const bytes=await fetchBounded('./good',1024,100,async()=>({ok:true,body:new Blob(['good']).stream()}));assert.equal(new TextDecoder().decode(bytes),'good');
});

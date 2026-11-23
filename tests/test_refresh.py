import csv,gzip,hashlib,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from refresh import config,extract,normalize,parts,year,ROOT
FIELDS=['UUID','Title','Genre','Collection UUID','Collection Title','Date','Date Start','Date End','Subject Geographic','Place Of Publication','Subject Topical','Subject Name','Contributor','Publisher','First Image','Number of Captures']
def row(n,genre='Menus'):
 r={x:'' for x in FIELDS};r.update({'UUID':f'{n:08d}-1234-1234-1234-123456789abc','Title':'Original title','Genre':genre,'Date':'ca. 1900','Date Start':'1900','Number of Captures':'2'});return r
class RefreshTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.path=Path(self.temp.name)/'source.csv';self.cfg={'genres':['Menus'],'collectionIds':[],'maxRecords':20}
 def write(self,rows):
  with self.path.open('w',newline='') as f:
   w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(rows)
 def test_expanded_genre_configuration_selects_an_extra_kind(self):
  self.write([row(1),row(2,'Posters')]);a,_,_=extract([self.path],self.cfg);self.assertEqual(len(a),1);self.cfg['genres'].append('Posters');b,_,_=extract([self.path],self.cfg);self.assertEqual(len(b),2)
 def test_added_collection_is_an_or_selection(self):
  second=row(2,'Unknown');second['Collection UUID']='12345678-1234-1234-1234-123456789abc';self.write([row(1),second]);self.cfg['collectionIds']=[second['Collection UUID']];self.assertEqual(len(extract([self.path],self.cfg)[0]),2)
 def test_no_truncation_duplicate_or_empty_silent_success(self):
  self.write([row(1),row(2)]);self.cfg['maxRecords']=1
  with self.assertRaisesRegex(ValueError,'exceeds'):extract([self.path],self.cfg)
  self.cfg['maxRecords']=20;self.write([row(1),row(1)])
  with self.assertRaisesRegex(ValueError,'Duplicate'):extract([self.path],self.cfg)
  self.write([row(1,'Not selected')])
  with self.assertRaisesRegex(ValueError,'empty'):extract([self.path],self.cfg)
 def test_missing_date_and_title_are_explicit_and_original_date_retained(self):
  r=row(1);r['Date Start']='';r['Title']='';x=normalize(r);self.assertIsNone(x[3]);self.assertEqual(x[1],'Title not recorded');self.assertEqual(x[2],['ca. 1900'])
 def test_source_image_host_must_be_expected(self):
  r=row(1);r['First Image']='https://evil.example/a';self.assertEqual(normalize(r)[11],'')
 def test_malformed_csv_and_reversed_date(self):
  self.path.write_text('id,title\n1,x\n')
  with self.assertRaisesRegex(ValueError,'schema'):extract([self.path],self.cfg)
  r=row(1);r['Date End']='1800';self.assertIsNone(normalize(r)[4]);self.assertIsNone(year('ca. 1900'))
 def test_committed_capture_is_complete_and_matches_source_config(self):
  cfg=config(ROOT/'web/config.json');status=json.loads((ROOT/'web/data/status.json').read_text());packed=(ROOT/'web/data/catalogue.json.gz').read_bytes();data=json.loads(gzip.decompress(packed));self.assertRegex(status['sourceCommit'],r'^[0-9a-f]{40}$');self.assertEqual(hashlib.sha256(packed).hexdigest(),status['sha256']);self.assertEqual(len(data['records']),status['recordCount'])
if __name__=='__main__':unittest.main()

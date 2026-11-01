"""Exercise account-free WebDAV sync using two disposable real kernel processes."""
import argparse,json,subprocess,tempfile,time,urllib.request

parser=argparse.ArgumentParser()
parser.add_argument("--kernel",required=True)
parser.add_argument("--resources",required=True)
parser.add_argument("--fixture",required=True)
args=parser.parse_args()
from pathlib import Path
root=Path(tempfile.mkdtemp(prefix='siyuan-selfhost-smoke-'))
for n in ['a','b','cloud']:(root/n).mkdir(exist_ok=True)
processes=[]
def launch(args,name):
 log=open(root/(name+'.log'),'w');p=subprocess.Popen(args,stdout=log,stderr=log);processes.append(p);return p

def dav():return launch([str(Path(args.fixture).resolve()),str(root/'cloud')],'dav')

def request(port,path,body,token):
 r=urllib.request.Request(f'http://127.0.0.1:{port}'+path,data=json.dumps(body).encode(),headers={'Authorization':'Token '+token,'Content-Type':'application/json'})
 with urllib.request.urlopen(r,timeout=120) as response:d=json.load(response)
 assert d['code']==0,(path,d.get('code'),d.get('msg'))
 return d.get('data')
try:
 d=dav()
 tokens={}
 for n,port in [('a',16816),('b',16818)]:
  launch([str(Path(args.kernel).resolve()),'serve','--wd='+str(Path(args.resources).resolve()),'--workspace='+str(root/n),'--port='+str(port),'--accessAuthCode=fixture-local-only'],n)
  for i in range(50):
   try:
    conf=json.loads((root/n/'conf/conf.json').read_text());token=conf['api']['token']
    data=request(port,'/api/system/bootProgress',{},token)
    if data['progress']>=100:tokens[port]=token;break
   except (OSError,ValueError,KeyError):pass
   time.sleep(.3)
  else:raise RuntimeError('boot timeout '+n)
 def call(port,path,body={}):return request(port,path,body,tokens[port])
 key=call(16816,'/api/repo/initRepoKey')['key']
 call(16818,'/api/repo/importRepoKey',{'key':key})
 for port in tokens:
  call(port,'/api/sync/setSyncProviderWebDAV',{'webdav':{'endpoint':'http://127.0.0.1:16807','username':'test','password':'fixture-only','timeout':7,'concurrentReqs':4}})
  call(port,'/api/sync/setSyncProvider',{'provider':3})
  call(port,'/api/sync/setSyncMode',{'mode':3})
  call(port,'/api/sync/setSyncEnable',{'enabled':True})
 notebook=call(16816,'/api/notebook/createNotebook',{'name':'Self-hosted test'})['notebook']['id']
 time.sleep(2)
 call(16816,'/api/notebook/openNotebook',{'notebook':notebook})
 time.sleep(1)
 asset=root/'a/data/assets/selfhost-roundtrip.txt'
 asset.parent.mkdir(exist_ok=True)
 asset.write_bytes(b'selfhost-attachment-roundtrip')
 doc=call(16816,'/api/filetree/createDocWithMd',{'notebook':notebook,'path':'/Roundtrip','markdown':'server-to-phone-marker\n\n[fixture](assets/selfhost-roundtrip.txt)'})
 def sync(port,upload):call(port,'/api/sync/performSync',{'upload':upload})
 time.sleep(1);sync(16816,True);sync(16818,False)
 assert 'server-to-phone-marker' in call(16818,'/api/block/getBlockKramdown',{'id':doc})['kramdown']
 print('SERVER_TO_SECOND_WORKSPACE_OK',flush=True)
 assert (root/'b/data/assets/selfhost-roundtrip.txt').read_bytes()==asset.read_bytes()
 print('ATTACHMENT_ROUNDTRIP_OK',flush=True)
 call(16818,'/api/block/appendBlock',{'dataType':'markdown','data':'phone-to-server-marker','parentID':doc})
 time.sleep(1);sync(16818,True);sync(16816,False)
 assert 'phone-to-server-marker' in call(16816,'/api/block/getBlockKramdown',{'id':doc})['kramdown']
 print('SECOND_WORKSPACE_TO_SERVER_OK',flush=True)
 d.terminate();d.wait(timeout=10)
 offline=call(16818,'/api/filetree/createDocWithMd',{'notebook':notebook,'path':'/Offline','markdown':'offline-reconnect-marker'})
 sync(16818,True)
 assert 'offline-reconnect-marker' in call(16818,'/api/block/getBlockKramdown',{'id':offline})['kramdown']
 print('LOCAL_NOTE_RETAINED_WHEN_STORAGE_UNREACHABLE',flush=True)
 call(16818,'/api/sync/setSyncMode',{'mode':1})
 d=dav();time.sleep(.3)
 # Network failures use the upstream five-minute backoff. Reset the interval
 # through its public setting so the automatic-job test completes promptly.
 call(16818,'/api/sync/setSyncInterval',{'interval':30})
 for _ in range(24):
  sync(16816,False)
  try:
   if 'offline-reconnect-marker' in call(16816,'/api/block/getBlockKramdown',{'id':offline})['kramdown']:
    break
  except AssertionError:
   pass
  time.sleep(5)
 else:
  raise AssertionError('automatic upload did not resume after reconnection')
 print('OFFLINE_NOTE_AUTOMATICALLY_SYNCED_AFTER_STORAGE_RECONNECT',flush=True)
finally:
 print("Smoke workspace logs:",root,flush=True)
 for p in processes:
  if p.poll() is None:
   p.terminate()
 for p in processes:
  try:p.wait(timeout=15)
  except subprocess.TimeoutExpired:p.kill()

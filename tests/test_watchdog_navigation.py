import asyncio,importlib.util,json,subprocess,sys,types,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]/'stelab-kiosk'
sys.path.insert(0,str(ROOT))

def load(name,file):
 spec=importlib.util.spec_from_file_location(name,ROOT/file);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
m=load('watchdog_fixed','chromium_watchdog.py')
class StopLoop(BaseException):pass
class Controller:
 def __init__(self,urls,results=None):self.urls=urls;self.i=0;self.settings=0;self.logins=0;self.reloads=0;self.results=results or []
 async def get_page_target(self):return {'url':self.urls[self.i]}
 async def evaluate(self,script):
  if 'passwordField' in script:self.logins+=1;return {'result':{'value':None}}
  self.settings+=1;r=self.results[self.settings-1] if self.settings<=len(self.results) else {'ok':True,'changed':True}
  return {'result':{'value':r}}
 async def reload(self,**kwargs):self.reloads+=1
 async def sleep(self,_):
  self.i+=1
  if self.i>=len(self.urls):raise StopLoop()
def run(module,c):
 with patch.object(module,'ChromiumController',return_value=c),patch.object(module,'BROWSER_REFRESH',0),patch.object(module.asyncio,'sleep',c.sleep):
  try:asyncio.run(module.main())
  except StopLoop:pass
class Tests(unittest.TestCase):
 def test_route_changes_do_not_reapply_or_reload(self):
  c=Controller([m.HA_URL_BASE+p for p in ['/overview/0','/config','/config/dashboard','/config?x=1','/overview/0?edit=1']]);run(m,c)
  self.assertEqual((c.settings,c.reloads),(1,1))
 def test_unchanged_settings_need_no_reload(self):
  c=Controller([m.HA_URL_BASE+'/config']*2,[{'ok':True,'changed':False}]);run(m,c);self.assertEqual((c.settings,c.reloads),(1,0))
 def test_failed_settings_are_retried(self):
  c=Controller([m.HA_URL_BASE+'/config']*3,[{'ok':False,'changed':False},{'ok':True,'changed':True}]);run(m,c)
  self.assertEqual((c.settings,c.reloads),(2,1))
 def test_auth_and_external_pages_are_not_configured(self):
  c=Controller(['https://example.com/',m.HA_URL_BASE+'/auth/authorize?response_type=code',m.HA_URL_BASE+'/overview/0',m.HA_URL_BASE+'/config']);run(m,c)
  self.assertEqual((c.logins,c.settings,c.reloads),(1,1,1))
 def test_javascript_preserves_theme_and_compares_json_semantically(self):
  js=m.build_settings_script('"always_hidden"','{"dark":true}')
  code="""const script=JSON.parse(require('fs').readFileSync(0,'utf8'));
function run(seed){ const data={...seed};global.localStorage={getItem:k=>data[k]??null,setItem:(k,v)=>{data[k]=String(v)},removeItem:k=>{delete data[k]}};const first=eval(script);const second=eval(script);return {first,second,data};}
const a=run({'dockedSidebar':'"always_hidden"','selectedTheme':'{"theme":"glass_header"}'});
if(!a.first.changed || a.second.changed || JSON.parse(a.data.selectedTheme).theme!=='glass_header')throw Error('custom theme lost or repeated write');
const b=run({'dockedSidebar':'"always_hidden"','selectedTheme':'{ "dark": true, "theme": "glass_header" }'});
if(b.first.changed || b.second.changed)throw Error('equivalent JSON treated as change');
const c=run({});if(!c.first.changed || c.second.changed)throw Error('initialization not idempotent');
console.log('JS settings cases passed');"""
  r=subprocess.run(['node','-e',code],input=json.dumps(js),text=True,capture_output=True)
  self.assertEqual(r.returncode,0,r.stderr)
if __name__=='__main__':unittest.main(verbosity=2)

#!/usr/bin/env python3
"""Local 120s input idle timeout, with visible playing-video and manual-off support."""
from __future__ import annotations
import asyncio,ctypes,fcntl,json,logging,math,os,signal,subprocess,sys,time
from pathlib import Path
sys.path.insert(0,'/')
from aiohttp import ClientSession,ClientTimeout
from browser_ctl import ChromiumController,ChromiumPageSession
from browser_visibility import BrowserWindowSaver
LOG=logging.getLogger('display_idle')
TIMEOUT=float(os.environ.get("SCREEN_TIMEOUT", "120"))
POLL=2.0

class ScreenInfo(ctypes.Structure):
    _fields_=[('window',ctypes.c_ulong),('state',ctypes.c_int),('kind',ctypes.c_int),('since',ctypes.c_ulong),('idle',ctypes.c_ulong),('mask',ctypes.c_ulong)]
class X11Screen:
    def __init__(self):
        self.x=ctypes.CDLL('libX11.so.6');self.s=ctypes.CDLL('libXss.so.1');self.ext=ctypes.CDLL('libXext.so.6')
        self.x.XOpenDisplay.argtypes=[ctypes.c_char_p];self.x.XOpenDisplay.restype=ctypes.c_void_p
        self.x.XDefaultRootWindow.argtypes=[ctypes.c_void_p];self.x.XDefaultRootWindow.restype=ctypes.c_ulong
        self.s.XScreenSaverAllocInfo.restype=ctypes.POINTER(ScreenInfo)
        self.s.XScreenSaverQueryInfo.argtypes=[ctypes.c_void_p,ctypes.c_ulong,ctypes.POINTER(ScreenInfo)]
        self.ext.DPMSInfo.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_ushort),ctypes.POINTER(ctypes.c_int)]
        self.display=self.x.XOpenDisplay(os.environ.get('DISPLAY',':0').encode())
        if not self.display:raise RuntimeError('Cannot open kiosk X display')
        self.root=self.x.XDefaultRootWindow(self.display);self.info=self.s.XScreenSaverAllocInfo()
    def sample(self):
        if not self.s.XScreenSaverQueryInfo(self.display,self.root,self.info):raise RuntimeError('Cannot read X input idle time')
        level=ctypes.c_ushort();enabled=ctypes.c_int()
        if not self.ext.DPMSInfo(self.display,ctypes.byref(level),ctypes.byref(enabled)):raise RuntimeError('Cannot read DPMS status')
        return self.info.contents.idle/1000.0,level.value==0
    def configure(self):
        subprocess.run(['xset','s','off','+dpms','dpms','0','0','0'],check=True,timeout=5,capture_output=True)
    def set_on(self,value):
        subprocess.run(['xset','+dpms','dpms','force','on' if value else 'off'],check=True,timeout=5,capture_output=True)

class IdlePolicy:
    def __init__(self,timeout=TIMEOUT):
        self.timeout=timeout;self.last_video=-math.inf;self.last_wake=-math.inf
        self.previous_on=None;self.previous_idle=None;self.expected=None;self.manual_off=False
    def decide(self,now,idle,on,video):
        own_transition=self.expected is not None and on==self.expected
        if own_transition:self.expected=None
        input_reset=self.previous_idle is not None and idle+0.5<self.previous_idle
        external_wake=self.previous_on is False and on and not own_transition
        if input_reset or external_wake:
            self.manual_off=False;self.last_wake=now
        if self.previous_on is True and not on and not own_transition:self.manual_off=True
        if video:self.last_video=now
        age=min(idle,now-self.last_video,now-self.last_wake)
        if self.manual_off:desired=False
        elif video:desired=True
        elif age>=self.timeout:desired=False
        else:desired=on or input_reset or external_wake
        self.previous_on=on;self.previous_idle=idle
        return desired
    def commanded(self,on):self.expected=on

PROBE=r"""(() => {
 const videos=[];let n=0;
 const visible=e=>{const r=e.getBoundingClientRect();const w=e.ownerDocument.defaultView;const s=w.getComputedStyle(e);return r.width>1&&r.height>1&&r.bottom>0&&r.right>0&&r.top<w.innerHeight&&r.left<w.innerWidth&&s.display!=='none'&&s.visibility!=='hidden'&&Number(s.opacity)!==0;};
 const visit=root=>{for(const e of root.querySelectorAll('*')){
   if(e.tagName==='VIDEO'){videos.push({key:n++,t:Number(e.currentTime)||0,active:visible(e)&&!e.paused&&!e.ended&&e.readyState>=2&&e.videoWidth>0});}
   if(e.shadowRoot)visit(e.shadowRoot);
   if(e.tagName==='IFRAME'&&visible(e)){try{if(e.contentDocument)visit(e.contentDocument);}catch(_){}}
 }};
 if(document.visibilityState==='visible')visit(document);
 return {visible:document.visibilityState==='visible',videos};
})()"""

class VideoDetector:
    def __init__(self):self.controller=ChromiumController();self.previous={};self.live={}
    def observe(self,now,samples):
        current={};active_keys=set()
        for key,t,active in samples:
            current[key]=t
            if not active:continue
            active_keys.add(key)
            if key not in self.previous or t>self.previous[key]+0.02:self.live[key]=now
        self.previous=current;self.live={k:v for k,v in self.live.items() if k in active_keys}
        return any(now-t<=4 for t in self.live.values())
    async def sample(self,now):
        targets=await self.controller.list_targets();samples=[]
        async with ClientSession(timeout=ClientTimeout(total=4)) as session:
            for target in targets:
                if target.get('type') not in ['page','iframe'] or not target.get('webSocketDebuggerUrl'):continue
                try:
                    async with session.ws_connect(target['webSocketDebuggerUrl']) as socket:
                        page=ChromiumPageSession(socket)
                        result=await page.call('Runtime.evaluate',{'expression':PROBE,'returnByValue':True})
                        value=result.get('result',{}).get('value',{})
                        if not value.get('visible'):continue
                        for v in value.get('videos',[]):samples.append((target['id']+':'+str(v['key']),float(v['t']),bool(v['active'])))
                except Exception:continue  # A tab/frame may disappear during navigation.
        return self.observe(now,samples)

async def main():
    lock=open('/run/stelab-display-idle.lock','w')
    try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:return
    screen=X11Screen();screen.configure();windows=BrowserWindowSaver();policy=IdlePolicy();video=VideoDetector();last_error=-math.inf;last_video=False
    loop=asyncio.get_running_loop();task=asyncio.current_task()
    for signum in (signal.SIGTERM,signal.SIGINT):loop.add_signal_handler(signum,task.cancel)
    LOG.info('Started: %ss input idle timeout; playing-video exception; explicit off wins', TIMEOUT)
    try:
        while True:
            now=time.monotonic()
            try:
                idle,on=screen.sample()
                windows.sync(on)
                try:playing=await video.sample(now)
                except Exception:playing=False
                if playing!=last_video:LOG.info('Visible video %s','playing' if playing else 'stopped/paused');last_video=playing
                desired=policy.decide(now,idle,on,playing)
                if desired!=on:
                    screen.set_on(desired);policy.commanded(desired)
                    windows.sync(desired)
                    LOG.info('Display %s (input idle %.1fs; video=%s)','on' if desired else 'off',idle,playing)
            except Exception as e:
                if now-last_error>=60:LOG.warning('Idle monitor error: %s',type(e).__name__);last_error=now
            await asyncio.sleep(POLL)
    finally:
        windows.close()
if __name__=='__main__':
    logging.basicConfig(level=logging.INFO,format='[%(asctime)s] %(levelname)s: [display_idle] %(message)s',datefmt='%H:%M:%S')
    try:asyncio.run(main())
    except (asyncio.CancelledError,KeyboardInterrupt):pass

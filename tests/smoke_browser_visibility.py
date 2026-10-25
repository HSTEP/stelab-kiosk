"""Real minimize/restore, preserving focus and already minimized windows."""
import importlib.util
import os
import subprocess
import time
from Xlib import display


def wait_for(check, message):
    end=time.monotonic()+15
    while time.monotonic()<end:
        if check():return
        time.sleep(.1)
    raise AssertionError(message)


def window(title):
    r=subprocess.run(['xdotool','search','--name','^'+title+'$'],capture_output=True,text=True)
    return r.stdout.strip() if r.returncode==0 else None


def hidden(w):
    return '_NET_WM_STATE_HIDDEN' in subprocess.check_output(['xprop','-id',str(w),'_NET_WM_STATE'],text=True)


def main():
    os.environ['DISPLAY']=':0';processes=[];saver=None
    try:
        processes.append(subprocess.Popen(['Xvfb',':0','-screen','0','1024x768x24','-nolisten','tcp']))
        wait_for(lambda: subprocess.run(['xdpyinfo'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0,'X server')
        processes.append(subprocess.Popen(['openbox'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL))
        wait_for(lambda: 'window id #' in subprocess.check_output(['xprop','-root','_NET_SUPPORTING_WM_CHECK'],text=True),'WM')
        for title,kind in [('Dashboard visibility test','chromium'),('Already minimized test','chromium'),('AI focus test','ChatGPT')]:
            processes.append(subprocess.Popen(['xterm','-class',kind,'-title',title]))
            wait_for(lambda: window(title),'fixture '+title)
        dashboard=window('Dashboard visibility test');already=window('Already minimized test');ai=window('AI focus test')
        subprocess.run(['xdotool','windowminimize',already,'windowactivate','--sync',ai],check=True)
        wait_for(lambda: hidden(already),'manually minimized fixture')
        spec=importlib.util.spec_from_file_location('visibility','/browser_visibility.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        saver=m.BrowserWindowSaver(user_id=os.getuid())
        saver.sync(False);saver.sync(False)
        wait_for(lambda: hidden(dashboard),'screen-off did not hide dashboard')
        assert hidden(already)
        assert saver.hidden==[int(dashboard)], saver.hidden
        saver.sync(True)
        wait_for(lambda: not hidden(dashboard),'screen-on did not restore dashboard')
        assert hidden(already),'Manually minimized window was unexpectedly restored'
        wait_for(lambda: subprocess.check_output(['xdotool','getactivewindow'],text=True).strip()==ai,'AI focus was not preserved')
        saver.sync(False);saver.close();saver=None
        wait_for(lambda: not hidden(dashboard),'controller exit left dashboard hidden')
        print('PASS: screen-off hides only kiosk windows; wake restores state/focus; manual minimization preserved; shutdown restores')
    finally:
        if saver:saver.close()
        for p in reversed(processes):
            if p.poll() is None:p.terminate();p.wait(timeout=8)

if __name__=='__main__':main()

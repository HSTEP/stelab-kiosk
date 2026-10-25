"""Real autohide/task restoration over fullscreen, in a disposable X server."""
import os
import subprocess
import time
from Xlib import display


def wait_for(check, message, seconds=15):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        value = check()
        if value:
            return value
        time.sleep(.1)
    raise AssertionError(message)


def window(name):
    r = subprocess.run(['xdotool','search','--name','^'+name+'$'],capture_output=True,text=True)
    return r.stdout.strip().splitlines()[-1] if r.returncode == 0 else None


def geometry(identifier):
    raw = subprocess.check_output(['xdotool','getwindowgeometry','--shell',identifier],text=True)
    return {k:int(v) for k,v in (line.split('=',1) for line in raw.splitlines())}


def main():
    os.environ['DISPLAY'] = ':0'
    processes = []
    d = None
    try:
        processes.append(subprocess.Popen(['Xvfb',':0','-screen','0','1024x768x24','-nolisten','tcp']))
        wait_for(lambda: subprocess.run(['xdpyinfo'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode == 0,'X server')
        processes.append(subprocess.Popen(['openbox'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL))
        wait_for(lambda: 'window id #' in subprocess.check_output(['xprop','-root','_NET_SUPPORTING_WM_CHECK'],text=True),'window manager')
        processes.append(subprocess.Popen(['xterm','-class','ChatGPT','-title','ChatGPT taskbar test']))
        app = wait_for(lambda: window('ChatGPT taskbar test'),'app fixture')
        subprocess.run(['xdotool','windowminimize',app],check=True)
        processes.append(subprocess.Popen(['xterm','-class','chromium','-title','Dashboard taskbar test']))
        dashboard = wait_for(lambda: window('Dashboard taskbar test'),'dashboard fixture')
        subprocess.run(['wmctrl','-i','-r',hex(int(dashboard)),'-b','add,fullscreen'],check=True)
        processes.append(subprocess.Popen(['python3','/desktop_session.py','panel']))
        panel = wait_for(lambda: window('STELAB Taskbar'),'taskbar window')
        d = display.Display()
        def visible_height():
            g = geometry(panel)
            return min(g['HEIGHT'], 768-g['Y'])
        subprocess.run(['xdotool','mousemove','500','300'],check=True)
        wait_for(lambda: visible_height() <= 4,'taskbar did not hide')
        subprocess.run(['xdotool','mousemove','180','767'],check=True)
        wait_for(lambda: visible_height() >= 40,'taskbar did not reveal over fullscreen')
        pointer = d.screen().root.query_pointer()
        assert pointer.child and pointer.child.id == int(panel), 'Fullscreen covered the taskbar hit area'
        subprocess.run(['xdotool','mousemove','180','745','click','1'],check=True)
        wait_for(lambda: subprocess.check_output(['xdotool','getactivewindow'],text=True).strip() == app,
                 'Click did not restore minimized app')
        subprocess.run(['xdotool','mousemove','500','300'],check=True)
        wait_for(lambda: visible_height() <= 4,'taskbar did not hide after switching')
        # Refocusing the fullscreen window must not bury the hidden edge again.
        subprocess.run(['xdotool','windowactivate','--sync',dashboard],check=True)
        subprocess.run(['xdotool','mousemove','180','767'],check=True)
        wait_for(lambda: visible_height() >= 40,'taskbar lost after fullscreen refocus')
        assert d.screen().root.query_pointer().child.id == int(panel)
        subprocess.run(['xdotool','mousemove','500','300'],check=True)
        wait_for(lambda: visible_height() <= 4,'taskbar did not hide again')
        print('PASS: taskbar hidden edge, reveal above fullscreen, click restores minimized app, automatic rehide')
    finally:
        if d: d.close()
        for process in reversed(processes):
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=8)


if __name__ == '__main__':
    main()

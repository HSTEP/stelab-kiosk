"""Real autohide/task restoration over fullscreen, in a disposable X server."""
import os
import subprocess
import time
from Xlib import X, display


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
        helper = processes[-1]
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
        # Reproduce the production startup condition: desktop, OSK, and a dock
        # that is taken back by Openbox after its initial overlay setup.
        processes.append(subprocess.Popen(['python3','/desktop_session.py','run']))
        processes.append(subprocess.Popen(['dbus-run-session','--','onboard'],
                                          stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL))
        time.sleep(1)
        panel_window = d.create_resource_object('window',int(panel))
        panel_window.unmap(); d.sync()
        panel_window.change_attributes(override_redirect=False)
        panel_window.map(); d.sync()
        wait_for(lambda: panel_window.get_attributes().override_redirect
                 and panel_window.query_tree().parent.id == d.screen().root.id,
                 'taskbar did not recover from window-manager takeover')
        time.sleep(1)
        # Repeated notifications with identical data must not feed back into
        # XConfigureWindow -> Openbox -> property notification -> XConfigureWindow.
        root = d.screen().root
        atom = d.intern_atom('_NET_CLIENT_LIST_STACKING')
        current = root.get_full_property(atom,X.AnyPropertyType)
        for _ in range(100):
            root.change_property(atom,d.intern_atom('WINDOW'),32,current.value)
        d.sync()
        def cpu_seconds():
            with open(f'/proc/{helper.pid}/stat') as f:
                fields=f.read().rsplit(')',1)[1].split()
            return (int(fields[11])+int(fields[12]))/os.sysconf('SC_CLK_TCK')
        before=cpu_seconds(); time.sleep(4); used=cpu_seconds()-before
        assert used < .25, f'Taskbar event loop used {used:.2f} CPU seconds during 4 seconds idle'
        assert helper.poll() is None
        print(f'PASS: desktop/OSK takeover recovery, repeated stack notifications, helper CPU {used:.2f}s / 4s')
        print('PASS: taskbar hidden edge, reveal above fullscreen, click restores minimized app, automatic rehide')
    finally:
        if d: d.close()
        for process in reversed(processes):
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=8)


if __name__ == '__main__':
    main()

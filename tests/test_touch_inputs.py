import importlib.util
from pathlib import Path
import unittest
s=importlib.util.spec_from_file_location('touch_inputs',Path(__file__).resolve().parents[1]/'stelab-kiosk/touch_inputs.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class TouchTests(unittest.TestCase):
 def test_late_node_and_permission_wait(self):
  now=[0.]
  def scan():return [] if now[0]<2 else ['/dev/input/event6']
  result=m.wait_ready(timeout=10,settle=3,scan=scan,can_read=lambda n:now[0]>=4,clock=lambda:now[0],sleep=lambda n:now.__setitem__(0,now[0]+n))
  self.assertTrue(result);self.assertEqual(now[0],7)
 def test_unreadable_has_bounded_wait(self):
  now=[0.]
  self.assertFalse(m.wait_ready(timeout=5,scan=lambda:['/dev/input/event6'],can_read=lambda n:False,clock=lambda:now[0],sleep=lambda n:now.__setitem__(0,now[0]+n)))
  self.assertEqual(now[0],5)
 def test_vendor_independent_direct_touch_only(self):
  text='''Master id=2 [master pointer (3)]
 Touch mode: direct
OddVendor id=7 [slave  pointer (2)]
 Type: XITouchClass
 Touch mode: direct
Trackpad id=8 [slave pointer (2)]
 Touch mode: dependent
Keyboard id=9 [slave keyboard (3)]
'''
  self.assertEqual(m.touch_ids(text),['7'])
 def test_hotplug_retries_failed_mapping_and_reenables(self):
  calls=[];fail=[True]
  def run(*args):
   calls.append(args)
   if args[1]=='--list':return 'Vendor id=7 [slave pointer (2)]\n Touch mode: direct'
   if args[1]=='list-props':return 'Device Node (5): "/dev/input/event6"\nDevice Enabled (2): 0'
   if args[1]=='map-to-output' and fail[0]:raise m.subprocess.CalledProcessError(1,args)
   return ''
  mapped=set()
  with self.assertRaises(m.subprocess.CalledProcessError):m.reconcile('HDMI-1',mapped,run)
  self.assertFalse(mapped);fail[0]=False;m.reconcile('HDMI-1',mapped,run)
  self.assertEqual(mapped,{('7','/dev/input/event6')})
  self.assertIn(('xinput','enable','7'),calls)
if __name__=='__main__':unittest.main()

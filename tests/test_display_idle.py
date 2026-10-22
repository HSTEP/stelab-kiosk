import importlib.util, sys, unittest
from pathlib import Path
from unittest.mock import patch
ADDON=Path(__file__).resolve().parents[1]/'stelab-kiosk'
sys.path.insert(0,str(ADDON))
s=importlib.util.spec_from_file_location('stelab_display_idle',ADDON/'stelab_display_idle.py')
m=importlib.util.module_from_spec(s)
with patch.dict('os.environ', {'SCREEN_TIMEOUT':'120'}):
 s.loader.exec_module(m)
class Tests(unittest.TestCase):
 def test_static_sleeps_at_120(self):
  p=m.IdlePolicy();self.assertTrue(p.decide(0,0,True,False));self.assertTrue(p.decide(119,119,True,False));self.assertFalse(p.decide(120,120,True,False))
 def test_video_inhibits_and_pause_gets_two_minutes(self):
  p=m.IdlePolicy();self.assertTrue(p.decide(500,500,True,True));self.assertTrue(p.decide(900,900,True,True));self.assertTrue(p.decide(1019,1019,True,False));self.assertFalse(p.decide(1020,1020,True,False))
 def test_permanent_presence_has_no_effect_on_timeout(self):
  p=m.IdlePolicy();self.assertFalse(p.decide(130,130,True,False))
 def test_manual_off_wins_even_with_video(self):
  p=m.IdlePolicy();p.decide(10,10,True,True);self.assertFalse(p.decide(12,12,False,True));self.assertFalse(p.decide(20,20,False,True));self.assertTrue(p.decide(21,0,True,True))
 def test_auto_off_can_be_woken_by_video(self):
  p=m.IdlePolicy();self.assertFalse(p.decide(120,120,True,False));p.commanded(False);self.assertTrue(p.decide(122,122,False,True));self.assertFalse(p.manual_off)
 def test_external_wake_gets_full_timeout(self):
  p=m.IdlePolicy();p.decide(500,500,False,False);self.assertTrue(p.decide(501,501,True,False));self.assertTrue(p.decide(620,620,True,False));self.assertFalse(p.decide(621,621,True,False))
 def test_stalled_hidden_or_paused_video_does_not_inhibit_forever(self):
  v=m.VideoDetector();self.assertTrue(v.observe(0,[('a',1,True)]));self.assertTrue(v.observe(2,[('a',2,True)]));self.assertFalse(v.observe(7,[('a',2,True)]));self.assertFalse(v.observe(8,[('a',3,False)]))
if __name__=='__main__':unittest.main(verbosity=2)

"""The clean app environments preserve Supervisor's timezone, not secrets."""
import importlib.util
from pathlib import Path
import os
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]/'stelab-kiosk'
spec=importlib.util.spec_from_file_location('kiosk_browser_timezone',ROOT/'kiosk_browser.py');browser=importlib.util.module_from_spec(spec);spec.loader.exec_module(browser)
class TimezoneEnvironment(unittest.TestCase):
 def test_prague_preserved_without_secrets(self):
  with patch.dict(os.environ,{'TZ':'Europe/Prague','SUPERVISOR_TOKEN':'not-a-real-token','HA_PASSWORD':'not-a-real-password'},clear=True):
   env=browser.environment()
  self.assertEqual(env['TZ'],'Europe/Prague');self.assertNotIn('SUPERVISOR_TOKEN',env);self.assertNotIn('HA_PASSWORD',env)
 def test_utc_fallback(self):
  with patch.dict(os.environ,{},clear=True):self.assertEqual(browser.environment()['TZ'],'Etc/UTC')
 def test_ai_launcher_passes_only_timezone(self):
  source=(ROOT/'stelab-chatgpt.sh').read_text();self.assertIn('TZ="${TZ:-Etc/UTC}"',source);self.assertIn('env -i',source)
if __name__=='__main__':unittest.main()

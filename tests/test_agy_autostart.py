"""The unattended launcher must supply a controlling terminal and resume."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


@unittest.skipUnless(shutil.which("script"), "requires util-linux script")
class AntigravityAutostartTest(unittest.TestCase):
    def test_unattended_launcher_has_controlling_terminal(self):
        helper = Path(__file__).resolve().parents[1] / "stelab-kiosk/agy-autostart.sh"
        with tempfile.TemporaryDirectory() as directory:
            launcher = Path(directory) / "fake launcher"
            launcher.write_text(
                '#!/bin/sh\nset -eu\n'
                'test "$#" -eq 1 && test "$1" = --continue || exit 41\n'
                'test -t 0 && test -t 1 && test -t 2 || exit 42\n'
                'printf "private terminal output\\n" > /dev/tty\n'
            )
            launcher.chmod(0o700)
            run = subprocess.run(
                ["sh", str(helper), str(launcher)], stdin=subprocess.DEVNULL,
                capture_output=True, text=True, timeout=5,
            )
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout, "")

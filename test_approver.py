import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent


class ApproverTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.home = self.root / 'home'
        self.home.mkdir()
        self.plugin = self.root / 'plugin'
        self.plugin.mkdir()
        for name in ('approve.py', 'manage.py', 'config.json'):
            shutil.copy(ROOT / name, self.plugin / name)
        self.env = dict(os.environ, HOME=str(self.home), PYTHONDONTWRITEBYTECODE='1')
        self.config = json.loads((self.plugin / 'config.json').read_text())

    def save(self):
        (self.plugin / 'config.json').write_text(json.dumps(self.config))

    def approve(self, tool='run_command', args=None, raw=None):
        if raw is None:
            raw = json.dumps({'toolCall': {'name': tool, 'args': args if args is not None else {'CommandLine': 'git status'}}})
        result = subprocess.run([sys.executable, str(self.plugin / 'approve.py')], input=raw,
                                text=True, capture_output=True, env=self.env, check=True)
        return json.loads(result.stdout)

    def test_safe_boundary_and_patterns(self):
        for command in ('  sudo reboot', 'echo x; sudo reboot', 'chmod 777 file.txt',
                        'chmod -R 777 .', 'git push -f', 'git push --force', 'rm -rf /'):
            with self.subTest(command=command):
                self.assertEqual(self.approve(args={'CommandLine': command})['decision'], 'ask')
        self.assertEqual(self.approve()['decision'], 'allow')
        self.assertEqual(self.approve(tool='view_file', args={'path': 'a'})['decision'], 'allow')
        self.assertEqual(self.approve(tool='delete_project', args={})['decision'], 'ask')
        for raw in ('', 'not json', '{}', '{"toolCall": {"name": "run_command", "args": {}}}',
                    '{"toolCall": {"name": "run_command", "args": {"CommandLine": null}}}'):
            with self.subTest(raw=raw):
                self.assertEqual(self.approve(raw=raw)['decision'], 'ask')
        self.assertEqual(self.approve(args={'CommandLine': 'echo x | cat'})['decision'], 'ask')

    def test_modes_config_and_management(self):
        self.config['mode'] = 'off'
        self.save()
        self.assertEqual(self.approve()['decision'], 'ask')
        manage = 'python3 ~/.gemini/config/plugins/auto-approver/manage.py mode safe'
        response = self.approve(args={'CommandLine': manage})
        self.assertEqual(response['decision'], 'allow')
        self.assertNotIn('permissionOverrides', response)
        self.assertEqual(self.approve(args={'CommandLine': manage + '; sudo reboot'})['decision'], 'ask')
        self.assertEqual(self.approve(args={'CommandLine': manage + '; git status'})['decision'], 'ask')
        self.assertEqual(self.approve(args={'CommandLine': manage + '$(whoami)'})['decision'], 'ask')
        self.assertEqual(self.approve(args={'CommandLine': manage + ' > /tmp/out'})['decision'], 'ask')
        self.assertEqual(self.approve(args={'CommandLine': 'echo auto-approver manage.py'})['decision'], 'ask')
        self.config['mode'] = 'all'
        self.save()
        self.assertEqual(self.approve(args={'CommandLine': 'sudo reboot'})['decision'], 'allow')
        self.config['mode'] = 'safe'
        self.config['highRiskAction'] = 'bogus'
        self.save()
        self.assertEqual(self.approve()['decision'], 'ask')
        self.config['highRiskAction'] = 'deny'
        self.save()
        self.assertEqual(self.approve(args={'CommandLine': 'sudo reboot'})['decision'], 'deny')
        (self.plugin / 'config.json').write_text('{bad')
        self.assertEqual(self.approve()['decision'], 'ask')
        (self.plugin / 'config.json').unlink()
        self.assertEqual(self.approve()['decision'], 'ask')

    def test_private_log_and_read_only_settings(self):
        settings = self.home / '.gemini' / 'antigravity-cli' / 'settings.json'
        settings.parent.mkdir(parents=True)
        settings.write_text(json.dumps({'trustedWorkspaces': ['/keep']}))
        before = settings.read_bytes()
        self.config['logFile'] = 'private-audit.log'
        self.save()
        secret = 'api-key-test-sentinel'
        self.approve(args={'CommandLine': 'git status --token=' + secret})
        self.approve(tool='view_file', args={'path': '/private/' + secret})
        self.approve(raw='not json')
        self.assertEqual(settings.read_bytes(), before)
        log = self.plugin / 'private-audit.log'
        self.assertTrue(log.exists())
        self.assertNotIn(secret, log.read_text())
        self.assertNotIn('CommandLine=', log.read_text())
        self.assertNotIn('/private/', log.read_text())
        self.assertEqual(log.stat().st_mode & 0o777, 0o600)
        result = subprocess.run([sys.executable, str(self.plugin / 'manage.py'), 'log', '0'],
                                text=True, capture_output=True, env=self.env, check=True)
        self.assertNotIn('tool=', result.stdout)
        result = subprocess.run([sys.executable, str(self.plugin / 'manage.py'), 'log', '10'],
                                text=True, capture_output=True, env=self.env, check=True)
        self.assertIn('tool=', result.stdout)
        self.assertEqual(settings.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()

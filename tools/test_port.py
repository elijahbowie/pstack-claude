"""Behavior checks for safe regeneration and standalone vendoring."""
import contextlib
import hashlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import port


class PortTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'upstream'
        self.dest = self.root / 'port'
        manifest = self.source / '.cursor-plugin' / 'plugin.json'
        manifest.parent.mkdir(parents=True)
        manifest.write_text(json.dumps({
            'name': 'pstack', 'version': '0.15.10', 'description': 'workflow',
            'author': {'name': 'Lauren Tan'}, 'homepage': 'https://example.com',
            'repository': 'https://example.com/repo', 'license': 'MIT', 'keywords': ['workflow'],
        }))
        skill = self.source / 'skills' / 'poteto-mode' / 'SKILL.md'
        skill.parent.mkdir(parents=True)
        skill.write_text('---\nname: Poteto Mode\nmode: true\ndescription: workflow\n'
                         'disable-model-invocation: true\n---\n'
                         'Cursor tool uses /poteto-mode.\n')
        agent = self.source / 'agents' / 'poteto-agent.md'
        agent.parent.mkdir()
        agent.write_text('---\nname: poteto-agent\ndescription: workflow\n'
                         'is_background: true\n---\n'
                         'Use subagent_type: "poteto-agent".\n')
        self.asset = self.source / 'assets' / 'binary.dat'
        self.asset.parent.mkdir()
        self.asset.write_bytes(b'\x00\xff\r\n')
        automation = self.source / 'automations' / 'benny' / 'SKILL.md'
        automation.parent.mkdir(parents=True)
        automation.write_text('Cursor tool uses /poteto-mode.\n')
        self.rules = [('test.tool', 'lit', 'Cursor tool', 'Agent tool', True)]

    def run_port(self, rules=None, source=None):
        with patch.object(port, 'RULES', rules if rules is not None else self.rules), \
             patch('sys.argv', ['port.py', str(source or self.source), '--dest-repo', str(self.dest)]), \
             contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return port.main()

    def snapshot(self):
        return {p.relative_to(self.dest).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in self.dest.rglob('*') if p.is_file()}

    def test_success_is_repeatable_and_preserves_reference_files(self):
        self.assertEqual(self.run_port(), 0)
        before = self.snapshot()
        self.assertEqual(self.run_port(), 0)
        self.assertEqual(self.snapshot(), before)
        plugin = self.dest / 'plugins' / 'pstack'
        skill = (plugin / 'skills' / 'poteto-mode' / 'SKILL.md').read_text()
        self.assertIn('name: poteto-mode', skill)
        self.assertNotIn('\nmode:', skill)
        self.assertIn('disable-model-invocation: true', skill)
        self.assertIn('Agent tool uses /pstack:poteto-mode.', skill)
        agent = (plugin / 'agents' / 'poteto-agent.md').read_text()
        self.assertIn('background: true', agent)
        self.assertIn('subagent_type: "pstack:poteto-agent"', agent)
        self.assertEqual((plugin / 'assets' / 'binary.dat').read_bytes(), self.asset.read_bytes())
        self.assertEqual((plugin / 'automations' / 'benny' / 'SKILL.md').read_text(),
                         'Cursor tool uses /poteto-mode.\n')
        marketplace = json.loads((self.dest / '.claude-plugin' / 'marketplace.json').read_text())
        self.assertEqual(marketplace['plugins'][0]['version'], '0.15.10')

    def test_missing_rule_keeps_existing_destination(self):
        self.assertEqual(self.run_port(), 0)
        before = self.snapshot()
        missing = [('missing', 'lit', 'removed upstream text', 'replacement', True)]
        self.assertEqual(self.run_port(rules=missing), 1)
        self.assertEqual(self.snapshot(), before)

    def test_malformed_frontmatter_keeps_existing_destination(self):
        self.assertEqual(self.run_port(), 0)
        before = self.snapshot()
        skill = self.source / 'skills' / 'poteto-mode' / 'SKILL.md'
        skill.write_text('---\nname: broken\nCursor tool\n')
        with self.assertRaisesRegex(ValueError, 'unterminated frontmatter'):
            self.run_port()
        self.assertEqual(self.snapshot(), before)

    def test_rejects_overlapping_source_and_destination(self):
        overlapping = self.dest / 'plugins' / 'pstack'
        overlapping.mkdir(parents=True)
        import shutil
        shutil.copytree(self.source, overlapping, dirs_exist_ok=True)
        before = self.snapshot()
        with self.assertRaises(SystemExit) as error:
            self.run_port(source=overlapping)
        self.assertEqual(error.exception.code, 2)
        self.assertEqual(self.snapshot(), before)

    def test_vendoring_unscopes_owned_files_and_preserves_other_skills(self):
        # Exercise the shipped script and real generated inventory.
        target = self.root / 'target repo'
        other = target / '.claude' / 'skills' / 'user-skill' / 'SKILL.md'
        other.parent.mkdir(parents=True)
        other.write_text('Keep /pstack:poteto-mode literally here.\n')
        script = Path(__file__).resolve().parent / 'vendor-into-repo.sh'
        subprocess.run(['bash', str(script), str(target)], check=True, capture_output=True, text=True)
        self.assertEqual(other.read_text(), 'Keep /pstack:poteto-mode literally here.\n')
        vendored = (target / '.claude' / 'skills' / 'poteto-mode' / 'SKILL.md').read_text()
        self.assertNotIn('/pstack:', vendored)
        self.assertNotIn('subagent_type: "pstack:', vendored)
        self.assertIn('/poteto-mode', vendored)
        names = {p.parent.name for p in (target / '.claude' / 'skills').glob('*/SKILL.md')}
        self.assertTrue({'correct', 'poteto-help', 'benchmark-checklist', 'principle-explain-the-number'} <= names)


if __name__ == '__main__':
    unittest.main()

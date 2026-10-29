"""Behavioral checks in disposable Git repositories; never touches real projects."""

import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().with_name('check_discovery_scope.py')


class ScopeGuardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='discovery-scope-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.s0, self.code = self.base / 's0', self.base / 'code'
        for root in (self.s0, self.code):
            root.mkdir()
            self.git(root, 'init', '-b', 'main')
            self.git(root, 'config', 'user.name', 'Scope Test')
            self.git(root, 'config', 'user.email', 'scope@example.invalid')
        for name in ('AGENTS.md', 'openspec/config.yaml', '.openspec-store/store.yaml',
                     '.agents/skills/native/SKILL.md', '.agents/skills/project-discovery/SKILL.md',
                     'context/project.md'):
            self.write(self.s0 / name, f'original {name}\n')
        self.write(self.s0 / '.gitignore', '.local/\n')
        self.write(self.code / 'src/app.py', 'original code\n')
        self.write(self.code / '.gitignore', 'cache/\n')
        for root in (self.s0, self.code):
            self.git(root, 'add', '.')
            self.git(root, 'commit', '-m', 'baseline')
        self.serial = 0

    @staticmethod
    def write(path, text):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')

    @staticmethod
    def git(root, *args):
        result = subprocess.run(['git', '-C', str(root), *args], capture_output=True, check=False)
        if result.returncode:
            raise AssertionError(result.stderr.decode(errors='replace'))
        return result.stdout

    def cli(self, *args, expected=0):
        result = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True,
                                encoding='utf-8', check=False)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def snapshot(self):
        self.serial += 1
        path = self.base / f'snapshot-{self.serial}.json'
        self.cli('snapshot', '--s0', self.s0, '--repo', self.code, '--output', path)
        return path

    def verify(self, snapshot, *allowed, expected=0):
        args = ['verify', '--snapshot', snapshot]
        for name in allowed:
            args += ['--allow-context', name]
        return self.cli(*args, expected=expected)

    def test_unchanged_dirty_baseline_is_valid(self):
        self.write(self.s0 / 'openspec/config.yaml', 'preexisting dirty\n')
        self.write(self.code / 'src/app.py', 'preexisting dirty code\n')
        self.write(self.s0 / 'preexisting-untracked.txt', 'untracked\n')
        self.git(self.s0, 'add', 'openspec/config.yaml')
        before = self.git(self.s0, 'status', '--porcelain')
        snapshot = self.snapshot()
        self.assertTrue(self.verify(snapshot)['ok'])
        self.assertEqual(before, self.git(self.s0, 'status', '--porcelain'))

    def test_context_changes_require_exact_allowlist_and_support_new_component(self):
        snapshot = self.snapshot()
        self.write(self.s0 / 'context/project.md', 'approved revision\n')
        self.write(self.s0 / 'context/components/api.md', 'approved new component\n')
        self.verify(snapshot, expected=1)
        self.verify(snapshot, 'context/project.md', expected=1)
        self.verify(snapshot, 'context/project.md', 'context/components/api.md')

    def test_arbitrary_context_subdirectories_still_require_exact_approved_files(self):
        approved = 'context/integrations/existing.md'
        self.write(self.s0 / approved, 'existing integration\n')
        snapshot = self.snapshot()
        self.write(self.s0 / approved, 'approved revised integration\n')
        self.verify(snapshot, approved)
        self.write(self.s0 / 'context/integrations/unapproved.md', 'not approved\n')
        result = self.verify(snapshot, approved, expected=1)
        self.assertEqual([item['path'] for item in result['violations']],
                         ['context/integrations/unapproved.md'])

    def test_protected_paths_remain_protected_even_when_already_dirty(self):
        protected = ('openspec/config.yaml', '.openspec-store/store.yaml', 'AGENTS.md',
                     '.agents/skills/native/SKILL.md', '.agents/skills/project-discovery/SKILL.md')
        for name in protected:
            with self.subTest(path=name):
                self.write(self.s0 / name, 'dirty before snapshot\n')
                snapshot = self.snapshot()
                self.write(self.s0 / name, 'changed after snapshot\n')
                result = self.verify(snapshot, 'context/project.md', expected=1)
                self.assertTrue(any(item['path'] == name for item in result['violations']))

    def test_new_ignored_and_nonignored_s0_files_are_detected(self):
        snapshot = self.snapshot()
        self.write(self.s0 / '.local/protected.txt', 'ignored secret content\n')
        self.write(self.s0 / 'new.txt', 'new\n')
        result = self.verify(snapshot, expected=1)
        self.assertEqual({item['path'] for item in result['violations']}, {'.local', '.local/protected.txt', 'new.txt'})
        self.assertNotIn('ignored secret content', snapshot.read_text())
        self.assertNotIn('ignored secret content', json.dumps(result))

    def test_protected_deletion_and_rename_are_detected(self):
        snapshot = self.snapshot()
        (self.s0 / 'AGENTS.md').unlink()
        (self.s0 / '.openspec-store/store.yaml').rename(self.s0 / '.openspec-store/renamed.yaml')
        result = self.verify(snapshot, expected=1)
        changes = {(item['path'], item['change']) for item in result['violations']}
        self.assertIn(('AGENTS.md', 'deleted'), changes)
        self.assertIn(('.openspec-store/store.yaml', 'deleted'), changes)
        self.assertIn(('.openspec-store/renamed.yaml', 'added'), changes)

    def test_code_is_readonly_relative_to_dirty_baseline(self):
        self.write(self.code / 'src/app.py', 'old dirty code\n')
        snapshot = self.snapshot()
        self.write(self.code / 'src/app.py', 'new dirty code\n')
        self.write(self.code / 'new-test.py', 'new test\n')
        result = self.verify(snapshot, 'context/project.md', expected=1)
        self.assertEqual({item['path'] for item in result['violations']}, {'src/app.py', 'new-test.py'})

    def test_code_ignored_untracked_limit_and_tracked_ignored_file(self):
        self.write(self.code / 'cache/tracked.txt', 'tracked despite ignore\n')
        self.git(self.code, 'add', '-f', 'cache/tracked.txt')
        snapshot = self.snapshot()
        self.write(self.code / 'cache/not-tracked.txt', 'outside documented code coverage\n')
        self.verify(snapshot)
        self.write(self.code / 'cache/tracked.txt', 'must still detect\n')
        self.verify(snapshot, expected=1)

    def test_index_and_head_changes_are_detected_even_for_allowed_context(self):
        snapshot = self.snapshot()
        self.write(self.s0 / 'context/project.md', 'approved content\n')
        self.git(self.s0, 'add', 'context/project.md')
        result = self.verify(snapshot, 'context/project.md', expected=1)
        self.assertTrue(any(item['path'] == '.git/index' for item in result['violations']))
        self.git(self.s0, 'commit', '-m', 'not authorized by scope check')
        result = self.verify(snapshot, 'context/project.md', expected=1)
        self.assertTrue(any(item['path'] == '.git/head' for item in result['violations']))

    def test_stat_cache_refresh_is_not_staging_but_index_flags_are(self):
        snapshot = self.snapshot()
        os.utime(self.code / 'src/app.py', None)
        self.git(self.code, 'status', '--porcelain')
        self.verify(snapshot)
        self.git(self.code, 'update-index', '--assume-unchanged', 'src/app.py')
        result = self.verify(snapshot, expected=1)
        self.assertTrue(any(item['path'] == '.git/index' for item in result['violations']))

    def test_permission_change_without_content_or_index_change_is_detected(self):
        snapshot = self.snapshot()
        target = self.code / 'src/app.py'
        original = stat.S_IMODE(target.stat().st_mode)
        changed = original & ~stat.S_IWUSR if os.name == 'nt' else original ^ stat.S_IXUSR
        try:
            target.chmod(changed)
            if stat.S_IMODE(target.stat().st_mode) == original:
                self.skipTest('Filesystem does not expose changed file mode')
            result = self.verify(snapshot, expected=1)
            self.assertTrue(any(item['path'] == 'src/app.py' for item in result['violations']))
        finally:
            target.chmod(original)

    def test_nested_git_metadata_fails_closed_in_s0(self):
        snapshot = self.snapshot()
        self.write(self.s0 / 'context/.git/hidden.txt', 'must not be invisible\n')
        self.verify(snapshot, 'context/project.md', expected=2)
        self.cli('snapshot', '--s0', self.s0, '--output', self.base / 'nested.json', expected=2)

    def test_snapshot_is_external_exclusive_and_roots_are_git_roots(self):
        for target in (self.s0 / 'snapshot.json', self.code / 'snapshot.json'):
            self.cli('snapshot', '--s0', self.s0, '--repo', self.code, '--output', target, expected=2)
            self.assertFalse(target.exists())
        snapshot = self.snapshot()
        before = snapshot.read_bytes()
        self.cli('snapshot', '--s0', self.s0, '--output', snapshot, expected=2)
        self.assertEqual(before, snapshot.read_bytes())
        self.cli('snapshot', '--s0', self.s0 / 'context', '--output', self.base / 'bad.json', expected=2)

    def test_allowlist_rejects_escape_protected_and_windows_aliases(self):
        snapshot = self.snapshot()
        for name in ('AGENTS.md', '../context/project.md', '/context/project.md',
                     'C:/context/project.md', 'context/../AGENTS.md', 'context/.GIT/config.md',
                     'context/project.md:extra', 'context/project.MD', 'context/project.md.',
                     'context/project.md ', 'context/CON.md', 'context/projec~1.md',
                     'context\\project.md', 'context//project.md'):
            with self.subTest(name=name):
                self.verify(snapshot, name, expected=2)

    def test_case_alias_and_hardlink_context_targets_are_rejected(self):
        snapshot = self.snapshot()
        self.verify(snapshot, 'context/PROJECT.md', expected=2)
        alias = self.s0 / 'context/alias.md'
        try:
            os.link(self.s0 / 'AGENTS.md', alias)
        except OSError as error:
            self.skipTest(f'Hardlinks unavailable: {error}')
        self.verify(snapshot, 'context/alias.md', expected=2)

    def test_symlink_context_target_and_parent_are_rejected(self):
        snapshot = self.snapshot()
        outside = self.base / 'external.md'
        self.write(outside, 'outside\n')
        link = self.s0 / 'context/link.md'
        try:
            link.symlink_to(outside)
        except OSError as error:
            self.skipTest(f'Symlinks unavailable: {error}')
        self.verify(snapshot, 'context/link.md', expected=2)
        self.verify(snapshot, expected=1)
        link.unlink()
        (self.s0 / 'context/components').symlink_to(self.base, target_is_directory=True)
        self.verify(snapshot, 'context/components/external.md', expected=2)

    @unittest.skipUnless(os.name == 'nt' and shutil.which('powershell'), 'Windows junction test')
    def test_junction_parent_is_rejected_without_reading_target(self):
        snapshot = self.snapshot()
        outside = self.base / 'external'
        self.write(outside / 'private.md', 'do not traverse\n')
        junction = self.s0 / 'context/components'
        env = dict(os.environ, DISCOVERY_TEST_LINK=str(junction), DISCOVERY_TEST_TARGET=str(outside))
        command = "$ErrorActionPreference='Stop'; New-Item -ItemType Junction -Path $env:DISCOVERY_TEST_LINK -Target $env:DISCOVERY_TEST_TARGET | Out-Null"
        result = subprocess.run(['powershell', '-NoProfile', '-Command', command], env=env, capture_output=True)
        if result.returncode:
            self.skipTest('Junction creation unavailable')
        self.verify(snapshot, 'context/components/private.md', expected=2)
        result = self.verify(snapshot, expected=1)
        self.assertFalse(any(item['path'].endswith('private.md') for item in result['violations']))

    def test_snapshot_schema_rejects_tampered_paths_and_duplicate_keys(self):
        snapshot = self.snapshot()
        original = json.loads(snapshot.read_text())
        for name in ('../secret', '.GIT/config', 'context/project.md:stream'):
            data = json.loads(json.dumps(original))
            data['roots'][0]['files'][name] = ['file', '0' * 64]
            snapshot.write_text(json.dumps(data), encoding='utf-8')
            self.verify(snapshot, expected=2)
        snapshot.write_text('{"version":1,"version":1,"roots":[]}', encoding='utf-8')
        self.verify(snapshot, expected=2)


if __name__ == '__main__':
    unittest.main()

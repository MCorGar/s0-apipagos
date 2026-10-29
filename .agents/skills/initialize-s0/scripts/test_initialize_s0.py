"""Behavioral checks in disposable Git repositories with a fake OpenSpec CLI.

Never touches real projects, the user's OpenSpec registry or Codex home. Set
S0_OPENSPEC_BIN to a real CLI to also run the end-to-end check against it.
"""

import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import textwrap
import unittest


SCRIPT = Path(__file__).resolve().with_name('initialize_s0.py')
REFERENCE = Path(__file__).resolve().parents[2] / 'connect-project' / 'references' / 'integrate-consumers.md'
sys.path.insert(0, str(SCRIPT.parent))
import initialize_s0  # noqa: E402

# Minimal stand-in for the commands the script uses. Stores live in
# $XDG_DATA_HOME/stores.json; init writes fixed bytes and needs delivery=both.
FAKE_CLI = textwrap.dedent('''
    import json, os, sys
    from pathlib import Path
    args, cwd = sys.argv[1:], Path.cwd()
    version = os.environ.get('FAKE_VERSION', '1.14.3')
    data = Path(os.environ['XDG_DATA_HOME'], 'stores.json')
    stores = json.loads(data.read_text()) if data.exists() else []
    config = Path(os.environ['XDG_CONFIG_HOME'], 'openspec', 'config.json')
    def pointer():
        path = cwd / 'openspec' / 'config.yaml'
        text = path.read_text() if path.exists() else ''
        return text.split('store:')[1].strip() if text.startswith('store:') else None
    if args == ['--version']:
        print(version)
    elif args[:2] == ['store', 'list']:
        print(json.dumps({'stores': stores, 'status': []}))
    elif args[:2] == ['store', 'doctor'] or args[:2] == ['status', '--all']:
        sys.exit(0 if (pointer() or any(s['id'] in args for s in stores)) else 1)
    elif args[:3] == ['config', 'set', 'delivery']:
        config.parent.mkdir(parents=True, exist_ok=True)
        config.write_text(json.dumps({'delivery': args[3]}))
    elif args[0] == 'init':
        if not config.exists() or json.loads(config.read_text()).get('delivery') != 'both':
            sys.exit('delivery not set')
        if pointer() and version != '1.14.3':
            sys.exit('init rejected with store:')
        log = os.environ.get('FAKE_INIT_LOG')
        if log:
            with open(log, 'a') as handle:
                handle.write(str(cwd) + '\\n')
        for tool in args[2].split(','):
            for name in ('explore', 'propose'):
                base = '.claude' if tool == 'claude' else '.agents'
                path = cwd / base / 'skills' / f'openspec-{name}' / 'SKILL.md'
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(f'generated {name} {version}\\n')
    elif args == ['context', '--json']:
        root = next((s['root'] for s in stores if s['id'] == pointer()), None)
        if root is None:
            sys.exit(1)
        print(json.dumps({'root': {'path': root}}))
    else:
        sys.exit(f'unsupported {args}')
''')


class Sandbox(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='initialize-s0-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.env = {key: value for key, value in os.environ.items() if not key.startswith('GIT_')}
        for name in ('data', 'config', 'codex', 'home'):
            (self.base / name).mkdir()
        self.env.update(XDG_DATA_HOME=str(self.base / 'data'), XDG_CONFIG_HOME=str(self.base / 'config'),
                        CODEX_HOME=str(self.base / 'codex'), GIT_CONFIG_GLOBAL=str(self.base / 'gitconfig'),
                        GIT_CONFIG_NOSYSTEM='1', HOME=str(self.base / 'home'))
        self.cli = self.base / 'bin' / 'openspec.py'
        self.write(self.cli, FAKE_CLI)
        self.s0 = self.repo('s0', 'https://user:token@github.com/acme/s0-pagos.git')
        for name, text in {'AGENTS.md': '# S0\n', 'openspec/config.yaml': 'schema: spec-driven\n',
                           '.openspec-store/store.yaml': 'version: 1\nid: pagos\n',
                           'context/project.md': '# S0 Core — contexto de la plantilla\n',
                           'repositories.yaml': '# comentario\nversion: 1\nrepositories: []\n'}.items():
            self.write(self.s0 / name, text)
        self.register('pagos', self.s0)

    @staticmethod
    def write(path, text):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')

    def git(self, root, *args):
        result = subprocess.run(['git', '-C', str(root), *args], capture_output=True, env=self.env, check=False)
        if result.returncode:
            raise AssertionError(result.stderr.decode(errors='replace'))
        return result.stdout.decode().strip()

    def repo(self, name, remote=None):
        root = self.base / 'src' / name if name != 's0' else self.base / name
        root.mkdir(parents=True)
        self.git(root, 'init', '-q', '-b', 'main')
        if remote:
            self.git(root, 'remote', 'add', 'origin', remote)
        return root.resolve()

    def register(self, sid, root):
        path = self.base / 'data' / 'stores.json'
        stores = json.loads(path.read_text()) if path.exists() else []
        path.write_text(json.dumps(stores + [{'id': sid, 'root': str(root)}]))

    def run_cli(self, *args, expected=0, cli_version=None):
        wrapper = self.base / 'bin' / ('openspec.cmd' if os.name == 'nt' else 'openspec')
        if not wrapper.exists():
            body = (f'@"{sys.executable}" "{self.cli}" %*\n' if os.name == 'nt'
                    else f'#!/bin/sh\nexec "{sys.executable}" "{self.cli}" "$@"\n')
            wrapper.write_text(body)
            wrapper.chmod(0o755)
        env = dict(self.env, FAKE_VERSION=cli_version or '1.14.3')
        result = subprocess.run([sys.executable, str(SCRIPT), *map(str, args), '--openspec', str(wrapper)],
                                cwd=self.s0, capture_output=True, encoding='utf-8', env=env, check=False)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def consumers(self, *roots):
        return [arg for root in roots for arg in ('--consumer', root)]

    def tree(self, root):
        return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*')
                if p.is_file() and '.git' not in p.relative_to(root).parts}


class InitializeS0Tests(Sandbox):
    # --- diagnose ---------------------------------------------------------

    def test_diagnose_classifies_and_strips_credentials(self):
        self.assertEqual(self.run_cli('diagnose')['state'], 'C')
        self.write(self.s0 / '.openspec-store/store.yaml', 'version: 1\nid: s0-core\n')
        result = self.run_cli('diagnose')
        self.assertEqual(result['state'], 'B')
        self.assertEqual(result['s0']['remote'], 'https://github.com/acme/s0-pagos.git')
        self.git(self.s0, 'remote', 'set-url', 'origin', 'git@github.com:nuamx/nuam-ia-arq-sdd-openspec.git')
        self.assertEqual(self.run_cli('diagnose')['state'], 'A')

    def test_diagnose_identity_states(self):
        self.write(self.s0 / 'context/project.md', '# Pagos\n')
        self.assertEqual(self.run_cli('diagnose')['state'], 'C')
        self.write(self.s0 / '.openspec-store/store.yaml', 'version: 1\nid: s0-core\n')
        self.write(self.s0 / 'openspec/specs/pagos/spec.md', 'x\n')
        result = self.run_cli('diagnose')
        self.assertEqual(result['state'], 'ambiguous')
        self.assertIn('specs', ' '.join(result['reasons']))

    def test_diagnose_lists_candidates_without_writing(self):
        api = self.repo('api', 'git@github.com:acme/api.git')
        self.write(api / 'AGENTS.md', '# api\n')
        other = self.repo('other-s0', 'git@github.com:acme/s0-otro.git')
        self.write(other / '.openspec-store/store.yaml', 'id: otro\n')
        (self.base / 'src' / 'plain').mkdir()
        before = self.tree(api)
        result = self.run_cli('diagnose', '--base', self.base / 'src')
        by_name = {Path(c['path']).name: c for c in result['candidates']}
        self.assertEqual(set(by_name), {'api', 'other-s0'})
        self.assertEqual(by_name['api']['agents'], 'append')
        self.assertEqual(by_name['other-s0']['excluded'], 'other-s0')
        self.assertEqual(result['registry'], {'state': 'registered'})
        self.assertEqual(self.tree(api), before)

    # --- plan and apply ---------------------------------------------------

    def test_plan_is_read_only_and_reports_conflicts(self):
        fresh = self.repo('fresh', 'git@github.com:acme/fresh.git')
        other = self.repo('other', 'git@github.com:acme/other.git')
        self.write(other / 'openspec/config.yaml', 'store: ajeno\n')
        local = self.repo('local', 'git@github.com:acme/local.git')
        self.write(local / 'openspec/changes/x/proposal.md', 'x\n')
        adapted = self.repo('adapted', 'git@github.com:acme/adapted.git')
        self.write(adapted / '.claude/skills/openspec-explore/SKILL.md', 'adaptado\n')
        before = {r: self.tree(r) for r in (fresh, other, local, adapted)}
        result = self.run_cli('plan', *self.consumers(fresh, other, local, adapted, self.s0), expected=1)
        states = [c['result'] for c in result['consumers']]
        self.assertEqual(states, ['ready', 'blocked:config-other-store', 'blocked:local-planning',
                                  'pending', 'blocked:contains-or-inside-s0'])
        self.assertEqual(result['consumers'][3]['actions']['init']['files'],
                         ['.claude/skills/openspec-explore/SKILL.md'])
        self.assertEqual({r: self.tree(r) for r in before}, before)
        self.assertFalse((self.base / 'config' / 'openspec').exists())

    def test_apply_connects_and_is_idempotent(self):
        api = self.repo('api', 'git@github.com:acme/api.git')
        self.write(api / 'AGENTS.md', '# reglas api\n')
        self.write(api / 'CLAUDE.md', 'notas\n')
        result = self.run_cli('apply-consumers', *self.consumers(api))
        self.assertEqual(result['consumers'][0]['result'], 'connected')
        self.assertEqual((api / 'openspec/config.yaml').read_text(), 'store: pagos\n')
        agents = (api / 'AGENTS.md').read_text()
        self.assertTrue(agents.startswith('# reglas api\n\n<!-- s0-connection:start -->'))
        self.assertIn('en el S0 pagos.', agents)
        self.assertEqual((api / 'CLAUDE.md').read_text(), '@AGENTS.md\n\nnotas\n')
        self.assertTrue((api / '.agents/skills/openspec-propose/SKILL.md').is_file())
        self.assertFalse((self.base / 'config' / 'openspec').exists(), 'user delivery must not change')
        snapshot = self.tree(api)
        log = self.base / 'init.log'
        self.env['FAKE_INIT_LOG'] = str(log)
        again = self.run_cli('apply-consumers', *self.consumers(api))
        self.assertEqual(again['consumers'][0]['done'], [])
        self.assertEqual(self.tree(api), snapshot)
        self.assertNotIn(str(api), log.read_text(), 'init must not rerun when integrations are present')

    def test_apply_updates_only_the_block(self):
        api = self.repo('api')
        old = '<!-- s0-connection:start -->\nviejo\n<!-- s0-connection:end -->\n'
        self.write(api / 'AGENTS.md', f'# a\n\n{old}\n# b\n')
        self.write(api / 'openspec/config.yaml', 'store: pagos\n')
        self.run_cli('apply-consumers', *self.consumers(api))
        text = (api / 'AGENTS.md').read_text()
        self.assertTrue(text.startswith('# a\n\n<!-- s0-connection:start -->\nEl contexto'))
        self.assertTrue(text.endswith('<!-- s0-connection:end -->\n\n# b\n'))
        self.assertEqual(text.count('s0-connection:start'), 1)

    def test_codex_global_prompts_leave_everything_pending(self):
        api = self.repo('api')
        self.write(self.base / 'codex/prompts/opsx-propose.md', 'x\n')
        result = self.run_cli('apply-consumers', *self.consumers(api), expected=1)
        self.assertIn('codex-global-prompts', result['blockers'])
        self.assertEqual(result['consumers'][0]['result'], 'pending')
        self.assertEqual(self.tree(api), {})
        self.run_cli('apply-consumers', '--tools', 'claude', *self.consumers(api))

    def test_cli_without_capability_or_unknown_version(self):
        api = self.repo('api')
        for version, reason in (('1.13.2', 'cli-without-consumer-init'), ('9.9.9', 'cli-version-unchecked')):
            result = self.run_cli('apply-consumers', *self.consumers(api), expected=1, cli_version=version)
            self.assertEqual(result['blockers'], [reason])
            self.assertEqual(self.tree(api), {})

    def test_unregistered_store_and_identity_conflict(self):
        (self.base / 'data' / 'stores.json').write_text('[]')
        api = self.repo('api')
        result = self.run_cli('apply-consumers', *self.consumers(api), expected=1)
        self.assertEqual(result['blockers'], ['store-missing'])
        self.assertEqual(self.tree(api), {})
        self.assertIn('contradicts', self.run_cli('plan', '--id', 'otro', expected=2)['error'])

    # --- locator and catalog ----------------------------------------------

    def locator(self):
        return Path(self.git(self.s0, 'rev-parse', '--absolute-git-dir'), 's0-local-sources.json')

    def test_locator_merges_and_rejects(self):
        api = self.repo('api', 'https://u:p@github.com/acme/api.git')
        web = self.repo('web')
        result = self.run_cli('write-locator', '--source', api, '--source', self.s0,
                              '--source', self.base / 'missing', expected=1)
        self.assertEqual([r['reason'] for r in result['rejected']], ['s0-root', 'not-git-root'])
        data = json.loads(self.locator().read_text())
        self.assertEqual(data['s0'], {'id': 'pagos', 'root': str(self.s0)})
        self.assertEqual(data['repositories'], [{'path': str(api), 'remote': 'https://github.com/acme/api.git'}])
        self.run_cli('write-locator', '--source', web)
        self.assertEqual(len(json.loads(self.locator().read_text())['repositories']), 2)
        self.assertFalse(self.run_cli('write-locator', '--source', web)['written'])

    def test_foreign_locator_is_kept(self):
        foreign = '{"version": 1, "s0": {"id": "otro", "root": "/x"}, "repositories": []}\n'
        self.locator().write_text(foreign)
        result = self.run_cli('write-locator', '--source', self.repo('api'), expected=2)
        self.assertIn('foreign', result['error'])
        self.assertEqual(self.locator().read_text(), foreign)

    def test_catalog_resolves_branches_and_keeps_comments(self):
        bare = self.base / 'remote' / 'api.git'
        bare.parent.mkdir()
        seed = self.repo('seed')
        self.write(seed / 'f', 'x\n')
        self.git(seed, 'add', '.')
        self.git(seed, '-c', 'user.name=t', '-c', 'user.email=t@example.invalid', 'commit', '-qm', 'x')
        self.git(seed, 'branch', '-m', 'trunk')
        subprocess.run(['git', 'clone', '-q', '--bare', str(seed), str(bare)], env=self.env, check=True)
        (self.base / 'gitconfig').write_text(f'[url "{bare.as_uri()}"]\n\tinsteadOf = https://example.invalid/api.git\n')
        result = self.run_cli('write-catalog', '--entry', 'api', 'https://example.invalid/api.git',
                              '--entry', 'web', 'git@example.invalid:acme/web.git', '--branch', 'web', 'main')
        self.assertEqual([(a['id'], a['branch']) for a in result['added']], [('api', 'trunk'), ('web', 'main')])
        text = (self.s0 / 'repositories.yaml').read_text()
        self.assertTrue(text.startswith('# comentario\nversion: 1\nrepositories:\n  - id: api\n'))
        again = self.run_cli('write-catalog', '--entry', 'api', 'git@example.invalid:fork/api.git',
                             '--entry', 'web', 'https://example.invalid/acme/web', '--branch', 'api', 'x', expected=1)
        self.assertEqual((again['kept'], again['conflicts']), (['web'], ['api']))
        self.assertEqual((self.s0 / 'repositories.yaml').read_text(), text)
        self.assertIn('without credentials',
                      self.run_cli('write-catalog', '--entry', 'x', 'https://u:t@h/x.git', expected=2)['error'])

    def test_catalog_without_remote_answer_omits_branch(self):
        result = self.run_cli('write-catalog', '--entry', 'api', 'https://unreachable.invalid/api.git')
        self.assertEqual(result['without_branch'], ['api'])
        self.assertNotIn('branch:', (self.s0 / 'repositories.yaml').read_text())

    # --- verify and contracts ---------------------------------------------

    def test_verify_reports_missing_parts(self):
        api = self.repo('api')
        self.run_cli('apply-consumers', '--tools', 'codex', *self.consumers(api))
        ok = self.run_cli('verify', '--tools', 'codex', *self.consumers(api), expected=1)
        # The fake CLI renders two workflows; the real core profile renders six.
        self.assertEqual(len(ok['consumers'][0]['missing_integrations']), 4)
        self.assertTrue(ok['consumers'][0]['context_resolves'] and ok['consumers'][0]['agents_block'])
        (api / 'CLAUDE.md').unlink()
        self.assertFalse(self.run_cli('verify', '--tools', 'codex', *self.consumers(api),
                                      expected=1)['consumers'][0]['claude_import'])

    def test_block_matches_reference_document(self):
        text = REFERENCE.read_text(encoding='utf-8')
        documented = re.search(r'```text\n(<!-- s0-connection:start -->.*?<!-- s0-connection:end -->\n)```',
                               text, re.S).group(1)
        self.assertEqual(documented, initialize_s0.block('<id>'))

    def test_remote_identity(self):
        key = initialize_s0.remote_key
        self.assertEqual(key('git@github.com:Acme/Api.git'), key('https://github.com/Acme/Api'))
        self.assertEqual(key('ssh://git@github.com/Acme/Api.git'), 'github.com/Acme/Api')
        self.assertNotEqual(key('https://gitlab.com/Acme/Api'), key('https://github.com/Acme/Api'))
        self.assertEqual(initialize_s0.clean_url('https://x:y@h.com/a.git'), 'https://h.com/a.git')
        self.assertEqual(initialize_s0.clean_url('ssh://git@h.com/a.git'), 'ssh://git@h.com/a.git')


@unittest.skipUnless(os.environ.get('S0_OPENSPEC_BIN'), 'S0_OPENSPEC_BIN not set')
class RealCliTests(Sandbox):
    """Same flow against a real CLI, with registry and Codex home kept temporary."""

    def test_real_cli_connects_consumer(self):
        real = os.environ['S0_OPENSPEC_BIN']
        env = dict(self.env, XDG_DATA_HOME=str(self.base / 'real-data'))
        subprocess.run([real, 'store', 'register', '.'], cwd=self.s0, env=env, capture_output=True, check=True)
        api = self.repo('api')
        for command in ('apply-consumers', 'verify'):
            result = subprocess.run([sys.executable, str(SCRIPT), command, '--consumer', str(api),
                                     '--openspec', real], cwd=self.s0, env=env, capture_output=True,
                                    encoding='utf-8', check=False)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()

#!/usr/bin/env python3
"""Deterministic steps of initialize-s0: diagnose, plan, consumer integration,
locator, catalog and verification. Every command prints one JSON document.

Python >=3.10, Git and, for plan/apply/verify, the OpenSpec CLI passed with
--openspec (default: `openspec` in PATH). diagnose and plan never write.
apply-consumers, write-locator and write-catalog write only the files named in
their plan, atomically, and are idempotent. No command stages, commits, pushes,
changes branches, registers stores, changes `origin` or edits user-level OpenSpec
configuration: `init` runs with a temporary XDG_CONFIG_HOME and `delivery both`.

Exit codes: 0 done, 1 something stayed pending or failed a check, 2 usage error.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import urlsplit, urlunsplit


MASTER = 'github.com/nuamx/nuam-ia-arq-sdd-openspec'
TEMPLATE_HEADING = '# S0 Core — contexto de la plantilla'
TEMPLATE_ID = 's0-core'
# Behaviour checked by hand per version; an unknown version leaves init pending.
CONSUMER_INIT = {'1.14.3': True, '1.13.2': False}
CORE_WORKFLOWS = ('apply-change', 'archive-change', 'explore', 'propose', 'sync-specs', 'update-change')
CODEX_PROMPTS = tuple(f'opsx-{name}.md' for name in (
    'propose', 'explore', 'new', 'continue', 'apply', 'update', 'ff', 'sync',
    'archive', 'bulk-archive', 'verify', 'onboard'))
INIT_ARGS = ('init', '--tools', '{tools}', '--profile', 'core', '--no-animation')
LOCATOR = 's0-local-sources.json'
BLOCK_START, BLOCK_END = '<!-- s0-connection:start -->', '<!-- s0-connection:end -->'
BLOCK_BODY = """El contexto y las especificaciones compartidas de este sistema están en el S0 {id}.
Comprueba el ejecutable OpenSpec y usa las capacidades que requiere la tarea.
Consulta la compatibilidad y las instrucciones vigentes del S0 resuelto.
Desde esta raíz, ejecuta openspec context --json y lee root.path.
Antes de planificar, lee AGENTS.md y context/project.md en esa raíz resuelta.
Mantén las specs y los artefactos OpenSpec allí; el código y sus tests van en
los repositorios afectados. Lee las skills propias desde la raíz S0 cuando
corresponda; registrar el store no las instala en este consumidor."""
ID_PATTERN = re.compile(r'^[a-z0-9][a-z0-9-]*$')


class UsageError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise UsageError(message)


def run(cmd, cwd=None, env=None, timeout=300):
    try:
        result = subprocess.run([str(part) for part in cmd], cwd=cwd, env=env, capture_output=True,
                                encoding='utf-8', errors='replace', timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        return 127, '', str(error)
    return result.returncode, result.stdout, result.stderr


def git(root, *args):
    code, out, _ = run(['git', '--no-optional-locks', '-C', root, *args])
    return out.strip() if code == 0 else None


def git_root(path):
    path = Path(path)
    if not path.is_dir():
        return None
    top = git(path, 'rev-parse', '--show-toplevel')
    if top is None or Path(top).resolve() != path.resolve():
        return None
    return path.resolve()


def inside(path, root):
    return path == root or root in path.parents


def clean_url(url):
    if not url:
        return None
    parts = urlsplit(url)
    if parts.scheme and parts.netloc and '@' in parts.netloc:
        host = parts.netloc.rsplit('@', 1)[1]
        user = parts.netloc.rsplit('@', 1)[0]
        keep = parts.scheme == 'ssh' and ':' not in user
        return urlunsplit(parts._replace(netloc=f'{user}@{host}' if keep else host))
    return url


def remote_key(url):
    """host/path identity: HTTPS and SSH of the same repository compare equal."""
    if not url:
        return None
    match = re.match(r'^(?:[^@/]+@)?([^:/]+):(?!//)(.+)$', url)
    if match and '://' not in url:
        host, path = match.groups()
    else:
        parts = urlsplit(url)
        host, path = (parts.hostname or ''), parts.path
    path = path.strip('/')
    path = path[:-4] if path.endswith('.git') else path
    return f'{host.lower()}/{path}' if host else path


def origin(root):
    return clean_url(git(root, 'config', '--get', 'remote.origin.url'))


def read_text(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError):
        return None


def scalar(text, key):
    match = re.search(rf'^{key}:\s*["\']?([^"\'#\s]+)', text or '', re.M)
    return match.group(1) if match else None


def write_atomic(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=f'.{path.name}.', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as handle:
            handle.write(data.encode('utf-8') if isinstance(data, str) else data)
        os.replace(temp, path)
    except BaseException:
        Path(temp).unlink(missing_ok=True)
        raise


def entries(path):
    return sorted(item.name for item in Path(path).iterdir()
                  if not item.name.startswith('.')) if Path(path).is_dir() else []


# --- S0 -------------------------------------------------------------------

def s0_root(value):
    root = git_root(value)
    require(root is not None, f'Not a Git root: {value}')
    require((root / 'AGENTS.md').is_file() and (root / 'openspec').is_dir(),
            'The S0 root needs AGENTS.md and openspec/')
    return root


def store_id(root):
    return scalar(read_text(root / '.openspec-store' / 'store.yaml'), 'id')


def is_s0(root):
    return (root / '.openspec-store' / 'store.yaml').is_file()


def parse_catalog(root):
    text = read_text(root / 'repositories.yaml')
    if text is None:
        return {'present': False, 'valid': True, 'entries': []}
    body = [line for line in text.splitlines() if line.strip() and not line.lstrip().startswith('#')]
    if scalar(text, 'version') != '1' or not any(re.match(r'^repositories:', line) for line in body):
        return {'present': True, 'valid': False, 'entries': []}
    if re.search(r'^repositories:\s*\[\s*\]\s*$', text, re.M):
        return {'present': True, 'valid': True, 'entries': []}
    items, current = [], None
    for line in text.splitlines()[[i for i, l in enumerate(text.splitlines())
                                   if l.startswith('repositories:')][0] + 1:]:
        if re.match(r'^\S', line) and not line.startswith('#'):
            break
        item = re.match(r'^\s+-\s+id:\s*(\S+)\s*$', line)
        field = re.match(r'^\s+(remote|branch):\s*(\S+)\s*$', line)
        if item:
            current = {'id': item.group(1)}
            items.append(current)
        elif field and current is not None:
            current[field.group(1)] = field.group(2)
        elif line.strip() and not line.lstrip().startswith('#'):
            return {'present': True, 'valid': False, 'entries': []}
    valid = all('remote' in item for item in items) and len({i['id'] for i in items}) == len(items)
    return {'present': True, 'valid': valid, 'entries': items if valid else []}


def locator_path(root):
    value = git(root, 'rev-parse', '--git-path', LOCATOR)
    require(value is not None, 'Cannot resolve the Git metadata path of the S0')
    path = Path(value)
    path = path if path.is_absolute() else root / path
    metadata = [Path(p if Path(p).is_absolute() else root / p).resolve() for p in
                filter(None, (git(root, 'rev-parse', '--git-dir'), git(root, 'rev-parse', '--git-common-dir')))]
    require(not path.is_symlink() and any(inside(path.parent.resolve(), base) for base in metadata),
            'The locator path leaves the Git metadata of the S0')
    return path


def read_locator(root, sid):
    path = locator_path(root)
    if not path.exists():
        return path, {'state': 'absent', 'repositories': []}
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        valid = (data.get('version') == 1 and isinstance(data.get('s0'), dict)
                 and isinstance(data.get('repositories'), list)
                 and all(isinstance(item, dict) and isinstance(item.get('path'), str)
                         and (item.get('remote') is None or isinstance(item.get('remote'), str))
                         for item in data['repositories']))
    except (OSError, ValueError, AttributeError):
        valid = False
    if not valid:
        return path, {'state': 'invalid', 'repositories': []}
    owner = data['s0']
    if owner.get('id') != sid or Path(str(owner.get('root', ''))) != root:
        return path, {'state': 'foreign', 'owner': owner, 'repositories': []}
    return path, {'state': 'valid', 'repositories': data['repositories']}


def cli_info(binary):
    path = shutil.which(binary) if binary else None
    if not path:
        return {'command': binary, 'path': None, 'version': None, 'consumer_init': None}
    code, out, _ = run([path, '--version'], timeout=60)
    version = out.strip().splitlines()[-1].strip() if code == 0 and out.strip() else None
    return {'command': binary, 'path': path, 'version': version,
            'consumer_init': CONSUMER_INIT.get(version)}


def registry(cli, root, sid):
    if not cli['path']:
        return {'state': 'unknown', 'reason': 'no-cli'}
    code, out, _ = run([cli['path'], 'store', 'list', '--json'], cwd=root, timeout=60)
    try:
        stores = json.loads(out)['stores'] if code == 0 else None
    except (ValueError, KeyError, TypeError):
        stores = None
    if stores is None:
        return {'state': 'unknown', 'reason': 'store-list-failed'}
    by_id = next((s for s in stores if s.get('id') == sid), None)
    by_root = next((s for s in stores if s.get('root') and Path(s['root']).resolve() == root), None)
    if by_id and Path(by_id['root']).resolve() == root:
        return {'state': 'registered'}
    if by_id:
        return {'state': 'id-conflict', 'other_root': by_id['root']}
    if by_root:
        return {'state': 'root-conflict', 'other_id': by_root.get('id')}
    return {'state': 'missing'}


def classify(info):
    reasons = []
    if remote_key(info['remote']) == MASTER:
        return 'A', ['origin es el repositorio maestro']
    template = info['template_context'] and not info['specs'] and not info['changes'] \
        and not info['catalog_entries']
    if info['id'] == TEMPLATE_ID:
        if not info['remote']:
            return 'ambiguous', ['id s0-core sin origin propio']
        if template:
            return 'B', ['remoto propio, id s0-core y contenido de plantilla']
        reasons = [name for name, flag in (('contexto propio', not info['template_context']),
                                           ('specs', info['specs']), ('changes', info['changes']),
                                           ('catálogo con entradas', info['catalog_entries'])) if flag]
        return 'ambiguous', [f'id s0-core con {r}' for r in reasons]
    if not info['id']:
        return 'ambiguous', ['sin .openspec-store/store.yaml']
    return 'C', [f'identidad propia {info["id"]}']


# --- Consumers ------------------------------------------------------------

def config_state(root, sid):
    files = [root / 'openspec' / name for name in ('config.yaml', 'config.yml')
             if (root / 'openspec' / name).exists()]
    planning = bool(entries(root / 'openspec' / 'specs') or entries(root / 'openspec' / 'changes'))
    if not files:
        return {'state': 'absent', 'store': None, 'local_planning': planning}
    if len(files) > 1:
        return {'state': 'duplicate', 'store': None, 'local_planning': planning}
    text = read_text(files[0])
    lines = [l.strip() for l in (text or '').splitlines() if l.strip() and not l.strip().startswith('#')]
    pointer = scalar(text, 'store')
    if text is None or not lines:
        return {'state': 'invalid', 'store': None, 'local_planning': planning}
    if len(lines) == 1 and pointer:
        state = 'pointer' if pointer == sid else 'other-store'
        return {'state': state, 'store': pointer, 'local_planning': planning}
    return {'state': 'own', 'store': pointer, 'local_planning': planning}


def block(sid):
    return f'{BLOCK_START}\n{BLOCK_BODY.format(id=sid)}\n{BLOCK_END}\n'


def agents_action(root, sid):
    text = read_text(root / 'AGENTS.md')
    if text is None:
        return 'create' if not (root / 'AGENTS.md').exists() else 'unreadable'
    start, end = text.find(BLOCK_START), text.find(BLOCK_END)
    if start < 0 and end < 0:
        return 'append'
    if start < 0 or end < start or text.count(BLOCK_START) > 1:
        return 'malformed'
    current = text[start:end + len(BLOCK_END)] + '\n'
    return 'keep' if current == block(sid) else 'update'


def claude_action(root):
    text = read_text(root / 'CLAUDE.md')
    if text is None:
        return 'create' if not (root / 'CLAUDE.md').exists() else 'unreadable'
    return 'keep' if re.search(r'^@(\./)?AGENTS\.md\s*$', text, re.M) else 'append'


def consumer_info(path, s0, sid, catalog):
    root = git_root(path)
    if root is None:
        return {'path': str(Path(path).resolve()), 'git_root': False}
    remote = origin(root)
    status = git(root, 'status', '--short') or ''
    item = {
        'path': str(root), 'git_root': True, 'remote': remote,
        'branch': git(root, 'branch', '--show-current'), 'head': git(root, 'rev-parse', 'HEAD'),
        'changes': len(status.splitlines()), 'config': config_state(root, sid),
        'agents': agents_action(root, sid), 'claude': claude_action(root),
        'catalog_id': next((e['id'] for e in catalog if remote_key(e.get('remote')) == remote_key(remote)
                            and remote), None),
    }
    if inside(root, s0) or inside(s0, root):
        item['excluded'] = 'contains-or-inside-s0'
    elif is_s0(root):
        item['excluded'] = 'other-s0'
    return item


def candidates(base, s0, sid, catalog):
    base = Path(base).resolve(strict=True)
    found = []
    for child in sorted(base.iterdir()):
        if child.is_dir() and not child.is_symlink() and not child.name.startswith('.') \
                and git_root(child) is not None:
            found.append(consumer_info(child, s0, sid, catalog))
    return found


# --- Integrations -----------------------------------------------------------

def codex_prompts():
    home = Path(os.environ.get('CODEX_HOME') or Path.home() / '.codex')
    return [str(home / 'prompts' / name) for name in CODEX_PROMPTS if (home / 'prompts' / name).exists()]


def run_init(cli, root, tools, **extra_env):
    """init with a temporary, empty XDG_CONFIG_HOME set to delivery both.

    The user's registry (XDG_DATA_HOME), HOME and CODEX_HOME are kept unless a
    disposable reference render overrides them through extra_env."""
    with tempfile.TemporaryDirectory(prefix='s0-openspec-config-') as config:
        env = dict(os.environ, XDG_CONFIG_HOME=config, **{k: str(v) for k, v in extra_env.items()})
        code, out, err = run([cli['path'], 'config', 'set', 'delivery', 'both'], cwd=root, env=env)
        if code == 0:
            code, out, err = run([cli['path'], *(a.format(tools=tools) for a in INIT_ARGS)],
                                 cwd=root, env=env)
    return code, (out + err).strip()[-2000:]


def reference(cli, tools):
    """Bytes this CLI generates for the integrations, rendered in a disposable repository.

    Replaces trial runs on copies: a target that exists with other bytes is a file
    init would overwrite. Registry and Codex home are temporary, so the render has
    no effect outside its own directory."""
    with tempfile.TemporaryDirectory(prefix='s0-openspec-reference-') as temp:
        repo, codex, data = (Path(temp, name) for name in ('repo', 'codex', 'data'))
        for path in (repo, codex, data):
            path.mkdir()
        run(['git', 'init', '-q', repo])
        code, output = run_init(cli, repo, tools, CODEX_HOME=codex, XDG_DATA_HOME=data)
        if code:
            raise UsageError(f'Reference init failed: {output[-300:]}')
        return {path.relative_to(repo).as_posix(): path.read_bytes()
                for base in ('.claude', '.agents') for path in sorted((repo / base).rglob('*'))
                if path.is_file()}


def init_decision(root, files):
    missing = [name for name in files if not (root / name).is_file()]
    differs = [name for name in files if (root / name).is_file() and (root / name).read_bytes() != files[name]]
    if not missing:
        return {'action': 'skip', 'reason': 'integrations-present', 'outdated': differs}
    if differs:
        return {'action': 'pending', 'reason': 'would-overwrite', 'files': differs, 'missing': len(missing)}
    return {'action': 'run', 'missing': len(missing)}


def build_plan(args):
    s0 = s0_root(args.s0)
    sid = store_id(s0)
    require(sid and ID_PATTERN.match(sid), 'The S0 has no valid identity in .openspec-store/store.yaml')
    require(not args.id or args.id == sid, f'Requested id {args.id} contradicts the S0 identity {sid}')
    tools = ','.join(sorted(set(args.tools.split(','))))
    require(set(tools.split(',')) <= {'claude', 'codex'}, 'Supported tools: claude, codex')
    cli = cli_info(args.openspec)
    catalog = parse_catalog(s0)['entries']
    reg = registry(cli, s0, sid)
    blockers = []
    if not cli['path']:
        blockers.append('no-cli')
    elif cli['consumer_init'] is not True:
        blockers.append('cli-without-consumer-init' if cli['consumer_init'] is False else 'cli-version-unchecked')
    prompts = codex_prompts() if 'codex' in tools.split(',') else []
    if prompts:
        blockers.append('codex-global-prompts')
    files = reference(cli, tools) if not blockers else None
    if reg['state'] != 'registered':
        blockers.append(f'store-{reg["state"]}')
    s0_init = init_decision(s0, files) if files else {'action': 'pending', 'reason': 'no-reference'}
    consumers = []
    for path in args.consumer:
        item = consumer_info(path, s0, sid, catalog)
        actions = {}
        if not item['git_root']:
            item['result'] = 'blocked:not-git-root'
        elif 'excluded' in item:
            item['result'] = f'blocked:{item["excluded"]}'
        elif item['config']['local_planning']:
            item['result'] = 'blocked:local-planning'
        elif item['config']['state'] not in ('absent', 'pointer'):
            item['result'] = f'blocked:config-{item["config"]["state"]}'
        elif item['agents'] in ('malformed', 'unreadable') or item['claude'] == 'unreadable':
            item['result'] = 'blocked:instructions-unreadable'
        else:
            actions['pointer'] = 'create' if item['config']['state'] == 'absent' else 'keep'
            actions['init'] = init_decision(Path(item['path']), files) if files else \
                {'action': 'pending', 'reason': blockers[0] if blockers else 'no-reference'}
            actions['agents'], actions['claude'] = item['agents'], item['claude']
            pending = actions['init']['action'] == 'pending' or blockers
            item['result'] = 'pending' if pending else 'ready'
        item['actions'] = actions
        consumers.append(item)
    return {'s0': {'root': str(s0), 'id': sid}, 'tools': tools, 'cli': cli, 'registry': reg,
            'blockers': blockers, 'codex_prompts': prompts, 's0_integrations': s0_init,
            'consumers': consumers}


def resolves_to(cli, root, s0):
    code, out, _ = run([cli['path'], 'context', '--json'], cwd=root, timeout=60)
    try:
        return code == 0 and Path(json.loads(out)['root']['path']).resolve() == s0
    except (ValueError, KeyError, TypeError):
        return False


def apply_instructions(root, sid, actions):
    agents = root / 'AGENTS.md'
    if actions['agents'] == 'create':
        write_atomic(agents, block(sid))
    elif actions['agents'] == 'append':
        text = read_text(agents)
        write_atomic(agents, text + ('\n' if text and not text.endswith('\n') else '')
                     + ('\n' if text.strip() else '') + block(sid))
    elif actions['agents'] == 'update':
        text = read_text(agents)
        start, end = text.find(BLOCK_START), text.find(BLOCK_END) + len(BLOCK_END)
        end += 1 if text[end:end + 1] == '\n' else 0
        write_atomic(agents, text[:start] + block(sid) + text[end:])
    claude = root / 'CLAUDE.md'
    if actions['claude'] == 'create':
        write_atomic(claude, '@AGENTS.md\n')
    elif actions['claude'] == 'append':
        text = read_text(claude)
        write_atomic(claude, '@AGENTS.md\n\n' + text)


def apply_consumers(args):
    plan = build_plan(args)
    s0, sid = Path(plan['s0']['root']), plan['s0']['id']
    if args.s0_integrations and plan['s0_integrations']['action'] == 'run':
        code, output = run_init(plan['cli'], s0, plan['tools'])
        plan['s0_integrations'].update(applied=code == 0, output=None if code == 0 else output)
    for item in plan['consumers']:
        if item['result'] != 'ready':
            continue
        root, actions, done = Path(item['path']), item['actions'], []
        if actions['pointer'] == 'create':
            write_atomic(root / 'openspec' / 'config.yaml', f'store: {sid}\n')
            done.append('pointer')
        if actions['init']['action'] == 'run':
            code, output = run_init(plan['cli'], root, plan['tools'])
            if code:
                item.update(result='pending:init-failed', output=output, done=done)
                continue
            done.append('init')
        if not resolves_to(plan['cli'], root, s0):
            item.update(result='pending:context-not-resolved', done=done)
            continue
        apply_instructions(root, sid, actions)
        done += [name for name in ('agents', 'claude') if actions[name] not in ('keep',)]
        item.update(result='connected', done=done)
    return plan, all(item['result'] == 'connected' for item in plan['consumers'])


# --- Locator and catalog -----------------------------------------------------

def write_locator(args):
    s0 = s0_root(args.s0)
    sid = store_id(s0)
    require(sid, 'The S0 has no identity in .openspec-store/store.yaml')
    path, current = read_locator(s0, sid)
    require(current['state'] in ('absent', 'valid'),
            f'Locator {current["state"]}: kept unchanged, review it by hand ({path})')
    merged = {str(Path(e['path'])): e for e in current['repositories']}
    accepted, rejected = [], []
    for value in args.source:
        root = git_root(value)
        if root is None:
            rejected.append({'path': value, 'reason': 'not-git-root'})
        elif inside(root, s0) or inside(s0, root) or is_s0(root):
            rejected.append({'path': str(root), 'reason': 's0-root'})
        else:
            entry = {'path': str(root), 'remote': origin(root)}
            accepted.append(entry)
            merged[entry['path']] = entry
    data = {'version': 1, 's0': {'id': sid, 'root': str(s0)}, 'repositories': list(merged.values())}
    changed = bool(merged) and (current['state'] == 'absent' or merged != {str(Path(e['path'])): e
                                                                          for e in current['repositories']})
    if changed:
        write_atomic(path, json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    return {'path': str(path), 'written': changed, 'accepted': accepted, 'rejected': rejected}, not rejected


def default_branch(url):
    code, out, _ = run(['git', 'ls-remote', '--symref', '--', url, 'HEAD'], timeout=60)
    match = re.search(r'^ref: refs/heads/(\S+)\s+HEAD$', out, re.M) if code == 0 else None
    return match.group(1) if match else None


def write_catalog(args):
    s0 = s0_root(args.s0)
    path = s0 / 'repositories.yaml'
    catalog = parse_catalog(s0)
    require(catalog['present'] and catalog['valid'], 'repositories.yaml is missing or not in the known format')
    branches = dict(args.branch or [])
    requested = []
    for rid, url in args.entry:
        require(ID_PATTERN.match(rid), f'Invalid catalog id: {rid}')
        require(clean_url(url) == url and not re.match(r'^(file:|/|\.)', url),
                f'Catalog remotes are HTTPS/SSH URLs without credentials: {rid}')
        requested.append((rid, url))
    existing = {e['id']: e for e in catalog['entries']}
    keys = {remote_key(e['remote']): e['id'] for e in catalog['entries']}
    added, kept, conflicts = [], [], []
    todo = []
    for rid, url in requested:
        if rid in existing:
            (kept if remote_key(existing[rid]['remote']) == remote_key(url) else conflicts).append(rid)
        elif remote_key(url) in keys:
            conflicts.append(rid)
        else:
            todo.append((rid, url))
            keys[remote_key(url)] = rid
    with ThreadPoolExecutor(max_workers=8) as pool:
        found = list(pool.map(lambda pair: branches.get(pair[0]) or default_branch(pair[1]), todo))
    lines = []
    for (rid, url), branch in zip(todo, found):
        lines += [f'  - id: {rid}', f'    remote: {url}'] + ([f'    branch: {branch}'] if branch else [])
        added.append({'id': rid, 'remote': url, 'branch': branch})
    if lines:
        text = read_text(path)
        if re.search(r'^repositories:\s*\[\s*\]\s*$', text, re.M):
            text = re.sub(r'^repositories:\s*\[\s*\]\s*$', 'repositories:\n' + '\n'.join(lines), text,
                          count=1, flags=re.M)
        else:
            all_lines = text.splitlines()
            start = next(i for i, l in enumerate(all_lines) if l.startswith('repositories:'))
            end = next((i for i in range(start + 1, len(all_lines))
                        if re.match(r'^\S', all_lines[i]) and not all_lines[i].startswith('#')), len(all_lines))
            while end > start + 1 and not all_lines[end - 1].strip():
                end -= 1
            all_lines[end:end] = lines
            text = '\n'.join(all_lines)
        write_atomic(path, text if text.endswith('\n') else text + '\n')
    return {'path': str(path), 'added': added, 'kept': kept, 'conflicts': conflicts,
            'without_branch': [a['id'] for a in added if not a['branch']]}, not conflicts


# --- Verification ------------------------------------------------------------

def expected_files(tools):
    files = []
    for tool in tools.split(','):
        files += [f'.claude/skills/openspec-{w}/SKILL.md' for w in CORE_WORKFLOWS] if tool == 'claude' else []
        files += [f'.claude/commands/opsx/{w.split("-")[0]}.md' for w in CORE_WORKFLOWS] if tool == 'claude' else []
        files += [f'.agents/skills/openspec-{w}/SKILL.md' for w in CORE_WORKFLOWS] if tool == 'codex' else []
    return files


def verify(args):
    s0 = s0_root(args.s0)
    sid = store_id(s0)
    cli = cli_info(args.openspec)
    require(cli['path'], f'OpenSpec CLI not found: {args.openspec}')
    tools = ','.join(sorted(set(args.tools.split(','))))
    checks = {}
    code, out, err = run([cli['path'], 'store', 'doctor', sid], cwd=s0)
    checks['store_doctor'] = {'ok': code == 0, 'output': (out + err).strip()[-1500:]}
    code, _, err = run([cli['path'], 'status', '--all', '--store', sid], cwd=s0)
    checks['store_status'] = {'ok': code == 0, 'error': err.strip()[-500:] or None}
    checks['s0_diff_check'] = {'ok': git(s0, 'diff', '--check') is not None}
    consumers = []
    for value in args.consumer:
        root = git_root(value)
        if root is None:
            consumers.append({'path': value, 'ok': False, 'reason': 'not-git-root'})
            continue
        code, _, _ = run([cli['path'], 'status', '--all'], cwd=root)
        item = {
            'path': str(root),
            'context_resolves': resolves_to(cli, root, s0),
            'status_ok': code == 0,
            'pointer': config_state(root, sid)['state'] == 'pointer',
            'no_local_planning': not config_state(root, sid)['local_planning'],
            'agents_block': agents_action(root, sid) == 'keep',
            'claude_import': claude_action(root) == 'keep',
            'missing_integrations': [f for f in expected_files(tools) if not (root / f).is_file()],
            'diff_check': git(root, 'diff', '--check') is not None,
            'changes': (git(root, 'status', '--short') or '').splitlines(),
        }
        item['ok'] = all(item[k] for k in ('context_resolves', 'status_ok', 'pointer', 'no_local_planning',
                                           'agents_block', 'claude_import', 'diff_check')) \
            and not item['missing_integrations']
        consumers.append(item)
    ok = all(c['ok'] for c in checks.values()) and all(c['ok'] for c in consumers)
    return {'s0': {'root': str(s0), 'id': sid}, 'cli': cli, 'checks': checks, 'consumers': consumers}, ok


# --- Diagnose ----------------------------------------------------------------

def diagnose(args):
    s0 = s0_root(args.s0)
    sid = store_id(s0)
    catalog = parse_catalog(s0)
    context = read_text(s0 / 'context' / 'project.md') or ''
    info = {
        'root': str(s0), 'remote': origin(s0), 'branch': git(s0, 'branch', '--show-current'),
        'head': git(s0, 'rev-parse', 'HEAD'), 'changes': (git(s0, 'status', '--short') or '').splitlines(),
        'id': sid, 'template_context': context.lstrip().startswith(TEMPLATE_HEADING),
        'specs': entries(s0 / 'openspec' / 'specs'),
        'changes_active': [n for n in entries(s0 / 'openspec' / 'changes') if n != 'archive'],
        'archived': entries(s0 / 'openspec' / 'changes' / 'archive'),
        'sources_root': git(s0, 'config', '--local', '--get', 's0.sourcesRoot'),
    }
    state, reasons = classify({**info, 'changes': info['changes_active'] or info['archived'],
                               'catalog_entries': catalog['entries']})
    clis = [cli_info(b) for b in dict.fromkeys(filter(None, [args.openspec, 'openspec']))]
    working = next((c for c in clis if c['path']), {'path': None})
    try:
        _, locator = read_locator(s0, sid)
    except UsageError as error:
        locator = {'state': 'unsafe', 'reason': str(error), 'repositories': []}
    found = candidates(args.base, s0, sid, catalog['entries']) if args.base else []
    found += [consumer_info(p, s0, sid, catalog['entries']) for p in args.source]
    return {'state': state, 'reasons': reasons, 's0': info, 'catalog': catalog,
            'registry': registry(working, s0, sid) if sid else {'state': 'unknown', 'reason': 'no-id'},
            'locator': locator, 'cli': clis, 'codex_prompts': codex_prompts(),
            'candidates': found}, True


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest='command', required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument('--s0', default='.', help='S0 Git root (default: current directory)')
    common.add_argument('--openspec', default='openspec', help='OpenSpec executable for this operation')
    consumers = argparse.ArgumentParser(add_help=False)
    consumers.add_argument('--consumer', action='append', default=[], help='Consumer Git root (repeatable)')
    consumers.add_argument('--tools', default='claude,codex')
    consumers.add_argument('--id', help='Expected S0 id; must match the adopted identity')

    item = sub.add_parser('diagnose', parents=[common], help='Read-only state A/B/C/ambiguous with evidence')
    item.add_argument('--base', help='Folder whose child Git roots are candidate sources')
    item.add_argument('--source', action='append', default=[], help='Explicit source root (repeatable)')
    sub.add_parser('plan', parents=[common, consumers], help='Per-root actions and conflicts, no writes')
    item = sub.add_parser('apply-consumers', parents=[common, consumers], help='Apply the ready part of the plan')
    item.add_argument('--s0-integrations', action='store_true', help='Also generate missing S0 integrations')
    item = sub.add_parser('write-locator', parents=[common], help='Merge verified local sources')
    item.add_argument('--source', action='append', required=True)
    item = sub.add_parser('write-catalog', parents=[common], help='Add entries to repositories.yaml')
    item.add_argument('--entry', nargs=2, action='append', required=True, metavar=('ID', 'URL'))
    item.add_argument('--branch', nargs=2, action='append', metavar=('ID', 'BRANCH'),
                      help='Known branch; skips the git ls-remote lookup for that id')
    sub.add_parser('verify', parents=[common, consumers], help='store doctor, status, context and diff checks')

    args = parser.parse_args(argv)
    try:
        if args.command == 'diagnose':
            result, ok = diagnose(args)
        elif args.command == 'plan':
            result = build_plan(args)
            ok = not result['blockers'] and all(c['result'] == 'ready' for c in result['consumers'])
        elif args.command == 'apply-consumers':
            result, ok = apply_consumers(args)
        elif args.command == 'write-locator':
            result, ok = write_locator(args)
        elif args.command == 'write-catalog':
            result, ok = write_catalog(args)
        else:
            result, ok = verify(args)
    except UsageError as error:
        print(json.dumps({'error': str(error)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
"""Compare a discovery worktree with an external, immutable-by-convention baseline.

Python >=3.10 and Git. No writes to repositories, Git mutations, rollback, or
approval inference. Pass exact context paths only after the user approves them.
S0 includes ignored files; code includes tracked and nonignored untracked files.
Ignored untracked code is outside coverage; submodules need separate Git roots.
File hashes cover bytes plus permission mode reported by the platform (Windows
does not expose POSIX executable permissions). Nested .git entries fail closed.
This is a before/after check, not a sandbox: transient/concurrent reverted edits
and baseline tampering are outside its guarantees. JSON stores hashes, not text.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys


class ScopeError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise ScopeError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def is_link(path):
    info = path.lstat()
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, 'st_file_attributes', 0) & 0x400)


def git(root, *args, optional=False):
    env = {key: value for key, value in os.environ.items()
           if not key.startswith(('GIT_', 'GIT_CONFIG_'))}
    env.update(GIT_OPTIONAL_LOCKS='0', GIT_NO_LAZY_FETCH='1')
    result = subprocess.run(
        ['git', '--no-optional-locks', '-c', 'core.fsmonitor=false',
         '-c', 'core.untrackedCache=false', '-C', str(root), *args],
        capture_output=True, env=env, check=False)
    if result.returncode and not optional:
        raise ScopeError(f'Git command failed: {args[0]} (exit {result.returncode})')
    return result.stdout if not result.returncode else b''


def git_root(value):
    root = Path(value).resolve(strict=True)
    require(root.is_dir(), 'Repository root must be a directory')
    actual = Path(os.fsdecode(git(root, 'rev-parse', '--show-toplevel')).strip()).resolve()
    require(root == actual, 'Pass the Git root, not a repository subdirectory')
    return root


def inside(path, root):
    return path == root or root in path.parents


def relative_name(value):
    require(isinstance(value, str) and value and '\\' not in value,
            'Paths must be nonempty relative POSIX paths')
    parts = value.split('/')
    require(not PurePosixPath(value).is_absolute() and all(part not in ('', '.', '..') for part in parts),
            'Absolute paths and dot components are forbidden')
    require(all(part.casefold() != '.git' for part in parts), 'Git metadata paths are forbidden')
    require(all(not re.search(r'[<>:"|?*\x00-\x1f]', part) and not part.endswith((' ', '.'))
                and not re.search(r'~[0-9]', part)
                and part.split('.')[0].upper() not in
                {'CON', 'PRN', 'AUX', 'NUL', *(f'COM{i}' for i in range(1, 10)),
                 *(f'LPT{i}' for i in range(1, 10))} for part in parts),
            'Unsafe or aliased filename')
    return parts


def file_state(root, name):
    parts = relative_name(name)
    current = root
    for part in parts[:-1]:
        current = current / part
        if current.exists() or current.is_symlink():
            if is_link(current):
                return ['blocked-parent', digest(os.fsencode(os.readlink(current)))]
    path = root.joinpath(*parts)
    try:
        info = path.lstat()
    except FileNotFoundError:
        return None
    if is_link(path):
        return ['link', digest(os.fsencode(os.readlink(path)))]
    if stat.S_ISDIR(info.st_mode):
        return ['directory', None]
    require(stat.S_ISREG(info.st_mode), 'Unsupported special file in worktree')
    sha = hashlib.sha256(f'mode:{stat.S_IMODE(info.st_mode):o}\0'.encode('ascii'))
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            sha.update(chunk)
    return ['file', sha.hexdigest()]


def git_state(root):
    # Semantic index: object/mode/stage and assume-unchanged/skip-worktree flags.
    # Reading status may refresh raw index stat-cache without staging anything.
    index = git(root, 'ls-files', '--stage', '-z') + b'\0' + git(root, 'ls-files', '-v', '-z')
    return {
        'head': git(root, 'rev-parse', '--verify', '--quiet', 'HEAD', optional=True).decode().strip() or None,
        'ref': git(root, 'symbolic-ref', '-q', 'HEAD', optional=True).decode().strip() or None,
        'index': digest(index),
    }


def capture(root, role):
    before = git_state(root)
    files = {}
    if role == 's0':
        def visit(folder):
            for entry in sorted(os.scandir(folder), key=lambda item: item.name):
                if folder == root and entry.name == '.git':
                    continue
                name = Path(entry.path).relative_to(root).as_posix()
                state = file_state(root, name)
                require(state is not None, 'Worktree changed during capture; retry')
                files[name] = state
                if state[0] == 'directory':
                    visit(Path(entry.path))
        visit(root)
    else:
        names = git(root, 'ls-files', '--cached', '--others', '--exclude-standard', '-z')
        for name in sorted(set(os.fsdecode(item) for item in names.split(b'\0') if item)):
            state = file_state(root, name)
            if state is not None:
                files[name] = state
    require(len({name.casefold() for name in files}) == len(files), 'Case-aliased file paths')
    require(before == git_state(root), 'HEAD or index changed during capture; retry from a stable state')
    return {'path': str(root), 'role': role, 'git': before, 'files': files}


def external(path, roots):
    path = Path(path).resolve()
    require(all(not inside(path, root) for root in roots), 'Snapshot must be outside every repository')
    return path


def roots_check(roots):
    require(roots and all(not inside(a, b) and not inside(b, a)
                         for i, a in enumerate(roots) for b in roots[i + 1:]),
            'Repository roots must be unique and nonoverlapping')


def snapshot(args):
    roots = [git_root(args.s0), *(git_root(value) for value in args.repo)]
    roots_check(roots)
    raw_output = Path(args.output)
    require(not (os.path.lexists(raw_output) and is_link(raw_output)), 'Snapshot output cannot be a link')
    output = external(raw_output, roots)
    require(output.parent.is_dir(), 'Snapshot parent directory must already exist')
    states = [capture(root, 's0' if i == 0 else 'code') for i, root in enumerate(roots)]
    with output.open('x', encoding='utf-8') as target:
        json.dump({'version': 1, 'roots': states}, target, ensure_ascii=True, indent=2)
        target.write('\n')
    return {'ok': True, 'snapshot': str(output), 'repositories': len(roots)}, 0


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'Duplicate JSON key')
        result[key] = value
    return result


def load_snapshot(path):
    require(not is_link(Path(path)), 'Snapshot must be an ordinary file')
    with Path(path).open(encoding='utf-8') as source:
        data = json.load(source, object_pairs_hook=unique_object)
    require(isinstance(data, dict) and set(data) == {'version', 'roots'}
            and type(data['version']) is int and data['version'] == 1
            and isinstance(data['roots'], list) and data['roots'], 'Invalid snapshot schema')
    roots = []
    for i, state in enumerate(data['roots']):
        require(isinstance(state, dict) and set(state) == {'path', 'role', 'git', 'files'}, 'Invalid root schema')
        require(state['role'] == ('s0' if i == 0 else 'code')
                and isinstance(state['path'], str) and Path(state['path']).is_absolute(), 'Invalid root identity')
        root = git_root(state['path'])
        require(str(root) == state['path'], 'Snapshot root must be canonical')
        roots.append(root)
        info = state['git']
        require(isinstance(info, dict) and set(info) == {'head', 'ref', 'index'}, 'Invalid Git schema')
        require(isinstance(info['index'], str) and re.fullmatch('[0-9a-f]{64}', info['index']), 'Invalid index hash')
        require(info['head'] is None or isinstance(info['head'], str)
                and re.fullmatch('[0-9a-f]{40}|[0-9a-f]{64}', info['head']), 'Invalid HEAD')
        require(info['ref'] is None or isinstance(info['ref'], str)
                and info['ref'].startswith('refs/') and not re.search(r'[\x00-\x20]', info['ref']), 'Invalid HEAD ref')
        require(isinstance(state['files'], dict), 'Invalid files schema')
        folded = set()
        for name, entry in state['files'].items():
            relative_name(name)
            require(name.casefold() not in folded, 'Case-aliased file paths')
            folded.add(name.casefold())
            require(isinstance(entry, list) and len(entry) == 2 and entry[0] in
                    ('file', 'directory', 'link', 'blocked-parent'), 'Invalid file entry')
            require(entry[1] is None if entry[0] == 'directory' else
                    isinstance(entry[1], str) and re.fullmatch('[0-9a-f]{64}', entry[1]), 'Invalid file hash')
    roots_check(roots)
    external(path, roots)
    return data


def allowed_context(root, name, baseline):
    parts = relative_name(name)
    require(parts[0] == 'context' and len(parts) >= 2
            and parts[-1].endswith('.md') and len(parts[-1]) > 3, 'Only exact context Markdown paths may be allowed')
    require(baseline.get(name, ['file'])[0] == 'file', 'Cannot allow a baseline link or directory')
    current = root
    for i, part in enumerate(parts):
        if current.is_dir():
            matches = [item for item in os.listdir(current) if item.casefold() == part.casefold()]
            require(not matches or matches == [part], 'Case-aliased context path')
        current = current / part
        if current.exists() or current.is_symlink():
            require(not is_link(current), 'Context path contains a symlink or junction')
            info = current.stat()
            require(i < len(parts) - 1 and stat.S_ISDIR(info.st_mode)
                    or i == len(parts) - 1 and stat.S_ISREG(info.st_mode) and info.st_nlink == 1,
                    'Context target must be a regular file without hardlink aliases')
    require(inside(current.resolve(), root), 'Context target escapes S0')


def verify(args):
    data = load_snapshot(args.snapshot)
    s0 = Path(data['roots'][0]['path'])
    allowed = set(args.allow_context)
    for name in allowed:
        allowed_context(s0, name, data['roots'][0]['files'])
    parents = {str(parent) for name in allowed for parent in PurePosixPath(name).parents if str(parent) != '.'}
    violations = []
    for baseline in data['roots']:
        current = capture(Path(baseline['path']), baseline['role'])
        for key in baseline['git']:
            if baseline['git'][key] != current['git'][key]:
                violations.append({'root': baseline['path'], 'path': f'.git/{key}', 'change': 'git-state'})
        for name in sorted(baseline['files'].keys() | current['files'].keys()):
            old, new = baseline['files'].get(name), current['files'].get(name)
            if old == new:
                continue
            if baseline['role'] == 's0' and (name in allowed or
                    name in parents and old is None and new == ['directory', None]):
                continue
            violations.append({'root': baseline['path'], 'path': name,
                               'change': 'added' if old is None else 'deleted' if new is None else 'modified'})
    return {'ok': not violations, 'violations': violations}, 1 if violations else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    before = commands.add_parser('snapshot')
    before.add_argument('--s0', required=True)
    before.add_argument('--repo', action='append', default=[])
    before.add_argument('--output', required=True)
    after = commands.add_parser('verify')
    after.add_argument('--snapshot', required=True)
    after.add_argument('--allow-context', action='append', default=[])
    args = parser.parse_args()
    try:
        result, code = snapshot(args) if args.command == 'snapshot' else verify(args)
    except (ScopeError, OSError, UnicodeError, json.JSONDecodeError, RecursionError) as error:
        result, code = {'ok': False, 'error': str(error)}, 2
    print(json.dumps(result, ensure_ascii=True))
    return code


if __name__ == '__main__':
    sys.exit(main())

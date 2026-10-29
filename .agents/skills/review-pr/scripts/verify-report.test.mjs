import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdirSync, mkdtempSync, readFileSync, rmSync, truncateSync, writeFileSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';
import { changedLines, verifyReport } from './verify-report.mjs';

const verifierPath = fileURLToPath(new URL('./verify-report.mjs', import.meta.url));

const diff = [
  'diff --git a/internal/money.go b/internal/money.go',
  '--- a/internal/money.go',
  '+++ b/internal/money.go',
  '@@ -10,2 +10,2 @@',
  ' func price() string {',
  '- return "1.00"',
  '+ return "2.00"',
  '',
].join('\n');

function fixture() {
  const input = { repository: 'example/review-fixture', number: 7, headOid: 'a'.repeat(40), files: [{ path: 'internal/money.go' }], diff };
  const report = { repository: input.repository, number: input.number, headOid: input.headOid, comments: [{ path: 'internal/money.go', line: 11, side: 'RIGHT', body: 'The changed value violates the declared fixture contract.', evidence: 'return "2.00"' }] };
  return { input, report };
}

test('verifies identity, actual changed line, and literal evidence', () => {
  const { input, report } = fixture();
  const result = verifyReport(input, report);
  assert.equal(result.ok, true);
  assert.equal(result.comments, 1);
  assert.match(result.diffSha256, /^[a-f0-9]{64}$/);
});

test('rejects wrong PR identity or head', () => {
  for (const [key, value] of [['repository', 'example/other'], ['number', 8], ['headOid', 'b'.repeat(40)]]) {
    const { input, report } = fixture();
    report[key] = value;
    assert.equal(verifyReport(input, report).ok, false);
  }
});

test('rejects invalid captured identities even when the report matches them', () => {
  for (const [key, value] of [['repository', 'review-fixture'], ['number', 0], ['number', 2 ** 53], ['headOid', 'abcdef']]) {
    const { input, report } = fixture();
    input[key] = value;
    report[key] = value;
    assert.equal(verifyReport(input, report).ok, false);
  }
});

test('rejects wrong file, unchanged line, wrong side, or borrowed evidence', () => {
  for (const mutation of [
    { path: 'other.go' }, { line: 10 }, { side: 'LEFT' }, { evidence: 'func price() string {' }, { evidence: 'invented' },
  ]) {
    const { input, report } = fixture();
    Object.assign(report.comments[0], mutation);
    assert.equal(verifyReport(input, report).ok, false);
  }
});

test('rejects evidence copied from a changed line in another captured file', () => {
  const { input, report } = fixture();
  input.files.push({ path: 'internal/other.go' });
  input.diff += [
    'diff --git a/internal/other.go b/internal/other.go',
    '--- /dev/null', '+++ b/internal/other.go',
    '@@ -0,0 +1 @@', '+const borrowed = true', '',
  ].join('\n');
  report.comments[0].evidence = 'const borrowed = true';
  const result = verifyReport(input, report);
  assert.equal(result.ok, false);
  assert.ok(result.errors.some((error) => error.includes('evidence is not literal')));
});

test('supports deleted lines with LEFT and rejects duplicate comments', () => {
  const { input, report } = fixture();
  report.comments[0].side = 'LEFT';
  report.comments[0].evidence = 'return "1.00"';
  assert.equal(verifyReport(input, report).ok, true);
  report.comments.push({ ...report.comments[0] });
  assert.equal(verifyReport(input, report).ok, false);
});

test('supports renamed paths, spaces, Unicode quoting and header-like source lines', () => {
  const localDiff = [
    'diff --git "a/old name.go" "b/nuam \\303\\261.go"',
    '--- "a/old name.go"', '+++ "b/nuam \\303\\261.go"',
    '@@ -1 +1 @@', '--- old value', '+++ new value', '',
  ].join('\n');
  const parsed = changedLines(localDiff);
  assert.deepEqual(parsed.errors, []);
  assert.equal(parsed.lines.get(JSON.stringify(['nuam ñ.go', 'RIGHT', 1])), '++ new value');
  assert.equal(parsed.lines.get(JSON.stringify(['nuam ñ.go', 'LEFT', 1])), '-- old value');
  const { input, report } = fixture();
  input.diff = localDiff;
  input.files = [{ path: 'nuam ñ.go' }];
  report.comments = ['LEFT', 'RIGHT'].map((side) => ({
    path: 'nuam ñ.go', side, line: 1, body: 'Check this changed value.',
    evidence: side === 'LEFT' ? '-- old value' : '++ new value',
  }));
  assert.equal(verifyReport(input, report).ok, true);
});

test('supports deleted files and multiple hunks', () => {
  const localDiff = [
    'diff --git a/deleted.go b/deleted.go', '--- a/deleted.go', '+++ /dev/null',
    '@@ -1 +0,0 @@', '-package deleted',
    'diff --git a/added.go b/added.go', '--- /dev/null', '+++ b/added.go',
    '@@ -0,0 +1 @@', '+package added', '',
  ].join('\n');
  const parsed = changedLines(localDiff);
  assert.deepEqual(parsed.errors, []);
  assert.equal(parsed.lines.get(JSON.stringify(['deleted.go', 'LEFT', 1])), 'package deleted');
  assert.equal(parsed.lines.get(JSON.stringify(['added.go', 'RIGHT', 1])), 'package added');
  const { input, report } = fixture();
  input.diff = localDiff;
  input.files = [{ path: 'deleted.go' }, { path: 'added.go' }];
  report.comments = [{ path: 'deleted.go', side: 'LEFT', line: 1, body: 'This removal breaks its caller.', evidence: 'package deleted' }];
  assert.equal(verifyReport(input, report).ok, true);
});

test('supports multiple hunks, CRLF transport and no-newline markers', () => {
  const { input, report } = fixture();
  input.diff += ['@@ -20 +20 @@', '-old', '\\ No newline at end of file', '+new', '\\ No newline at end of file', ''].join('\n');
  input.diff = input.diff.replaceAll('\n', '\r\n');
  report.comments.push({ path: 'internal/money.go', line: 20, side: 'RIGHT', body: 'Check the second change.', evidence: 'new' });
  assert.equal(verifyReport(input, report).ok, true);
});

test('rejects truncated diffs and invalid report shapes but allows no findings', () => {
  const { input, report } = fixture();
  report.comments = [];
  assert.equal(verifyReport(input, report).ok, true);
  input.diff = diff.replace('+ return "2.00"\n', '');
  assert.equal(verifyReport(input, report).ok, false);
  assert.equal(verifyReport(null, report).ok, false);
  input.files = [{ path: '../outside.go' }];
  assert.equal(verifyReport(input, report).ok, false);
});

test('rejects incomplete middle hunks, missing headers and malformed hunk headers', () => {
  for (const invalidDiff of [
    diff.replace('+ return "2.00"\n', 'diff --git a/next.go b/next.go\n'),
    diff.replace('+++ b/internal/money.go\n', ''),
    diff.replace('@@ -10,2 +10,2 @@', '@@ not a hunk @@'),
    'diff --git a/file.go b/file.go\n--- a/file.go\n',
  ]) {
    const { input, report } = fixture();
    input.diff = invalidDiff;
    report.comments = [];
    assert.equal(verifyReport(input, report).ok, false, invalidDiff);
  }
});

test('rejects extra hunk lines instead of silently accepting an incomplete capture', () => {
  for (const extra of ['+extra', '-extra', ' extra', '+++ header-like extra', '--- header-like extra']) {
    const { input, report } = fixture();
    input.diff += `${extra}\n`;
    assert.equal(verifyReport(input, report).ok, false, extra);
  }
});

test('rejects repeated changed locations and invalid numeric hunk ranges', () => {
  for (const invalidDiff of [
    diff + diff,
    diff.replace('@@ -10,2 +10,2 @@', '@@ -0,2 +0,2 @@'),
    diff.replace('@@ -10,2 +10,2 @@', '@@ -9007199254740992,2 +10,2 @@'),
  ]) {
    const { input, report } = fixture();
    input.diff = invalidDiff;
    report.comments = [];
    assert.equal(verifyReport(input, report).ok, false);
  }
});

test('rejects unsafe or noncanonical captured paths and unsafe diff paths', () => {
  for (const unsafe of ['../outside.go', '/outside.go', 'C:/outside.go', 'internal\\money.go', './internal/money.go', 'internal//money.go', 'internal/money.go/', 'bad\0.go']) {
    const { input, report } = fixture();
    input.files = [{ path: unsafe }];
    report.comments = [];
    assert.equal(verifyReport(input, report).ok, false, unsafe);
  }
  const { input, report } = fixture();
  input.diff = diff.replaceAll('a/internal/money.go', 'a/../outside.go');
  report.comments = [];
  assert.equal(verifyReport(input, report).ok, false);
});

test('rejects invalid comment shapes, blank bodies, blank evidence and invalid line numbers', () => {
  for (const comment of [null, [], 'text', { body: ' ' }, { evidence: ' ' }, { line: 0 }, { line: 1.5 }, { line: 2 ** 53 }]) {
    const { input, report } = fixture();
    report.comments = [comment && !Array.isArray(comment) && typeof comment === 'object' ? { ...report.comments[0], ...comment } : comment];
    assert.equal(verifyReport(input, report).ok, false);
  }
});

function cliFixture(t) {
  const temp = mkdtempSync(path.join(os.tmpdir(), 's0 review '));
  t.after(() => rmSync(temp, { recursive: true, force: true }));
  const cwd = path.join(temp, 'unrelated working directory');
  mkdirSync(cwd);
  const { input, report } = fixture();
  const inputPath = path.join(temp, 'captured input.json');
  const reportPath = path.join(temp, 'review report.json');
  writeFileSync(inputPath, JSON.stringify(input));
  writeFileSync(reportPath, JSON.stringify(report));
  return {
    input, report, inputPath, reportPath, cwd,
    run: (args = [inputPath, reportPath]) => spawnSync(process.execPath, [verifierPath, ...args], { cwd, encoding: 'utf8', windowsHide: true }),
  };
}

test('CLI runs from an unrelated CWD with absolute or relative paths containing spaces and preserves files', (t) => {
  const files = cliFixture(t);
  const before = [readFileSync(files.inputPath), readFileSync(files.reportPath)];
  for (const args of [[files.inputPath, files.reportPath], [path.relative(files.cwd, files.inputPath), path.relative(files.cwd, files.reportPath)]]) {
    const result = files.run(args);
    assert.equal(result.error, undefined);
    assert.equal(result.status, 0, result.stderr);
    assert.equal(result.stderr, '');
    assert.deepEqual(JSON.parse(result.stdout), verifyReport(files.input, files.report));
  }
  assert.deepEqual([readFileSync(files.inputPath), readFileSync(files.reportPath)], before);
});

test('CLI returns JSON and exit status 1 for a mismatched identity', (t) => {
  const files = cliFixture(t);
  files.report.headOid = 'b'.repeat(40);
  writeFileSync(files.reportPath, JSON.stringify(files.report));
  const result = files.run();
  assert.equal(result.status, 1);
  assert.equal(result.stderr, '');
  assert.equal(JSON.parse(result.stdout).ok, false);
});

test('CLI accepts UTF-8 BOM artifacts and a valid empty findings list', (t) => {
  const files = cliFixture(t);
  files.report.comments = [];
  writeFileSync(files.inputPath, `\uFEFF${JSON.stringify(files.input)}`);
  writeFileSync(files.reportPath, `\uFEFF${JSON.stringify(files.report)}`);
  const result = files.run();
  assert.equal(result.status, 0, result.stderr);
  assert.equal(JSON.parse(result.stdout).comments, 0);
});

test('CLI rejects unreadable, malformed and oversized artifacts without logging their contents', (t) => {
  const files = cliFixture(t);
  for (const prepare of [
    () => rmSync(files.inputPath),
    () => writeFileSync(files.inputPath, 'private fixture content: not valid JSON'),
    () => truncateSync(files.inputPath, 32 * 1024 * 1024 + 1),
  ]) {
    prepare();
    const result = files.run();
    assert.equal(result.status, 1);
    assert.equal(result.stdout, '');
    assert.match(result.stderr, /^Review artifacts could not be read or parsed\./);
    assert.ok(!result.stderr.includes('private fixture content'));
  }
});

test('CLI rejects missing arguments with usage on stderr', (t) => {
  const result = cliFixture(t).run([]);
  assert.equal(result.status, 1);
  assert.equal(result.stdout, '');
  assert.match(result.stderr, /^Usage: node verify-report\.mjs/);
});

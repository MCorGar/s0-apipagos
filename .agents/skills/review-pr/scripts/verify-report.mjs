import { createHash } from 'node:crypto';
import { readFileSync, statSync } from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

function decodePath(value) {
  let decoded = value.split('\t')[0];
  if (decoded.startsWith('"') && decoded.endsWith('"')) {
    const bytes = [];
    const body = decoded.slice(1, -1);
    for (let index = 0; index < body.length; index += 1) {
      if (body[index] !== '\\') {
        const point = body.codePointAt(index);
        bytes.push(...Buffer.from(String.fromCodePoint(point)));
        if (point > 0xffff) {
          index += 1;
        }
        continue;
      }
      const octal = body.slice(index + 1).match(/^[0-7]{1,3}/);
      if (octal) {
        bytes.push(Number.parseInt(octal[0], 8));
        index += octal[0].length;
        continue;
      }
      index += 1;
      const escaped = { t: '\t', n: '\n', r: '\r', b: '\b', f: '\f', v: '\v', a: '\x07' }[body[index]] ?? body[index];
      bytes.push(...Buffer.from(escaped ?? ''));
    }
    decoded = Buffer.from(bytes).toString('utf8');
  }
  if (decoded === '/dev/null') {
    return null;
  }
  const result = decoded.replace(/^[ab]\//, '');
  return result;
}

function locationKey(file, side, line) {
  const result = JSON.stringify([file, side, line]);
  return result;
}

export function changedLines(diff) {
  const lines = new Map();
  const errors = [];
  let oldPath = null;
  let newPath = null;
  let oldLine = 0;
  let newLine = 0;
  let oldRemaining = 0;
  let newRemaining = 0;
  let hasOldHeader = false;
  let hasNewHeader = false;
  let inHunk = false;
  function recordChangedLine(file, side, line, content) {
    const key = locationKey(file, side, line);
    if (lines.has(key)) {
      errors.push('Diff repeats a changed line location.');
    }
    lines.set(key, content);
  }
  for (const raw of diff.split('\n')) {
    const line = raw.endsWith('\r') ? raw.slice(0, -1) : raw;
    if (line.startsWith('diff --git ')) {
      if (oldRemaining !== 0 || newRemaining !== 0) {
        errors.push('Diff has an incomplete hunk.');
      }
      if (hasOldHeader !== hasNewHeader) {
        errors.push('Diff has an incomplete file header.');
      }
      oldPath = null;
      newPath = null;
      oldRemaining = 0;
      newRemaining = 0;
      hasOldHeader = false;
      hasNewHeader = false;
      inHunk = false;
      continue;
    }
    if (line.startsWith('\\ No newline at end of file')) {
      continue;
    }
    if (oldRemaining > 0 || newRemaining > 0) {
      const currentPath = newPath ?? oldPath;
      if (line.startsWith('+')) {
        if (newRemaining <= 0) {
          errors.push('Diff has too many added lines.');
          continue;
        }
        recordChangedLine(currentPath, 'RIGHT', newLine, line.slice(1));
        newLine += 1;
        newRemaining -= 1;
      } else if (line.startsWith('-')) {
        if (oldRemaining <= 0) {
          errors.push('Diff has too many removed lines.');
          continue;
        }
        recordChangedLine(currentPath, 'LEFT', oldLine, line.slice(1));
        oldLine += 1;
        oldRemaining -= 1;
      } else if (line.startsWith(' ') && oldRemaining > 0 && newRemaining > 0) {
        oldLine += 1;
        newLine += 1;
        oldRemaining -= 1;
        newRemaining -= 1;
      } else {
        errors.push('Diff hunk contains an invalid or missing line.');
      }
      continue;
    }
    if (!inHunk && line.startsWith('--- ')) {
      oldPath = decodePath(line.slice(4));
      hasOldHeader = true;
      if (oldPath !== null && !safePath(oldPath)) {
        errors.push('Diff has an unsafe file path.');
      }
      continue;
    }
    if (!inHunk && line.startsWith('+++ ')) {
      newPath = decodePath(line.slice(4));
      hasNewHeader = true;
      if (newPath !== null && !safePath(newPath)) {
        errors.push('Diff has an unsafe file path.');
      }
      continue;
    }
    const hunk = line.match(/^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@/);
    if (hunk) {
      if (!hasOldHeader || !hasNewHeader || (newPath === null && oldPath === null)) {
        errors.push('Diff hunk has no file header.');
      }
      oldLine = Number(hunk[1]);
      newLine = Number(hunk[3]);
      oldRemaining = hunk[2] === undefined ? 1 : Number(hunk[2]);
      newRemaining = hunk[4] === undefined ? 1 : Number(hunk[4]);
      if (![oldLine, newLine, oldRemaining, newRemaining, oldLine + oldRemaining, newLine + newRemaining].every(Number.isSafeInteger)
          || (oldRemaining > 0 && oldLine < 1) || (newRemaining > 0 && newLine < 1)) {
        errors.push('Diff hunk has an invalid line range.');
      }
      inHunk = true;
    } else if (line.startsWith('@@')) {
      errors.push('Diff has an invalid hunk header.');
    } else if (inHunk && /^[ +\-]/.test(line)) {
      errors.push('Diff has extra lines after a complete hunk.');
    }
  }
  if (oldRemaining !== 0 || newRemaining !== 0) {
    errors.push('Diff has an incomplete final hunk.');
  }
  if (hasOldHeader !== hasNewHeader) {
    errors.push('Diff has an incomplete file header.');
  }
  return { lines, errors: [...new Set(errors)] };
}

function safePath(value) {
  const result = typeof value === 'string' && value.length > 0
    && !value.startsWith('/') && !value.includes('\\') && !value.includes('\0')
    && !/^[a-z]:/i.test(value) && !value.split('/').some((part) => ['', '.', '..'].includes(part));
  return result;
}

export function verifyReport(input, report) {
  const errors = [];
  if (!input || typeof input !== 'object' || Array.isArray(input)
      || !report || typeof report !== 'object' || Array.isArray(report)) {
    return { ok: false, errors: ['Input and report must be objects.'] };
  }
  if (typeof input.repository !== 'string' || !/^[^/\s]+\/[^/\s]+$/.test(input.repository)) {
    errors.push('Input repository must identify owner/repository.');
  }
  if (!Number.isSafeInteger(input.number) || input.number < 1) {
    errors.push('Input PR number must be a positive integer.');
  }
  if (typeof input.headOid !== 'string' || !/^(?:[a-f0-9]{40}|[a-f0-9]{64})$/i.test(input.headOid)) {
    errors.push('Input headOid must be a full Git object ID.');
  }
  for (const key of ['repository', 'number', 'headOid']) {
    if (input[key] !== report[key]) {
      errors.push(`Report ${key} does not match the captured PR.`);
    }
  }
  if (typeof input.diff !== 'string') {
    errors.push('Input diff must be a complete unified diff string.');
  }
  if (!Array.isArray(input.files) || !input.files.every((file) => safePath(file?.path))) {
    errors.push('Input files must contain valid repository-relative paths.');
  }
  if (!Array.isArray(report.comments)) {
    errors.push('Report comments must be an array.');
  }
  if (errors.length > 0) {
    return { ok: false, errors };
  }
  const capturedPaths = new Set(input.files.map((file) => file.path));
  const parsed = changedLines(input.diff);
  errors.push(...parsed.errors);
  const seen = new Set();
  for (let index = 0; index < report.comments.length; index += 1) {
    const comment = report.comments[index];
    const prefix = `Comment ${index + 1}`;
    if (!comment || typeof comment !== 'object' || Array.isArray(comment)) {
      errors.push(`${prefix} must be an object.`);
      continue;
    }
    if (!capturedPaths.has(comment.path)) {
      errors.push(`${prefix} path is not in the captured file list.`);
    }
    if (!Number.isSafeInteger(comment.line) || comment.line < 1 || !['LEFT', 'RIGHT'].includes(comment.side)) {
      errors.push(`${prefix} needs a positive line and LEFT/RIGHT side.`);
    }
    if (typeof comment.body !== 'string' || comment.body.trim().length === 0) {
      errors.push(`${prefix} body is empty.`);
    }
    const key = locationKey(comment.path, comment.side, comment.line);
    const changed = parsed.lines.get(key);
    if (changed === undefined) {
      errors.push(`${prefix} does not anchor to a changed line.`);
    }
    if (typeof comment.evidence !== 'string' || comment.evidence.trim().length === 0
        || changed === undefined || !changed.includes(comment.evidence)) {
      errors.push(`${prefix} evidence is not literal text from its changed line.`);
    }
    const fingerprint = JSON.stringify([key, comment.body]);
    if (seen.has(fingerprint)) {
      errors.push(`${prefix} duplicates a prior inline comment.`);
    }
    seen.add(fingerprint);
  }
  if (errors.length > 0) {
    return { ok: false, errors };
  }
  const diffSha256 = createHash('sha256').update(input.diff).digest('hex');
  return { ok: true, repository: input.repository, number: input.number, headOid: input.headOid, diffSha256, comments: report.comments.length };
}

function readJson(file) {
  if (statSync(file).size > 32 * 1024 * 1024) {
    throw new Error('Review artifact exceeds the 32 MiB limit.');
  }
  const result = JSON.parse(readFileSync(file, 'utf8').replace(/^\uFEFF/, ''));
  return result;
}

function main() {
  if (process.argv.length !== 4) {
    process.stderr.write('Usage: node verify-report.mjs <input.json> <report.json>\n');
    process.exitCode = 1;
    return;
  }
  try {
    const result = verifyReport(readJson(process.argv[2]), readJson(process.argv[3]));
    process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
    process.exitCode = result.ok ? 0 : 1;
  } catch {
    process.stderr.write('Review artifacts could not be read or parsed. No artifact contents were logged.\n');
    process.exitCode = 1;
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  main();
}

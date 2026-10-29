#!/usr/bin/env python3
"""Compare Core files without changing either checkout. Python 3 stdlib only."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import urlsplit


class ComparisonError(ValueError):
    pass


def git(root, *args, optional=False):
    result = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, check=False,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
    )
    if result.returncode and not optional:
        raise ComparisonError(result.stderr.decode("utf-8", "replace").strip())
    return result.stdout if result.returncode == 0 else None


def repository_root(value):
    root = Path(value).resolve(strict=True)
    actual = Path(git(root, "rev-parse", "--show-toplevel").decode().strip()).resolve()
    if root != actual:
        raise ComparisonError(f"La ruta debe ser la raíz Git exacta: {root}")
    return root


def relative_path(value, directory=False):
    if not isinstance(value, str) or not value or "\\" in value or ":" in value:
        raise ComparisonError(f"Ruta relativa inválida: {value!r}")
    path = value[:-1] if directory and value.endswith("/") else value
    if any(part in ("", ".", "..", ".git") for part in path.split("/")):
        raise ComparisonError(f"Ruta relativa inválida: {value!r}")
    return value


def local_bytes(root, relative):
    path = root / relative
    try:
        resolved = path.resolve(strict=True)
    except FileNotFoundError:
        if path.is_symlink():
            raise ComparisonError(f"Enlace sin destino: {relative}")
        return None
    try:
        resolved.relative_to(root)
    except ValueError:
        raise ComparisonError(f"La ruta sale de la raíz: {relative}") from None
    if not resolved.is_file():
        raise ComparisonError(f"Se esperaba un archivo: {relative}")
    return resolved.read_bytes()


def parse_json(data, label):
    try:
        return json.loads(data.decode("utf-8-sig"))
    except (UnicodeError, ValueError) as error:
        raise ComparisonError(f"{label}: JSON inválido ({error})") from error


def matches(path, selector):
    return path.startswith(selector) if selector.endswith("/") else path == selector


def manifest_groups(data):
    manifest = parse_json(data, "core-manifest.json")
    if not isinstance(manifest, dict) or type(manifest.get("version")) is not int or manifest["version"] != 1:
        raise ComparisonError("core-manifest.json requiere version: 1")
    groups = {}
    seen = []
    for group in ("shared", "review", "instance"):
        selectors = manifest.get(group)
        if not isinstance(selectors, list) or not selectors:
            raise ComparisonError(f"El grupo {group} debe ser una lista no vacía")
        groups[group] = []
        for selector in selectors:
            relative_path(selector, directory=True)
            if any(matches(selector.rstrip("/"), other) or matches(other.rstrip("/"), selector)
                   or selector == other for other in seen):
                raise ComparisonError(f"Selectores repetidos o superpuestos: {selector}")
            seen.append(selector)
            groups[group].append(selector)
    return groups


def classify(path, groups):
    return next((group for group, selectors in groups.items()
                 if any(matches(path, selector) for selector in selectors)), None)


def canonical_repository(value):
    value = value.strip().rstrip("/")
    scp = re.fullmatch(r"(?:[^@/]+@)?([^:/]+):(.+)", value)
    if "://" in value:
        parsed = urlsplit(value)
        if parsed.scheme not in ("https", "ssh"):
            raise ComparisonError("source.repository debe ser una URL Git HTTPS o SSH")
        host, path = parsed.hostname, parsed.path.lstrip("/")
        if parsed.password or (parsed.username and parsed.scheme != "ssh"):
            raise ComparisonError("La URL del repositorio no debe contener credenciales")
        if not host or parsed.query or parsed.fragment:
            raise ComparisonError("URL del repositorio inválida")
    elif scp:
        host, path = scp.groups()
    else:
        raise ComparisonError("source.repository debe ser una URL Git HTTPS o SSH")
    path = path.strip("/").removesuffix(".git")
    if not path or "\\" in path or any(part in ("", ".", "..") for part in path.split("/")):
        raise ComparisonError("Ruta de repositorio inválida")
    return (host.lower(), path)


def adoption_info(root, source_root, groups, selected_commit):
    data = local_bytes(root, "core-adoption.json")
    if data is None:
        return {"recorded": False}, {}, ["La instancia no registra una revisión del Core adoptada."]
    record = parse_json(data, "core-adoption.json")
    if not isinstance(record, dict) or type(record.get("version")) is not int or record["version"] != 1:
        raise ComparisonError("core-adoption.json requiere version: 1")
    source = record.get("source")
    if not isinstance(source, dict) or not isinstance(source.get("repository"), str):
        raise ComparisonError("core-adoption.json requiere source.repository y source.commit")
    expected_repo = canonical_repository(source["repository"])
    commit = source.get("commit")
    if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-fA-F]{40}|[0-9a-fA-F]{64}", commit):
        raise ComparisonError("source.commit debe ser un SHA completo")
    warnings = []
    origin = git(source_root, "config", "--get", "remote.origin.url", optional=True)
    if origin:
        if canonical_repository(origin.decode().strip()) != expected_repo:
            raise ComparisonError("La metadata de adopción corresponde a otro repositorio Core")
    else:
        warnings.append("El Core no tiene origin; la procedencia declarada no pudo verificarse.")
    overrides = record.get("overrides", [])
    if not isinstance(overrides, list):
        raise ComparisonError("overrides debe ser una lista")
    reasons = {}
    for item in overrides:
        if not isinstance(item, dict):
            raise ComparisonError("Cada override requiere path y reason")
        path = relative_path(item.get("path"))
        reason = item.get("reason")
        if path in reasons or not isinstance(reason, str) or not reason.strip():
            raise ComparisonError(f"Override repetido o sin motivo: {path}")
        if classify(path, groups) != "shared":
            raise ComparisonError(f"El override debe identificar un archivo shared: {path}")
        reasons[path] = reason.strip()
    available = git(source_root, "cat-file", "-e", commit + "^{commit}", optional=True) is not None
    if not available:
        warnings.append("El commit adoptado no está disponible en el Core local; no se descargó.")
    if commit.lower() != selected_commit.lower():
        warnings.append("La referencia comparada difiere del commit registrado como adoptado.")
    return {
        "recorded": True,
        "source": source,
        "matches_reference_commit": commit.lower() == selected_commit.lower(),
        "commit_available": available,
    }, reasons, warnings


class Snapshot:
    def __init__(self, root, revision=None):
        self.root = root
        self.historical = revision is not None
        if revision is not None and (not revision or revision.startswith("-") or "\0" in revision):
            raise ComparisonError("Referencia Git inválida")
        self.commit = git(root, "rev-parse", "--verify", (revision or "HEAD") + "^{commit}").decode().strip()
        self.dirty = False if self.historical else bool(git(root, "status", "--porcelain=v1", "--untracked-files=all"))
        self.entries = {}
        if self.historical:
            for entry in git(root, "ls-tree", "-rz", "--full-tree", self.commit).split(b"\0"):
                if entry:
                    metadata, path = entry.split(b"\t", 1)
                    mode, kind, oid = metadata.decode().split()
                    self.entries[path.decode("utf-8")] = (mode, kind, oid)
        else:
            paths = git(root, "ls-files", "-z", "--cached", "--others", "--exclude-standard")
            self.entries = {path.decode("utf-8"): None for path in paths.split(b"\0") if path}

    def read(self, path):
        relative_path(path)
        if not self.historical:
            return local_bytes(self.root, path)
        entry = self.entries.get(path)
        if entry is None:
            return None
        mode, kind, oid = entry
        if kind != "blob" or mode == "120000":
            raise ComparisonError(f"La revisión contiene un enlace o submódulo no comparable: {path}")
        return git(self.root, "cat-file", "blob", oid)


def compare(core_path, instance_path, revision=None):
    core = Snapshot(repository_root(core_path), revision)
    instance = Snapshot(repository_root(instance_path))
    manifest = core.read("core-manifest.json")
    if manifest is None:
        raise ComparisonError("La fuente seleccionada no contiene core-manifest.json")
    groups = manifest_groups(manifest)
    adoption, overrides, warnings = adoption_info(instance.root, core.root, groups, core.commit)
    paths = set(core.entries) | set(instance.entries)
    paths.update(path for values in groups.values() for path in values if not path.endswith("/"))
    files = []
    unclassified = []
    instance_files = 0
    for path in sorted(paths):
        relative_path(path)
        group = classify(path, groups)
        if group is None:
            unclassified.append(path)
            continue
        if group == "instance":
            instance_files += 1
            continue
        source, target = core.read(path), instance.read(path)
        if source is None and target is None:
            continue
        status = "extra" if source is None else "missing" if target is None else "equal" if source == target else "modified"
        item = {
            "path": path, "group": group, "status": status,
            "expected_override": path in overrides and status != "equal",
            "core_sha256": hashlib.sha256(source).hexdigest() if source is not None else None,
            "instance_sha256": hashlib.sha256(target).hexdigest() if target is not None else None,
        }
        if path in overrides:
            item["reason"] = overrides[path]
        files.append(item)
    changed = {item["path"] for item in files if item["status"] != "equal"}
    for path in overrides.keys() - changed:
        warnings.append(f"Override sin diferencia actual: {path}")
    drift = sum(item["group"] == "shared" and item["status"] != "equal" and not item["expected_override"] for item in files)
    return {
        "version": 1,
        "core": {"mode": "revision" if core.historical else "working_tree", "commit": core.commit,
                 "has_local_changes": core.dirty},
        "instance": {"mode": "working_tree", "commit": instance.commit,
                     "has_local_changes": instance.dirty},
        "adoption": adoption,
        "summary": {
            "shared_drift": drift,
            "expected_overrides": sum(item["expected_override"] for item in files),
            "review_differences": sum(item["group"] == "review" and item["status"] != "equal" for item in files),
            "instance_files_excluded": instance_files,
            "unclassified_files": len(unclassified),
        },
        "files": files,
        "unclassified": unclassified,
        "warnings": warnings,
    }


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Compara Core e instancia sin escribir ni descargar archivos.")
    parser.add_argument("--core", required=True, help="Raíz Git del maestro")
    parser.add_argument("--instance", required=True, help="Raíz Git de la instancia")
    parser.add_argument("--revision", help="Commit o referencia local del Core; por defecto compara archivos actuales")
    parser.add_argument("--json", action="store_true", help="Resultado JSON")
    args = parser.parse_args(argv)
    try:
        report = compare(args.core, args.instance, args.revision)
    except (ComparisonError, OSError, UnicodeError) as error:
        if args.json:
            print(json.dumps({"error": str(error)}, ensure_ascii=False))
        else:
            print(f"Error: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"Core: {report['core']['mode']} ({report['core']['commit']})")
        print(f"Instancia: working_tree ({report['instance']['commit']})")
        for item in report["files"]:
            if item["status"] != "equal":
                suffix = f"; adaptación declarada: {item['reason']}" if item["expected_override"] else ""
                print(f"{item['group']}: {item['status']} {item['path']}{suffix}")
        for warning in report["warnings"]:
            print(f"Aviso: {warning}")
        print("Resumen: " + json.dumps(report["summary"], ensure_ascii=False))
    return 1 if report["summary"]["shared_drift"] else 0


if __name__ == "__main__":
    sys.exit(main())

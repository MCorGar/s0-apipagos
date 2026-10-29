"""Behavior checks for the read-only Core comparator, using isolated Git roots."""

import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


SPEC = importlib.util.spec_from_file_location("compare_core", Path(__file__).with_name("compare-core.py"))
COMPARATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(COMPARATOR)


class CompareCoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="s0-core-compare-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.core = self.make_repo("core")
        self.instance = self.make_repo("instance")
        self.other = self.make_repo("other")
        self.manifest = {
            "version": 1,
            "shared": ["skills/", "core-manifest.json"],
            "review": ["AGENTS.md"],
            "instance": ["context/", "core-adoption.json"],
        }
        for root in (self.core, self.instance, self.other):
            self.write(root, "core-manifest.json", json.dumps(self.manifest))
            self.write(root, "skills/one.md", "shared method\n")
            self.write(root, "skills/two.md", "second method\n")
            self.write(root, "AGENTS.md", "Common guidance\n")
            self.write(root, "context/project.md", f"Instance: {root.name}\n")
            self.commit(root)

    def git(self, root, *args):
        return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.STDOUT)

    def make_repo(self, name):
        root = self.base / name
        root.mkdir()
        self.git(root, "init")
        self.git(root, "config", "user.name", "Core comparator test")
        self.git(root, "config", "user.email", "core-test@example.invalid")
        self.git(root, "config", "commit.gpgsign", "false")
        self.git(root, "config", "core.autocrlf", "false")
        self.git(root, "remote", "add", "origin", "https://example.invalid/team/core.git")
        return root

    def write(self, root, path, content):
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8", newline="\n")

    def commit(self, root):
        self.git(root, "add", ".")
        self.git(root, "-c", "core.hooksPath=" + str(self.base / "no-hooks"), "commit", "-m", "fixture")
        return self.git(root, "rev-parse", "HEAD").decode().strip()

    def adoption(self, overrides=None, commit=None, repository="https://example.invalid/team/core.git"):
        record = {
            "version": 1,
            "source": {
                "repository": repository,
                "commit": commit or self.git(self.core, "rev-parse", "HEAD").decode().strip(),
            },
            "overrides": overrides or [],
        }
        self.write(self.instance, "core-adoption.json", json.dumps(record))

    def report(self, revision=None):
        return COMPARATOR.compare(self.core, self.instance, revision)

    def test_equal_shared_files_ignore_instance_content_and_remain_read_only(self):
        self.adoption()
        self.write(self.instance, "context/private.md", "instance-owned\n")
        before = {
            str(path): path.read_bytes()
            for root in (self.core, self.instance, self.other)
            for path in root.rglob("*") if path.is_file()
        }
        report = self.report()
        after = {str(path): path.read_bytes() for root in (self.core, self.instance, self.other)
                 for path in root.rglob("*") if path.is_file()}
        self.assertEqual(0, report["summary"]["shared_drift"])
        self.assertTrue(report["adoption"]["matches_reference_commit"])
        self.assertEqual(before, after)
        self.assertNotIn("context/project.md", [row["path"] for row in report["files"]])

    def test_modified_missing_and_extra_shared_files_are_distinct(self):
        self.write(self.instance, "skills/one.md", "different\n")
        (self.instance / "skills/two.md").unlink()
        self.write(self.instance, "skills/three.md", "extra\n")
        report = self.report()
        statuses = {row["path"]: row["status"] for row in report["files"]}
        self.assertEqual("modified", statuses["skills/one.md"])
        self.assertEqual("missing", statuses["skills/two.md"])
        self.assertEqual("extra", statuses["skills/three.md"])
        self.assertEqual(3, report["summary"]["shared_drift"])

    def test_declared_override_stays_modified_and_does_not_hide_other_changes(self):
        self.write(self.instance, "skills/one.md", "instance extension\n")
        self.write(self.instance, "skills/two.md", "unexplained change\n")
        self.adoption([{"path": "skills/one.md", "reason": "Instance-specific source integration"}])
        report = self.report()
        row = next(row for row in report["files"] if row["path"] == "skills/one.md")
        self.assertEqual("modified", row["status"])
        self.assertTrue(row["expected_override"])
        self.assertNotEqual(row["core_sha256"], row["instance_sha256"])
        self.assertEqual(1, report["summary"]["shared_drift"])

    def test_review_changes_are_visible_but_do_not_count_as_shared_drift(self):
        self.write(self.instance, "AGENTS.md", "Instance rules\n")
        report = self.report()
        self.assertEqual(1, report["summary"]["review_differences"])
        self.assertEqual(0, report["summary"]["shared_drift"])

    def test_revision_uses_committed_source_instead_of_working_tree(self):
        revision = self.git(self.core, "rev-parse", "HEAD").decode().strip()
        self.adoption(commit=revision)
        self.write(self.core, "skills/one.md", "new source not committed\n")
        self.assertEqual(1, self.report()["summary"]["shared_drift"])
        historical = self.report(revision)
        self.assertEqual(0, historical["summary"]["shared_drift"])
        self.assertEqual("revision", historical["core"]["mode"])

    def test_different_adopted_commit_is_reported(self):
        old = self.git(self.core, "rev-parse", "HEAD").decode().strip()
        self.adoption(commit=old)
        self.write(self.core, "skills/one.md", "new revision\n")
        new = self.commit(self.core)
        report = self.report(new)
        self.assertFalse(report["adoption"]["matches_reference_commit"])
        self.assertEqual(1, report["summary"]["shared_drift"])

    def test_foreign_source_metadata_is_rejected(self):
        self.adoption(repository="https://example.invalid/other/core.git")
        with self.assertRaises(COMPARATOR.ComparisonError):
            self.report()

    def test_ssh_and_https_repository_names_are_equivalent(self):
        self.adoption(repository="git@example.invalid:team/core.git")
        self.assertTrue(self.report()["adoption"]["recorded"])

    def test_malformed_metadata_and_overrides_are_rejected(self):
        cases = [
            "not-json",
            json.dumps({"version": 1}),
            json.dumps({"version": True}),
        ]
        for content in cases:
            with self.subTest(content=content):
                self.write(self.instance, "core-adoption.json", content)
                with self.assertRaises(COMPARATOR.ComparisonError):
                    self.report()
        for override in [
            {"path": "skills/one.md", "reason": ""},
            {"path": "../outside", "reason": "invalid"},
            {"path": "context/project.md", "reason": "instance data"},
        ]:
            with self.subTest(override=override):
                self.adoption([override])
                with self.assertRaises(COMPARATOR.ComparisonError):
                    self.report()

    def test_manifest_cannot_select_parent_paths_or_overlap_groups(self):
        for selector in ["../outside/", "/absolute", "C:/outside", ".git/config", "skills/../other"]:
            with self.subTest(selector=selector):
                manifest = dict(self.manifest, review=[selector])
                self.write(self.core, "core-manifest.json", json.dumps(manifest))
                with self.assertRaises(COMPARATOR.ComparisonError):
                    self.report()
        self.write(self.core, "core-manifest.json", json.dumps(dict(self.manifest, review=["skills/one.md"])))
        with self.assertRaises(COMPARATOR.ComparisonError):
            self.report()

    def test_file_link_outside_root_is_rejected(self):
        target = self.instance / "skills/one.md"
        target.unlink()
        try:
            target.symlink_to(self.other / "skills/one.md")
        except OSError as error:
            self.skipTest(f"Symlinks no disponibles: {error}")
        with self.assertRaises(COMPARATOR.ComparisonError):
            self.report()

    def test_directory_junction_outside_root_is_rejected_on_windows(self):
        if os.name != "nt":
            self.skipTest("Junctions sólo en Windows")
        directory = self.instance / "skills"
        self.assertEqual(self.instance.resolve(), directory.resolve().parent)
        shutil.rmtree(directory)
        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(directory), str(self.other / "skills")],
            capture_output=True,
        )
        if result.returncode:
            self.skipTest("No se pudo crear el junction del fixture")
        try:
            with self.assertRaises(COMPARATOR.ComparisonError):
                self.report()
        finally:
            directory.rmdir()

    def test_cli_exit_codes_distinguish_drift_and_invalid_metadata(self):
        command = [os.sys.executable, "-B", str(Path(__file__).with_name("compare-core.py")),
                   "--core", str(self.core), "--instance", str(self.instance), "--json"]
        equal = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(0, equal.returncode, equal.stderr)
        self.write(self.instance, "skills/one.md", "drift\n")
        drift = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(1, drift.returncode)
        self.assertEqual(1, json.loads(drift.stdout)["summary"]["shared_drift"])
        self.write(self.instance, "core-adoption.json", "broken")
        broken = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(2, broken.returncode)
        self.assertIn("error", json.loads(broken.stdout))


if __name__ == "__main__":
    unittest.main()

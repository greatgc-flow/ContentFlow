import ast
import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / "design/contentflow-v0.1/examples/workflow.example.json"
IDENTITY = UUID("00000000-0000-4000-8000-000000000001")
ENTITY = UUID("00000000-0000-4000-8000-000000000002")
NOW = datetime(2026, 11, 28, tzinfo=timezone.utc)


class DomainTests(unittest.TestCase):
    def test_canonical_vector_and_parser(self):
        from contentflow.domain import digest, decode
        expected = hashlib.sha256('CF-CJSON-1\0{"a":true,"한":75}'.encode()).hexdigest()
        self.assertEqual(expected, digest({"한": 75, "a": True}))
        for wire in (b'{"x":1,"x":2}', b'1.5', b'NaN', b'9007199254740992',
                     b'"\\udfff"', b'\xef\xbb\xbf{}'):
            with self.subTest(wire=wire), self.assertRaises(ValueError):
                decode(wire)
        for value in (1.0, {1: "x"}, (1, 2), 2**53):
            with self.subTest(value=value), self.assertRaises(ValueError):
                digest(value)

    def test_snapshot_cas_and_scope(self):
        from contentflow.domain import Revision
        body = {"rows": [100, 75]}
        first = Revision.create(IDENTITY, ENTITY, body)
        body["rows"][1] = 80
        second = first.edit(IDENTITY, 1, body)
        self.assertEqual(first.body, b'{"rows":[100,75]}')
        self.assertNotEqual(first.digest, second.digest)
        self.assertEqual(second.number, 2)
        for scope, expected in ((ENTITY, 1), (IDENTITY, 0), (IDENTITY, True)):
            with self.assertRaises(ValueError):
                first.edit(scope, expected, body)

    def test_review_binds_rights_revision_policy_actor_and_expiry(self):
        from contentflow.domain import Revision, Review, Rights
        doc = Revision.create(IDENTITY, ENTITY, {"rows": [100, 75]})
        expires = NOW + timedelta(days=1)
        rights = Rights(frozenset({"READ", "TRANSFORM"}), expires)
        review = Review.for_preview(doc, actor=ENTITY, policy="p1", expires=expires)
        valid = dict(document=doc, actor=ENTITY, policy="p1", rights=rights, now=NOW)
        self.assertTrue(review.permits_preview(**valid))
        for change in ({"document": doc.edit(IDENTITY, 1, {"rows": [100, 75]})},
                       {"document": Revision.create(ENTITY, IDENTITY, {"rows": [100, 75]})},
                       {"document": Revision.create(IDENTITY, ENTITY, {"rows": [90, 75]})},
                       {"actor": IDENTITY}, {"policy": "p2"}, {"now": expires},
                       {"rights": Rights(frozenset({"READ"}), expires)},
                       {"rights": Rights(rights.permissions, NOW)}):
            with self.subTest(change=change):
                self.assertFalse(review.permits_preview(**(valid | change)))

    def test_fixture_dag_and_adversarial_nodes(self):
        from contentflow.workflow import plan
        wf = json.loads(WORKFLOW.read_bytes())
        order = [s["key"] for s in wf["steps"]]
        self.assertEqual(plan(wf), order)
        wf["steps"].reverse()
        self.assertEqual(plan(wf), order)
        for changes in ({"depends_on": ["export"]}, {"depends_on": ["unknown"]},
                        {"kind": "SHELL"}, {"kind": "PUBLISH_SUBMIT", "effect": "PURE"},
                        {"effect": "PAID_REMOTE"}, {"provider_id": "cloud"},
                        {"inputs": ["absent"]}, {"inputs": [None]}, {"key": "qc"},
                        {"max_attempts": True}, {"gpu_slots": 1}, {"command": "echo"},
                        {"outputs": ["video"]}, {"optional": True}):
            bad = copy.deepcopy(wf)
            bad["steps"][-1].update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                plan(bad)

    def test_pure_import_boundary(self):
        allowed = {"__future__", "dataclasses", "datetime", "hashlib", "json", "re", "uuid",
                   "heapq", "graphlib", "contentflow.domain"}
        for name in ("domain", "workflow"):
            tree = ast.parse((ROOT / "contentflow" / (name + ".py")).read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    self.assertIn(node.module, allowed)
                elif isinstance(node, ast.Import):
                    self.assertLessEqual({a.name for a in node.names}, allowed)


class CommandTests(unittest.TestCase):
    def test_standalone_public_dry_run_does_not_write(self):
        env = dict(os.environ, PYTHONPATH=str(ROOT), PYTHONDONTWRITEBYTECODE="1")
        with tempfile.TemporaryDirectory() as tmp:
            cmd = [sys.executable, "-B", "-m", "contentflow", "run", "--workflow",
                   str(WORKFLOW), "--dry-run", "--json"]
            def invoke():
                return subprocess.run(cmd, cwd=tmp, env=env, capture_output=True, text=True)
            first = invoke()
            self.assertEqual(first.returncode, 0, first.stderr)
            one = json.loads(first.stdout)
            self.assertEqual(one["status"], "PLANNED")
            self.assertEqual(one["steps"][-1], "export")
            self.assertTrue(one["test_only"])
            self.assertEqual(one["workflow_digest"], json.loads(invoke().stdout)["workflow_digest"])
            cmd.remove("--dry-run")
            self.assertEqual(invoke().returncode, 2)
            self.assertEqual(list(Path(tmp).iterdir()), [])

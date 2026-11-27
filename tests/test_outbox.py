import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from uuid import UUID

from contentflow.execution import Money

WS = UUID("00000000-0000-4000-8000-000000000001")
A = UUID("00000000-0000-4000-8000-000000000002")
B = UUID("00000000-0000-4000-8000-000000000003")
CAP = Money(100, "KRW", 0)
BOUND = Money(75, "KRW", 0)


class OutboxTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "test.db"

    def test_crash_unknown_replay_and_settlement(self):
        from contentflow.outbox import FixtureOutbox
        with FixtureOutbox.create(self.path, WS, CAP) as box:
            first = box.prepare(A, {"source": "a"}, BOUND)
            self.assertEqual(first["state"], "HELD")
            self.assertEqual(box.prepare(A, {"source": "a"}, BOUND), first)
            with self.assertRaises(ValueError):
                box.prepare(A, {"source": "b"}, BOUND)
            self.assertEqual(box.claim(A)["state"], "UNKNOWN")
        with FixtureOutbox.open(self.path, WS) as box:
            self.assertEqual(box.prepare(A, {"source": "a"}, BOUND)["state"], "UNKNOWN")
            with self.assertRaises(ValueError):
                box.claim(A)
            with self.assertRaises(ValueError):
                box.prepare(B, {}, BOUND)
            result = box.reconcile(A, Money(20, "KRW", 0), "fake-receipt")
            self.assertEqual(result["state"], "SETTLED")
            self.assertEqual(box.reconcile(A, Money(20, "KRW", 0), "fake-receipt"), result)
            with self.assertRaises(ValueError):
                box.reconcile(A, Money(1, "KRW", 0), "fake-receipt")
            self.assertEqual(box.prepare(B, {}, BOUND)["state"], "HELD")

    def test_competing_reservations_share_one_cap(self):
        from contentflow.outbox import FixtureOutbox
        with FixtureOutbox.create(self.path, WS, CAP):
            pass
        sync = Barrier(2)
        def attempt(op):
            with FixtureOutbox.open(self.path, WS) as box:
                sync.wait(timeout=5)
                try:
                    return box.prepare(op, {"test_only": True}, BOUND)["state"]
                except ValueError as exc:
                    return str(exc)
        with ThreadPoolExecutor(2) as executor:
            self.assertCountEqual(executor.map(attempt, (A, B)), ["HELD", "reservation exceeds budget"])

    def test_foreign_or_existing_database_is_preserved(self):
        from contentflow.outbox import FixtureOutbox
        self.path.write_bytes(b"existing-user-bytes")
        with self.assertRaises(FileExistsError):
            FixtureOutbox.create(self.path, WS, CAP)
        with self.assertRaises((ValueError, sqlite3.DatabaseError)):
            FixtureOutbox.open(self.path, WS)
        self.assertEqual(self.path.read_bytes(), b"existing-user-bytes")
        self.path.unlink()
        with FixtureOutbox.create(self.path, WS, CAP):
            pass
        with self.assertRaises(ValueError):
            FixtureOutbox.open(self.path, B)
        missing = self.path.parent / "other"
        with self.assertRaises((ValueError, OSError, sqlite3.Error)):
            FixtureOutbox.open(missing, WS)
        self.assertFalse(missing.exists())

    def test_atomic_failure_and_overage(self):
        from contentflow.outbox import FixtureOutbox
        with FixtureOutbox.create(self.path, WS, CAP) as box:
            with self.assertRaises(ValueError):
                box.prepare(A, {}, Money(1, "USD", 2))
            box.prepare(A, {}, BOUND)
            box.claim(A)
            with self.assertRaises(ValueError):
                box.reconcile(A, Money(80, "KRW", 0), "")
            self.assertTrue(box.reconcile(A, Money(80, "KRW", 0), "overage")["over_limit"])
            with self.assertRaises(ValueError):
                box.prepare(B, {}, Money(1, "KRW", 0))

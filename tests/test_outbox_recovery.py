"""Check restoration of pending synthetic effects without restoring execution authority."""
import tempfile
import unittest
from pathlib import Path

from contentflow.execution import Money
from contentflow.outbox import FixtureOutbox
from test_outbox import A, B, BOUND, CAP, WS


class OutboxRecoveryTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.live = self.root / "live.sqlite3"
        self.snapshot = self.root / "checkpoint.json"
        self.review = self.root / "review.json"

    def test_pending_never_requeues_and_active_settlement_wins(self):
        from contentflow.outbox_recovery import checkpoint, read_review, restore_review
        with FixtureOutbox.create(self.live, WS, CAP) as live:
            live.prepare(A, {"credential": "must-not-export"}, BOUND)
            checkpoint(live, self.snapshot)
            live.claim(A)
            live.prepare(B, {}, Money(25, "KRW", 0))
            restore_review(live, self.snapshot, self.review)
            view = read_review(self.review)
            self.assertEqual(view["operations"][str(A)]["state"], "UNKNOWN")
            self.assertEqual(view["operations"][str(B)]["state"], "HELD")
            self.assertFalse(view["execution_authorized"])
            self.assertNotIn(b"must-not-export", self.snapshot.read_bytes())
            self.assertNotIn(b"must-not-export", self.review.read_bytes())
            with self.assertRaises(ValueError):
                FixtureOutbox.open(self.review, WS)
            with self.assertRaises(ValueError):
                live.claim(A)
            live.reconcile(A, Money(90, "KRW", 0), "private-receipt")
            target = self.root / "settled.json"
            restore_review(live, self.snapshot, target)
            view = read_review(target)
            self.assertEqual(view["operations"][str(A)]["actual"], 90)
            self.assertTrue(view["budget_frozen"])
            self.assertNotIn(b"private-receipt", target.read_bytes())

    def test_rejects_wrong_ledger_forged_snapshot_and_existing_destination(self):
        from contentflow.outbox_recovery import checkpoint, restore_review
        with FixtureOutbox.create(self.live, WS, CAP) as live:
            live.prepare(A, {"id": 1}, BOUND)
            checkpoint(live, self.snapshot)
        other = self.root / "other.sqlite3"
        with FixtureOutbox.create(other, WS, CAP) as conflicting:
            conflicting.prepare(A, {"id": 2}, BOUND)
            with self.assertRaises(ValueError):
                restore_review(conflicting, self.snapshot, self.review)
        self.assertFalse(self.review.exists())
        with FixtureOutbox.open(self.live, WS) as live:
            wire = self.snapshot.read_bytes()
            self.snapshot.write_bytes(wire.replace(b'"upper_minor":75', b'"upper_minor":70'))
            with self.assertRaises(ValueError):
                restore_review(live, self.snapshot, self.review)
            self.assertFalse(self.review.exists())
            self.snapshot.write_bytes(wire)
            self.review.write_bytes(b"existing bytes")
            with self.assertRaises(FileExistsError):
                restore_review(live, self.snapshot, self.review)
            self.assertEqual(self.review.read_bytes(), b"existing bytes")

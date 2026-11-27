import unittest


class ExecutionTests(unittest.TestCase):
    def test_requeue_requires_wait_or_running_and_terminals_are_final(self):
        from contentflow.execution import job_transition
        for waiting in ("WAITING_REVIEW", "WAITING_BUDGET", "WAITING_EXTERNAL"):
            state = "QUEUED"
            for target in ("RUNNING", waiting, "QUEUED", "RUNNING", "SUCCEEDED"):
                state = job_transition(state, target)
            for target in ("RUNNING", "QUEUED", "CANCELED"):
                with self.assertRaises(ValueError):
                    job_transition(state, target)
        with self.assertRaises(ValueError):
            job_transition("QUEUED", "SUCCEEDED")

    def test_steps_require_explicit_optional_skip(self):
        from contentflow.execution import step_transition
        for target in ("SUCCEEDED", "FAILED", "CANCELED"):
            self.assertEqual(step_transition("RUNNING", target), target)
            with self.assertRaises(ValueError):
                step_transition(target, "READY")
        self.assertEqual(step_transition("PENDING", "SKIPPED", optional=True), "SKIPPED")
        for optional in (False, 1, "yes"):
            with self.assertRaises(ValueError):
                step_transition("PENDING", "SKIPPED", optional=optional)

    def test_budget_currency_and_scale_are_exact(self):
        from contentflow.execution import Money, check_reservation
        cap = Money(100, "USD", 2)
        check_reservation(cap, Money(0, "USD", 2), Money(100, "USD", 2))
        for used, requested in ((Money(1, "USD", 2), cap),
                                (Money(0, "KRW", 0), cap), (cap, Money(1, "KRW", 0))):
            with self.assertRaises(ValueError):
                check_reservation(cap, used, requested)
        for values in ((1.0, "USD", 2), (True, "KRW", 0), (-1, "USD", 2),
                       (1, "KRW", 2), (1, "USD", True), (1, "EUR", 2)):
            with self.assertRaises(ValueError):
                Money(*values)

    def test_unknown_exposure_survives_until_evidenced_reconciliation(self):
        from contentflow.execution import Money, Reservation
        bound = Money(75, "KRW", 0)
        held = Reservation.hold(bound)
        unknown = held.unknown()
        self.assertEqual(held.state, "HELD")
        self.assertEqual(unknown.exposure, bound)
        for receipt in ("", None):
            with self.assertRaises(ValueError):
                unknown.resolve(Money(0, "KRW", 0), receipt)
        settled = unknown.resolve(Money(80, "KRW", 0), "fixture-receipt-1")
        self.assertTrue(settled.over_limit)
        self.assertEqual(settled.exposure.minor, 80)
        with self.assertRaises(ValueError):
            settled.resolve(Money(0, "KRW", 0), "second")
        self.assertEqual(unknown.resolve(Money(0, "KRW", 0), "proved-no-charge").state, "RELEASED")

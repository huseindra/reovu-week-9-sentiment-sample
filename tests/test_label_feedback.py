import csv
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from label_feedback import classify_severity, classify_topic, label_rows, score_sentiment


class SentimentTests(unittest.TestCase):
    def test_positive(self):
        self.assertEqual(score_sentiment("This is great, I love it, thank you!"), "positive")

    def test_negative(self):
        self.assertEqual(
            score_sentiment("This is unacceptable, the app keeps crashing and losing my work."),
            "negative",
        )

    def test_neutral(self):
        self.assertEqual(
            score_sentiment("Does the Pro plan include the team workspace feature?"),
            "neutral",
        )


class TopicTests(unittest.TestCase):
    def test_authentication(self):
        self.assertEqual(
            classify_topic("I cannot log in at all since this morning, invalid session."),
            "authentication",
        )

    def test_data_loss(self):
        self.assertEqual(
            classify_topic("All of my saved projects have disappeared, three days of work are gone."),
            "data-loss",
        )

    def test_security_privacy(self):
        self.assertEqual(
            classify_topic("I could see another customer's invoices and email address."),
            "security-privacy",
        )

    def test_billing_payments(self):
        self.assertEqual(
            classify_topic("I was charged twice for my June subscription, please refund."),
            "billing-payments",
        )

    def test_support_response_not_billing(self):
        # Mentions "billing" but is really about an unanswered ticket.
        self.assertEqual(
            classify_topic("I opened a support ticket about billing and nobody has replied."),
            "support-response",
        )

    def test_feature_request_not_high_severity_keyword(self):
        # "keyboard" contains "board" as a substring; must not be mistaken for the
        # \bboard\b high-severity keyword or any topic tied to it.
        self.assertEqual(
            classify_topic("One suggestion would be keyboard shortcuts for common actions."),
            "feature-request",
        )

    def test_default_general(self):
        self.assertEqual(classify_topic("Just saying hello, nothing to report."), "general")


class SeverityTests(unittest.TestCase):
    def test_critical_topic(self):
        self.assertEqual(
            classify_severity("irrelevant text", "authentication", "negative"), "critical"
        )

    def test_high_topic(self):
        self.assertEqual(
            classify_severity("irrelevant text", "billing-payments", "negative"), "high"
        )

    def test_low_override_beats_high_topic_bug(self):
        self.assertEqual(
            classify_severity(
                "Not urgent, but it makes the reports look unfinished when I share them.",
                "bug-stability",
                "negative",
            ),
            "low",
        )

    def test_bug_blocking_work_is_high(self):
        self.assertEqual(
            classify_severity(
                "The editor crashes and it is blocking my work.", "bug-stability", "negative"
            ),
            "high",
        )

    def test_onboarding_word_does_not_trigger_board_keyword(self):
        # Regression test: "board" must not match inside "onboarding".
        self.assertEqual(
            classify_severity(
                "The new onboarding flow is fantastic, great work.", "onboarding", "positive"
            ),
            "low",
        )

    def test_default_negative_is_medium(self):
        self.assertEqual(
            classify_severity("The settings page is confusing.", "usability", "negative"),
            "medium",
        )

    def test_default_neutral_is_low(self):
        self.assertEqual(
            classify_severity("Does the Pro plan include workspaces?", "pricing-plans", "neutral"),
            "low",
        )


class LabelRowsAndSplitTests(unittest.TestCase):
    def setUp(self):
        fixture = Path(__file__).resolve().parent / "fixtures" / "sample_feedback.csv"
        with fixture.open(newline="", encoding="utf-8") as f:
            self.rows = list(csv.DictReader(f))

    def test_label_rows_adds_expected_fields(self):
        labeled = label_rows(self.rows)
        self.assertEqual(len(labeled), len(self.rows))
        for row in labeled:
            self.assertIn("sentiment", row)
            self.assertIn("topic", row)
            self.assertIn("severity", row)

    def test_split_high_critical_from_routine(self):
        labeled = label_rows(self.rows)
        high_critical = [r for r in labeled if r["severity"] in ("high", "critical")]
        routine = [r for r in labeled if r["severity"] not in ("high", "critical")]

        self.assertEqual(len(high_critical) + len(routine), len(labeled))
        ids_by_id = {r["id"]: r for r in labeled}

        self.assertEqual(ids_by_id["1"]["severity"], "critical")  # login outage
        self.assertEqual(ids_by_id["2"]["severity"], "high")  # duplicate charge
        self.assertEqual(ids_by_id["3"]["severity"], "low")  # praise / feature request


if __name__ == "__main__":
    unittest.main()

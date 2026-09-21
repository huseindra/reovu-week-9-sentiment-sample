#!/usr/bin/env python3
"""Label customer feedback with sentiment, topic, and severity, then split
high/critical rows out from the rest.

Usage:
    python scripts/label_feedback.py [--input data/feedback.csv] [--outdir data/output]
"""

import argparse
import csv
import re
from pathlib import Path

# --- Sentiment -------------------------------------------------------------

NEGATIVE_WORDS = [
    "unacceptable", "cannot", "can't", "disappear", "gone", "panicking",
    "cancel", "cancelling", "competitor", "privacy problem", "serious",
    "crash", "crashes", "losing", "lost", "blocking", "disappointed",
    "frustrat", "confus", "gave up", "cuts off", "unfinished", "typo",
    "logging me out", "logs me out", "stuck", "failing", "fail", "too many",
    "do not match", "doesn't match", "does not match", "thin", "lost on",
    "not urgent, but", "problem", "issue", "bug", "slow", "annoying",
]

POSITIVE_WORDS = [
    "great", "fantastic", "love", "thank you", "thanks", "kind", "snappier",
    "speed improvements", "keep up the great work", "wish there was",
    "would thank you", "solved", "in under ten minutes",
]

def score_sentiment(text: str) -> str:
    lowered = text.lower()
    neg_hits = sum(1 for w in NEGATIVE_WORDS if w in lowered)
    pos_hits = sum(1 for w in POSITIVE_WORDS if w in lowered)
    if pos_hits > neg_hits:
        return "positive"
    if neg_hits > pos_hits:
        return "negative"
    return "neutral"


# --- Topic -------------------------------------------------------------
# Ordered most-specific/severe first: the first matching rule wins.

TOPIC_RULES = [
    ("security-privacy", [
        r"another customer'?s", r"privacy problem", r"see another customer",
    ]),
    ("data-loss", [
        r"disappeared", r"gone\b", r"recover them", r"days of work",
    ]),
    ("reliability-outage", [
        r"outage", r"cancelling our team plan", r"moving to a competitor",
    ]),
    ("authentication", [
        r"cannot log in", r"can't log in", r"invalid session", r"logging me out",
        r"logs me out",
    ]),
    ("billing-payments", [
        r"charged twice", r"duplicate charge", r"refund", r"payment keeps failing",
        r"upgrade to the annual plan",
    ]),
    ("reporting-data-accuracy", [
        r"revenue report", r"live dashboard", r"do not match|doesn't match|does not match",
    ]),
    ("bug-stability", [
        r"crash", r"\bbug\b", r"resets when i switch tabs", r"cuts off the last column",
    ]),
    ("performance", [
        r"seconds to load", r"slow\b"
    ]),
    ("support-response", [
        r"support ticket", r"nobody has replied", r"response time", r"support agent",
    ]),
    ("data-request", [
        r"delete all of my personal data", r"under the new regulations", r"confirm once this is done",
    ]),
    ("content-typo", [
        r"\btypo\b",
    ]),
    ("notifications", [
        r"notifications", r"batch them",
    ]),
    ("documentation", [
        r"api docs", r"webhook", r"working example payload",
    ]),
    ("pricing-plans", [
        r"pro plan", r"business plan", r"pricing page",
    ]),
    ("onboarding", [
        r"onboarding", r"invite my teammates", r"walkthrough", r"trial",
    ]),
    ("usability", [
        r"settings page", r"could not find", r"confusing",
    ]),
    ("feature-request", [
        r"would love to see", r"integration with", r"dark mode", r"keyboard shortcuts",
        r"widget for the home screen", r"wish there was",
    ]),
    ("mobile", [
        r"android", r"mobile app",
    ]),
    ("praise-general", [
        r"great app", r"love the", r"fantastic", r"thank you",
    ]),
]

def classify_topic(text: str) -> str:
    lowered = text.lower()
    for topic, patterns in TOPIC_RULES:
        for pattern in patterns:
            if re.search(pattern, lowered):
                return topic
    return "general"


# --- Severity -------------------------------------------------------------

CRITICAL_TOPICS = {"security-privacy", "data-loss", "reliability-outage", "authentication"}
HIGH_TOPICS = {"billing-payments", "reporting-data-accuracy", "data-request"}
HIGH_KEYWORDS = [
    r"blocking my work", r"unacceptable", r"stuck on monthly", r"\bboard\b",
]
LOW_OVERRIDE_PHRASES = ["not urgent", "small thing", "would be nice", "nice to have"]

def classify_severity(text: str, topic: str, sentiment: str) -> str:
    lowered = text.lower()
    if topic in CRITICAL_TOPICS:
        return "critical"
    if any(phrase in lowered for phrase in LOW_OVERRIDE_PHRASES) and topic not in HIGH_TOPICS:
        return "low"
    if topic in HIGH_TOPICS:
        return "high"
    if topic == "bug-stability" and ("blocking" in lowered or "crashes" in lowered):
        return "high"
    if any(re.search(pattern, lowered) for pattern in HIGH_KEYWORDS):
        return "high"
    if sentiment == "negative":
        return "medium"
    return "low"


def label_rows(rows):
    labeled = []
    for row in rows:
        message = row["message"]
        sentiment = score_sentiment(message)
        topic = classify_topic(message)
        severity = classify_severity(message, topic, sentiment)
        labeled.append({**row, "sentiment": sentiment, "topic": topic, "severity": severity})
    return labeled


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/feedback.csv", type=Path)
    parser.add_argument("--outdir", default="data/output", type=Path)
    args = parser.parse_args()

    with args.input.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    labeled = label_rows(rows)

    args.outdir.mkdir(parents=True, exist_ok=True)
    fieldnames = list(labeled[0].keys())

    all_path = args.outdir / "labeled_feedback.csv"
    priority_path = args.outdir / "high_critical_feedback.csv"
    routine_path = args.outdir / "routine_feedback.csv"

    priority_rows = [r for r in labeled if r["severity"] in ("high", "critical")]
    routine_rows = [r for r in labeled if r["severity"] not in ("high", "critical")]

    for path, data in [(all_path, labeled), (priority_path, priority_rows), (routine_path, routine_rows)]:
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

    print(f"Labeled {len(labeled)} rows -> {all_path}")
    print(f"  high/critical: {len(priority_rows)} -> {priority_path}")
    print(f"  routine:       {len(routine_rows)} -> {routine_path}")


if __name__ == "__main__":
    main()

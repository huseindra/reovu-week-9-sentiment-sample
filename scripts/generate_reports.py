#!/usr/bin/env python3
"""Turn labeled feedback into an escalation email draft and a routine log.

Reads the output of scripts/label_feedback.py (data/output/labeled_feedback.csv)
and produces two files:

  - reports/escalation_email_draft.txt  A single email addressed to the support
    lead, summarizing every "high"/"critical" row with a suggested customer
    reply for each.
  - reports/routine_log.txt             A plain-text log of every "medium"/"low"
    row, for record-keeping without needing a reply right away.

Usage:
    python scripts/generate_reports.py [--input data/output/labeled_feedback.csv]
                                        [--outdir reports]
                                        [--support-lead "<Support Lead Name> <support-lead@example.com>"]
"""

import argparse
import csv
from datetime import date
from pathlib import Path

ESCALATION_SEVERITIES = {"critical", "high"}

REPLY_TEMPLATES = {
    "authentication": (
        "Hi {name}, we're sorry you're locked out and understand the urgency. "
        "Our engineering team is investigating your account access right now and "
        "we'll update you as soon as it's restored."
    ),
    "data-loss": (
        "Hi {name}, we understand how alarming it is to lose your work. We're "
        "actively investigating whether your projects can be recovered and will "
        "follow up with a status as soon as we have one."
    ),
    "reliability-outage": (
        "Hi {name}, we're sorry for the repeated outages and understand the impact "
        "on your business. We're treating this as a top priority and will share a "
        "reliability update shortly."
    ),
    "security-privacy": (
        "Hi {name}, thank you for reporting this right away. This is a serious issue "
        "and our security team has already been notified and is investigating. We'll "
        "follow up with findings and next steps."
    ),
    "billing-payments": (
        "Hi {name}, we're sorry for the billing trouble. We're reviewing your account "
        "now and will follow up with a correction as soon as possible."
    ),
    "reporting-data-accuracy": (
        "Hi {name}, thank you for flagging the discrepancy. We understand you need to "
        "trust these figures, and we're investigating the mismatch now."
    ),
    "data-request": (
        "Hi {name}, thank you for your request. We're processing it in line with "
        "applicable regulations and will confirm once it's complete."
    ),
    "bug-stability": (
        "Hi {name}, sorry for the disruption this is causing. Our engineering team is "
        "investigating and we'll update you as soon as a fix is available."
    ),
}

DEFAULT_REPLY_TEMPLATE = (
    "Hi {name}, thank you for reaching out. We understand this is impacting your "
    "work and are treating it as a priority. We'll follow up shortly with next steps."
)


def suggested_reply(row: dict) -> str:
    template = REPLY_TEMPLATES.get(row["topic"], DEFAULT_REPLY_TEMPLATE)
    return template.format(name=row["name"])


def build_escalation_email(rows: list, support_lead: str) -> str:
    today = date.today().isoformat()
    critical = [r for r in rows if r["severity"] == "critical"]
    high = [r for r in rows if r["severity"] == "high"]

    lines = [
        f"To: {support_lead}",
        f"Subject: Escalation: {len(critical)} critical / {len(high)} high customer feedback items",
        "",
        f"Hi,",
        "",
        f"{len(rows)} items from today's feedback review ({today}) need attention. "
        "Suggested customer replies are included below for review before sending.",
        "",
    ]

    for severity_label, group in [("CRITICAL", critical), ("HIGH", high)]:
        if not group:
            continue
        lines.append(f"--- {severity_label} ({len(group)}) ---")
        lines.append("")
        for row in group:
            lines.append(f"[#{row['id']}] {row['name']} <{row['email']}> via {row['channel']} on {row['date']}")
            lines.append(f"Topic: {row['topic']} | Sentiment: {row['sentiment']}")
            lines.append(f"Message: {row['message']}")
            lines.append(f"Suggested reply: {suggested_reply(row)}")
            lines.append("")

    lines.append("Please review the suggested replies above before they go out.")
    lines.append("")
    lines.append("Thanks,")
    lines.append("Feedback triage")
    return "\n".join(lines) + "\n"


def build_routine_log(rows: list) -> str:
    today = date.today().isoformat()
    lines = [f"Routine feedback log ({today}) - {len(rows)} items", ""]
    for row in rows:
        lines.append(
            f"[#{row['id']}] {row['date']} | {row['name']} | {row['channel']} | "
            f"sentiment={row['sentiment']} topic={row['topic']} severity={row['severity']}"
        )
        lines.append(f"    {row['message']}")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/output/labeled_feedback.csv", type=Path)
    parser.add_argument("--outdir", default="reports", type=Path)
    parser.add_argument(
        "--support-lead",
        default="<Support Lead Name> <support-lead@example.com>",
        help="Name/email placeholder the escalation email is addressed to.",
    )
    args = parser.parse_args()

    with args.input.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    escalations = [r for r in rows if r["severity"] in ESCALATION_SEVERITIES]
    routine = [r for r in rows if r["severity"] not in ESCALATION_SEVERITIES]

    args.outdir.mkdir(parents=True, exist_ok=True)
    email_path = args.outdir / "escalation_email_draft.txt"
    log_path = args.outdir / "routine_log.txt"

    email_path.write_text(build_escalation_email(escalations, args.support_lead), encoding="utf-8")
    log_path.write_text(build_routine_log(routine), encoding="utf-8")

    print(f"Escalation email draft ({len(escalations)} items) -> {email_path}")
    print(f"Routine log ({len(routine)} items) -> {log_path}")


if __name__ == "__main__":
    main()

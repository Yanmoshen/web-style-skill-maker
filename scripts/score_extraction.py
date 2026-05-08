#!/usr/bin/env python3
"""Score a generated frontend style skill/demo against the production QA gate."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load_scorecard(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"scorecard not found: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("scorecard root must be an object")
    return value


def normalize_dimensions(scorecard: dict) -> list[dict]:
    dimensions = scorecard.get("dimensions", [])
    if isinstance(dimensions, dict):
        output = []
        for key, item in dimensions.items():
            if isinstance(item, dict):
                output.append({"id": key, **item})
        return output
    if isinstance(dimensions, list):
        return [item for item in dimensions if isinstance(item, dict)]
    return []


def validate_independent_review(scorecard: dict) -> list[str]:
    review = scorecard.get("scoring_review")
    if not isinstance(review, dict):
        return ["missing scoring_review metadata from independent final arbiter"]

    errors = []
    arbiter_role = str(review.get("arbiter_role", "")).strip().lower()
    if "final" not in arbiter_role and "arbiter" not in arbiter_role and "08" not in arbiter_role:
        errors.append("scoring_review.arbiter_role must identify an independent final arbiter")

    independent_from = review.get("independent_from", [])
    if not isinstance(independent_from, list) or not independent_from:
        errors.append("scoring_review.independent_from must list the roles this arbiter is independent from")

    evidence_reviewed = review.get("evidence_reviewed", [])
    if not isinstance(evidence_reviewed, list) or len([item for item in evidence_reviewed if item]) < 4:
        errors.append("scoring_review.evidence_reviewed must list source, DOM/CSS, motion/screenshot, and demo evidence")

    if review.get("demo_reviewed") is not True:
        errors.append("scoring_review.demo_reviewed must be true")

    if not str(review.get("judgment_notes", "")).strip():
        errors.append("scoring_review.judgment_notes must summarize the arbiter's independent judgment")

    return errors


def validate_iteration_review(scorecard: dict, total: float) -> list[str]:
    minimum = float(scorecard.get("minimum_score", 9.8))
    if minimum < 9.8:
        return ["minimum_score must be at least 9.8 for the current extraction gate"]

    review = scorecard.get("iteration_review")
    if not isinstance(review, dict):
        return ["missing iteration_review metadata for the 9.8 plus plateau gate"]

    errors = []
    try:
        delta = float(review.get("latest_full_rework_delta"))
    except (TypeError, ValueError):
        errors.append("iteration_review.latest_full_rework_delta must be numeric")
    else:
        if total > minimum and delta > 0.5:
            errors.append("latest full rework delta is above 0.5; continue one more iteration")
        if total <= minimum and delta <= 0.5 and not str(review.get("escalation_strategy", "")).strip():
            errors.append(
                "score is at or below 9.8 with low latest-delta; record iteration_review.escalation_strategy for the next redo"
            )

    if total > minimum:
        if review.get("stop_rule_satisfied") is not True:
            errors.append("iteration_review.stop_rule_satisfied must be true once score is above the release threshold")
    elif review.get("stop_rule_satisfied") is True:
        errors.append("iteration_review.stop_rule_satisfied cannot be true while score is at or below 9.8")

    return errors


def latest_iteration_delta(scorecard: dict) -> float | None:
    review = scorecard.get("iteration_review")
    if not isinstance(review, dict):
        return None
    try:
        return float(review.get("latest_full_rework_delta"))
    except (TypeError, ValueError):
        return None


def compute(scorecard: dict) -> dict:
    dimensions = normalize_dimensions(scorecard)
    total_weight = 0.0
    weighted = 0.0
    missing = []
    failed = []

    for item in dimensions:
        dim_id = str(item.get("id") or item.get("name") or "dimension")
        weight = float(item.get("weight", 1.0))
        score = item.get("score")
        total_weight += weight
        if score is None:
            missing.append(dim_id)
            failed.append(item)
            continue
        score_value = float(score)
        weighted += score_value * weight
        if score_value < 9.0:
            failed.append(item)

    total = weighted / total_weight if total_weight else 0.0
    blocking = [issue for issue in scorecard.get("blocking_issues", []) if issue]
    minimum = float(scorecard.get("minimum_score", 9.8))
    review_errors = validate_independent_review(scorecard)
    iteration_errors = validate_iteration_review(scorecard, total)
    iteration_delta = latest_iteration_delta(scorecard)
    plateau_escalation_required = iteration_delta is not None and total <= minimum and iteration_delta <= 0.5
    passed = total > minimum and not blocking and not missing and not review_errors and not iteration_errors
    return {
        "passed": passed,
        "score": round(total, 2),
        "minimum_score": minimum,
        "iteration_delta": iteration_delta,
        "plateau_escalation_required": plateau_escalation_required,
        "blocking_issues": blocking,
        "review_errors": review_errors,
        "iteration_errors": iteration_errors,
        "missing_scores": missing,
        "failed_dimensions": failed,
    }


def render_markdown(result: dict) -> str:
    lines = [
        "# Release Decision",
        "",
        f"Result: {'PASS' if result['passed'] else 'FAIL'}",
        f"Score: {result['score']} / 10",
        f"Minimum Score: {result['minimum_score']} / 10",
        f"Blocking Issues: {'yes' if result['blocking_issues'] else 'no'}",
        "",
    ]

    if result["blocking_issues"]:
        lines.extend(["## Blocking Issues", ""])
        for issue in result["blocking_issues"]:
            lines.append(f"- {issue}")
        lines.append("")

    if result["review_errors"]:
        lines.extend(["## Independent Review Errors", ""])
        for item in result["review_errors"]:
            lines.append(f"- {item}")
        lines.append("")

    if result["iteration_errors"]:
        lines.extend(["## Iteration Gate Errors", ""])
        for item in result["iteration_errors"]:
            lines.append(f"- {item}")
        lines.append("")

    if result["plateau_escalation_required"]:
        delta = result["iteration_delta"]
        delta_text = f"{delta:.2f}" if isinstance(delta, float) else "unknown"
        lines.extend([
            "## Strategy Escalation Required",
            "",
            f"- Score is at or below {result['minimum_score']} and latest full-rework delta is {delta_text}. This is a strategy plateau, not convergence.",
            "- Do not continue small CSS/text/spacing tweaks as the main fix.",
            "- The next redo must use at least one stronger generic strategy tied to the failed evidence: asset fidelity, runtime visual systems, typography/lettering, interaction/scroll architecture, or component/layout systems.",
            "- Record the selected upgrade strategy, rejected weaker strategy, expected score impact, and verification plan in qa/redo-report.md.",
            "",
        ])

    if result["missing_scores"]:
        lines.extend(["## Missing Scores", ""])
        for item in result["missing_scores"]:
            lines.append(f"- {item}")
        lines.append("")

    if result["failed_dimensions"]:
        lines.extend(["## Failed Dimensions", ""])
        for item in result["failed_dimensions"]:
            name = item.get("name") or item.get("id") or "dimension"
            score = item.get("score", "missing")
            agent = item.get("responsible_subagent", "")
            fix = item.get("required_fix", "")
            evidence = item.get("evidence", "")
            lines.append(f"- {name}: {score}/10")
            if agent:
                lines.append(f"  - Responsible subagent: {agent}")
            if evidence:
                lines.append(f"  - Evidence: {evidence}")
            if fix:
                lines.append(f"  - Required fix: {fix}")
        lines.append("")

    lines.append("Release is allowed only when the result is PASS, the scorecard was completed by an independent final arbiter, the score is above 9.8, and the iteration plateau rule is satisfied. A low-delta score at or below 9.8 requires strategy escalation, not acceptance.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Score a generated frontend style skill/demo.")
    parser.add_argument("--scorecard", required=True, help="Path to qa/scorecard.json")
    parser.add_argument("--out", help="Optional Markdown output path")
    args = parser.parse_args()

    try:
        scorecard = load_scorecard(Path(args.scorecard).expanduser().resolve())
        result = compute(scorecard)
    except Exception as error:
        print(f"score failed: {error}", file=sys.stderr)
        return 2

    markdown = render_markdown(result)
    if args.out:
        out = Path(args.out).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(markdown, encoding="utf-8", newline="\n")
    else:
        print(markdown)

    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Separate stopping events from budget fallback in audited outcome tables."""

import argparse
import collections
import csv
import hashlib
import json
from pathlib import Path

from stoplab.report import interval, write_csv

CONDITION = ("dataset", "query", "noise", "variant")


def identity(row):
    return tuple(row[key] for key in (*CONDITION, "seed"))


def flag(value):
    if value not in ("True", "False", True, False):
        raise ValueError("Expected a boolean stopping flag.")
    return value in ("True", True)


def classify(row, budget):
    """Use trigger status and annotation count, never the hindsight gap alone."""
    value = float(row["labels"])
    if not value.is_integer():
        raise ValueError("Label counts must be integers.")
    labels = int(value)
    if not 0 < labels <= budget:
        raise ValueError("Label count outside the trajectory budget.")
    if row["rule"] == "budget:all":
        if labels != budget or flag(row["stopped"]):
            raise ValueError("Invalid fixed-budget baseline.")
        return "fixed_budget"
    if flag(row["stopped"]):
        return "early_trigger" if labels < budget else "budget_trigger"
    if labels != budget:
        raise ValueError("A fallback must use the final budget.")
    return "fallback"


def failures(rows):
    """Summarize all seeds, including non-triggering rules and baseline models."""
    keyed = {}
    for row in rows:
        key = (*identity(row), row["rule"])
        if key in keyed:
            raise ValueError("Duplicate trajectory outcome.")
        keyed[key] = row
    groups = collections.defaultdict(list)
    for row in rows:
        baseline = keyed.get((*identity(row), "budget:all"))
        if baseline is None:
            raise ValueError("Missing final-budget baseline.")
        status = classify(row, int(float(baseline["labels"])))
        gap = float(row["f1_gap_to_peak"])
        groups[(*identity(row)[:-1], row["rule"])].append((row, status, gap))
    result = []
    for key, members in sorted(groups.items()):
        item = dict(zip((*CONDITION, "rule"), key))
        item["seeds"] = len(members)
        for status in ("early_trigger", "budget_trigger", "fallback", "fixed_budget"):
            subset = [m for m in members if m[1] == status]
            item[status + "_count"] = len(subset)
            mean, low, high = interval([float(m[1] == status) for m in members])
            item.update({status + "_rate": mean, status + "_low": low,
                         status + "_high": high})
            item[status + "_gap_count"] = sum(m[2] > .01 for m in subset)
            item[status + "_gap_rate_conditional"] = (
                sum(m[2] > .01 for m in subset) / len(subset) if subset else None)
        result.append(item)
    return result


def sensitivity(rows, variants, noises):
    """Pair declared replay settings against each stop set's default setting."""
    selected = {}
    defaults = {"sp": .99, "pcf": .01}
    for row in rows:
        if row["variant"] not in variants or float(row["noise"]) not in noises:
            continue
        if row["method"] not in defaults:
            continue
        key = (*identity(row), row["method"], row["stop_set"],
               float(row["threshold"]), int(row["window"]))
        if key in selected:
            raise ValueError("Duplicate replay decision.")
        selected[key] = row
    if not selected:
        raise ValueError("No replay decisions match the requested slice.")
    groups = collections.defaultdict(list)
    for key, row in selected.items():
        baseline = selected.get((*key[:-2], defaults[row["method"]], 3))
        if baseline is None:
            raise ValueError("Missing paired default replay setting.")
        groups[(*key[:4], *key[5:])].append((row, baseline))
    output = []
    for key, members in sorted(groups.items()):
        item = dict(zip((*CONDITION, "method", "stop_set", "threshold", "window"), key))
        item["seeds"] = len(members)
        for metric in ("labels", "macro_f1", "positive_f1"):
            mean, low, high = interval([float(a[metric]) - float(b[metric])
                                       for a, b in members])
            item.update({metric + "_delta": mean, metric + "_low": low,
                         metric + "_high": high})
        item["trigger_rate"] = sum(flag(a["stopped"]) for a, _ in members) / len(members)
        output.append(item)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=Path, required=True)
    parser.add_argument("--replay", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--variants", nargs="+", default=["linear-svm-symmetric"])
    parser.add_argument("--noises", type=float, nargs="+", default=[0, .15])
    args = parser.parse_args()
    with args.runs.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    args.output.mkdir(parents=True, exist_ok=True)
    write_csv(args.output / "failure-modes.csv", failures(rows))
    sources = {"runs_sha256": hashlib.sha256(args.runs.read_bytes()).hexdigest()}
    if args.replay:
        with args.replay.open(encoding="utf-8", newline="") as stream:
            pairs = sensitivity(csv.DictReader(stream), args.variants, args.noises)
        write_csv(args.output / "threshold-pairs.csv", pairs)
        sources["replay_sha256"] = hashlib.sha256(args.replay.read_bytes()).hexdigest()
    sources["failure_scope"] = "All input trajectory outcomes"
    if args.replay:
        sources["replay_scope"] = dict(variants=args.variants, noises=args.noises,
                                       methods=["sp", "pcf"],
                                       reference="same stop set, default threshold, window 3")
        sources["interpretation"] = "Descriptive paired replay. No test-set threshold selection."
    (args.output / "analysis.json").write_text(json.dumps(sources, indent=2) + "\n",
                                             encoding="utf-8")


if __name__ == "__main__":
    main()

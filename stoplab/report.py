"""Seed-level estimates, paired comparisons, and auditable research figures."""

import collections
import csv
import json
import pathlib

import matplotlib
import numpy as np

matplotlib.use("Agg")
from matplotlib import pyplot as plt


def interval(values: list, seed: int = 481) -> tuple:
    """Return mean and percentile bootstrap interval across independent seeds."""
    values = np.asarray(values, dtype=float)
    mean = float(values.mean())
    if len(values) < 2:
        return mean, None, None
    rng = np.random.default_rng(seed)
    means = rng.choice(values, (2000, len(values)), replace=True).mean(axis=1)
    low, high = np.quantile(means, [0.025, 0.975])
    return mean, float(low), float(high)


def write_csv(path: pathlib.Path, rows: list):
    """Write dictionaries with a consistent header."""
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def variant_comparisons(rows: list, reference: str | dict) -> list:
    """Pair variant differences within dataset, policy, noise, rule, and seed."""
    controls = {
        (row["dataset"], row["query"], row["noise"], row["rule"], row["seed"], row["variant"]):
            row for row in rows
    }
    groups = collections.defaultdict(list)
    for row in rows:
        key = (row["dataset"], row["query"], row["noise"], row["rule"],
               row["seed"])
        control_name = reference.get(row["variant"],
                                     row["variant"]) if isinstance(
                                         reference, dict) else reference
        if row["variant"] == control_name or (*key,
                                              control_name) not in controls:
            continue
        control = controls[(*key, control_name)]
        groups[(*key[:-1], row["variant"], control_name)].append({
            "macro_f1": row["macro_f1"] - control["macro_f1"],
            "positive_f1": row["positive_f1"] - control["positive_f1"],
            "labels": row["labels"] - control["labels"],
        })
    comparisons = []
    for (dataset, query, noise, rule, variant,
         control_name), members in sorted(groups.items()):
        row = dict(dataset=dataset,
                   query=query,
                   noise=noise,
                   rule=rule,
                   variant=variant,
                   reference=control_name,
                   paired_seeds=len(members))
        for metric in ("macro_f1", "positive_f1", "labels"):
            mean, low, high = interval([item[metric] for item in members])
            row.update({
                metric + "_delta": mean,
                metric + "_low": low,
                metric + "_high": high
            })
        comparisons.append(row)
    return comparisons


def generate(results: pathlib.Path, output: pathlib.Path):
    """Summarize runs without treating correlated iterations as replicates."""
    from stoplab import replay

    replay.audit(results)
    manifest_data, runs = replay.load_runs(results)
    output.mkdir(parents=True, exist_ok=True)
    groups = collections.defaultdict(list)
    comparisons = collections.defaultdict(list)
    rows = []
    seen = set()
    for run in runs:
        cfg = run["config"]
        condition = (run["dataset"]["name"], cfg["query"], cfg["noise"],
                     cfg["variant"])
        identity = (*condition, cfg["seed"])
        if identity in seen:
            raise ValueError("Duplicate seed within a condition.")
        seen.add(identity)
        by_rule = {row["rule"]: row for row in run["outcomes"]}
        for result in run["outcomes"]:
            row = dict(dataset=condition[0],
                       query=condition[1],
                       noise=condition[2],
                       variant=condition[3],
                       seed=cfg["seed"],
                       **result)
            rows.append(row)
            groups[(*condition, result["rule"])].append(row)
        for method in ("sp", "pcf", "confidence"):
            reference = by_rule[f"{method}:fixed"]
            for stop_set in ("remaining", "easy"):
                other = by_rule[f"{method}:{stop_set}"]
                comparisons[(*condition, method, stop_set)].append({
                    "f1": other["macro_f1"] - reference["macro_f1"],
                    "positive_f1": other["positive_f1"] - reference["positive_f1"],
                    "labels": other["labels"] - reference["labels"],
                })
    summaries = []
    for (dataset, query, noise, variant,
         rule), members in sorted(groups.items()):
        row = dict(dataset=dataset,
                   query=query,
                   noise=noise,
                   rule=rule,
                   variant=variant,
                   seeds=len(members))
        for metric in ("macro_f1", "positive_f1", "labels", "label_savings",
                       "f1_gap_to_peak", "excess_labels", "premature",
                       "stopped"):
            mean, low, high = interval([item[metric] for item in members])
            row.update({
                metric: mean,
                metric + "_low": low,
                metric + "_high": high
            })
        summaries.append(row)
    pairs = []
    for (dataset, query, noise, variant, method,
         stop_set), members in sorted(comparisons.items()):
        row = dict(dataset=dataset,
                   query=query,
                   noise=noise,
                   method=method,
                   variant=variant,
                   comparison=f"{stop_set} minus fixed",
                   seeds=len(members))
        for metric in ("f1", "positive_f1", "labels"):
            mean, low, high = interval([item[metric] for item in members])
            row.update({
                metric + "_delta": mean,
                metric + "_low": low,
                metric + "_high": high
            })
        pairs.append(row)
    write_csv(output / "runs.csv", rows)
    write_csv(output / "summary.csv", summaries)
    write_csv(output / "paired.csv", pairs)
    variants = manifest_data["specification"].get("variants", [{
        "name": "baseline"
    }])
    reference = variants[0]["name"]
    if any("reference" in variant for variant in variants):
        reference = {
            variant["name"]: variant.get("reference", variants[0]["name"])
            for variant in variants
        }
    write_csv(output / "variants.csv", variant_comparisons(rows, reference))
    manifest = runs[0]["manifest_id"]
    expected = runs[0]["expected_runs"]
    lines = [
        "# STOPLAB experiment report", "", f"Manifest: `{manifest}`", "",
        f"Completed trajectories: {len(runs)} / {expected}", "",
        "Each trajectory is shared by all stop rules. Budget fallback is included",
        "in cost/performance averages; `stopped` distinguishes real stops from",
        "right-censored rules. Fixed-budget results are a baseline, not a stop event.",
        "Intervals resample seeds (2,000 bootstrap samples), not iterations.",
        "Small-seed intervals are descriptive, not evidence of superiority.",
        "",
        "| Dataset | Variant | Query | Noise | Rule | Seeds | Macro F1 | Labels | Stops |",
        "|---|---|---|---:|---|---:|---:|---:|---:|"
    ]
    for row in summaries:
        lines.append(
            f"| {row['dataset']} | {row['variant']} | {row['query']} | {row['noise']:.0%} | "
            f"{row['rule']} | {row['seeds']} | {row['macro_f1']:.3f} | "
            f"{row['labels']:.1f} | {row['stopped']:.0%} |")
    lines.extend([
        "", "## Interpretation", "",
        "Inspect paired.csv before attributing differences to stop-set choice.",
        "Test F1 is retrospective evaluation only. The earliest near-peak",
        "point is a hindsight reference on this finite trajectory, not a",
        "deployable oracle or the globally optimal annotation budget.",
        "Annotation noise is simulated according to each variant; test labels remain",
        "clean. Class-conditional rates are conditional flip probabilities, not",
        "overall corruption fractions. This extends rather than exactly replicates papers."
    ])
    (output / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    first = runs[0]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), constrained_layout=True)
    counts = [step["labels"] for step in first["trace"]]
    axes[0].plot(counts, [step["macro_f1"] for step in first["trace"]],
                 color="#186599")
    axes[0].set(xlabel="Queried labels",
                ylabel="Held-out macro F1",
                ylim=(0, 1),
                title="One recorded trajectory (not an aggregate)")
    for stop_set, color in zip(("fixed", "remaining", "easy"),
                               ("#186599", "#ba632a", "#b33579")):
        values = [
            step["statistics"][stop_set]["kappa"] for step in first["trace"]
        ]
        axes[1].plot(counts, values, label=stop_set, color=color)
        outcome = next(item for item in first["outcomes"]
                       if item["rule"] == f"sp:{stop_set}")
        if outcome["stopped"]:
            axes[0].axvline(outcome["labels"],
                            color=color,
                            linestyle="--",
                            label=stop_set)
    axes[1].axhline(first["config"]["kappa"],
                    linestyle=":",
                    color="#555555",
                    label="SP threshold")
    axes[1].set(xlabel="Queried labels",
                ylabel="Consecutive-model kappa",
                title="Stop-set agreement (unsmoothed)")
    axes[1].legend(fontsize=8)
    if axes[0].get_legend_handles_labels()[0]:
        axes[0].legend(fontsize=8)
    fig.suptitle(
        f"{first['dataset']['name']} | {first['config']['query']} | "
        f"seed {first['config']['seed']} | noise {first['config']['noise']:.0%}"
    )
    fig.savefig(output / "trajectory.png", dpi=180)
    fig.savefig(output / "trajectory.svg")
    plt.close(fig)
    return {
        "runs": len(runs),
        "expected": expected,
        "report": str(output / "REPORT.md")
    }

# Research study specification

## Questions

1. Does evaluating stability on the shrinking unlabeled pool change stopping
   cost and held-out performance relative to a fixed random stop set?
2. Can label corruption produce stable predictions before useful performance,
   and do positive-only errors behave differently on imbalanced tasks?
3. Do effects persist across logistic regression and a linear SVM?
4. How sensitive are those conclusions to batch size, stop-set size, and the
   smoothing window? Which apparent improvements disappear under pairing?

These are hypotheses to test, not promised findings. A useful negative result
is that a suspected failure does not occur under a declared protocol.

## Staged execution

| Stage | Configuration | Training trajectories | Purpose |
|---|---|---:|---|
| Smoke | `smoke.json` | 1 | Installation and artifact sanity |
| Pilot | `pilot.json` | 96 | Four tasks, three seeds, two policies, two noise rates, two learners |
| Cluster | `cluster.json` | 5,120 | Four tasks × 20 seeds × two policies × four noise rates × eight variants |
| Sensitivity | `sensitivity.json` | Reuses existing trajectories | 12 thresholds × three windows × three stop sets |

The cluster configuration fixes 40 initial labels, budget 400, and baseline
batch size 20 / stop size 400. Variants change exactly one of learner,
annotation mechanism, batch size (5 or 50), or stop size (100 or 800).
Noise rates are 0, .05, .15, .30. Methods are evaluated on each trajectory,
not retrained separately. The cluster replay would produce 552,960 decisions
from 5,120 training trajectories. Conditions are intentionally paired,
independent seeds, rather than every trajectory or decision, are resampling units.

## Primary comparisons

Report remaining-minus-fixed and easy-minus-fixed SP effects separately for
each dataset, query policy, and noise condition. Report macro F1 difference,
label difference, stopping fraction, and uncertainty together. Retain budget
fallbacks in the main table, report stopping coverage so large savings cannot
hide frequent failures to trigger. Compare PCF as a separate criterion and
report positive F1 alongside macro F1.

Use the first declared variant as the control in `variants.csv`. The cluster
control is `baseline`, the pilot control is `logistic`. Variant effects pair
matching dataset, seed, query policy, noise rate, and stopping rule. Class-only
noise has different overall corruption, avoid interpreting its conditional
rate as equivalent exposure to symmetric noise.

## Confirmatory versus exploratory analysis

The local pilot supports implementation checks and exploratory questions.
It does not establish a new method's superiority. Freeze a separate study
configuration and use new seeds before making confirmatory claims prompted by
pilot findings. For truly held-out confirmation, reserve additional datasets
or a separately specified evaluation split, new seeds on the same text test
documents do not create a new held-out corpus.

Sensitivity replay is a diagnostic, not a threshold tuner. If a new adaptive
stopping method is developed, select its settings on separate development
data and evaluate it on untouched tasks. Preserve the old manifest and report
all predeclared comparisons, including failures and censored outcomes.

## Extension milestones

The implemented release provides the baseline infrastructure. Substantial
follow-on research can add independently validated multiclass generalizations,
human annotation costs, instance-dependent noise, and a development-only
calibration procedure for a new noise-aware criterion. Each extension should
include a mathematical definition, tests, a predeclared comparison, and a
failure analysis before claiming a contribution. None is claimed as implemented.

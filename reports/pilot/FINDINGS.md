# Local pilot findings - 2026-10-13

**Completed and audited:** 96/96 training trajectories, 1,824 fitted models,
960 default-rule outcomes, and 10,368 counterfactual threshold/window decisions.
The automated suite passed 24 tests. The complete run records and machine-readable
tables accompany this report. The current expanded design contains 15,360 trajectories: 8,640 robustness,
4,800 ablation, and 1,920 budget-extension runs. It was submitted on October 14,
2026. This report describes only the completed local pilot.

The pilot spans four tasks, two linear learners, two acquisition policies,
two symmetric annotation-noise rates (0 and 15%), and three seeds per condition.
The class-specific noise and batch/stop-size ablations are implemented and
configured for the larger study, this pilot does not establish their effects.

## What the pilot shows

The easy-set stress condition exposed a useful failure example. For balanced
synthetic data, uncertainty acquisition, linear SVM, and 15% annotation noise,
easy-set SP used 200 fewer labels on average than fixed-set SP, paired across
three seeds, but macro F1 was lower by 0.0522 (5.22 percentage points).
The descriptive bootstrap interval was [-0.1163, 0.0000] for the F1 difference
and [-300, 0] for the label difference. Both intervals include zero. This example
was selected after inspecting the pilot to illustrate a possible trade-off,
it is not a pre-registered significant effect or a universal conclusion.

At the default SP threshold of .99 and a three-pair window, the fixed random
stop set triggered in 8 of 96 trajectories, versus 30 for the remaining pool
and 23 for the initially easy set. Those are descriptive counts across a
heterogeneous matrix, not independent binomial observations or a superiority
test. They show that stop-set choice materially changes how often the rule
triggers within a 400-label budget.

PCF triggered in 10/96 fixed-set, 32/96 remaining-set, and 35/96 easy-set
conditions. Its positive-class target is different from macro F1, examine both
metrics rather than treating the two stopping criteria as interchangeable.

The high fixed-set censoring rate is itself an important result. Budget fallback
is retained in every cost/performance comparison. Reporting savings only among
successful stops would hide this behavior. The threshold replay can explore
coverage versus performance, but choosing thresholds from these test results
would require fresh development/confirmation data before a generalization claim.

## Reproducibility

- Manifest: `3b412e103cbafac213ef40b6e1740ac1ab6c68f6d0cf6207a70fe37380d44413`
- Configuration: `configs/pilot.json`, replay grid: `configs/sensitivity.json`.
- Source, dataset hashes, package versions, and full query histories are saved.
- Summed measured trajectory time: 424.1 seconds, slowest trajectory: 20.8
  seconds on this local Windows machine. These figures exclude dataset loading
  and report generation and are not cluster resource guarantees.
- No source text from 20 Newsgroups is redistributed.

Run `python -m stoplab audit --results results/pilot` to validate the bundled
records. Use a new output directory for a new platform or environment. The
audit checks query hashes, label accounting, and exact replay of stop decisions,
it does not claim to cryptographically authenticate research outcomes.

## Next experiment

Use the supplied cluster protocol to test whether these patterns persist with
30 seeds per main-study condition and 20 per follow-up condition,
class-specific noise, and batch/stop-size changes. The submitted configurations are fixed. Evaluate the annotation-cost and
predictive-performance trade-off before choosing further experiments. New seeds on the same text documents expand
randomness coverage but do not create a new held-out dataset. A genuinely new
stopping criterion should be developed on separate data, then compared under
the same paired protocol with predeclared thresholds and failure measures.

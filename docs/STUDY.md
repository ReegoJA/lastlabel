# Research study specification

## Purpose and origin

This project continues Reego John-Annaselvan's undergraduate research with Dr. Michael Bloodgood at The College of New Jersey. Bloodgood and his coauthors' published stopping methods are the foundation. The study asks when those methods preserve performance while reducing annotation effort, and where additional safeguards may be needed.

## Published foundation and implementation differences

| Choice | Basis |
| --- | --- |
| SP with mean kappa above 0.99 across three model pairs | Bloodgood and Vijay-Shanker (2009), also described in Kurlandski and Bloodgood (2022), section III-A |
| PCF estimate and consecutive threshold checks | Altschuler and Bloodgood (2019), equation 3 |
| Fixed versus current remaining stop sets | Kurlandski and Bloodgood (2022), sections III-A and V-A |
| Linear SVM, C=1, closest-to-hyperplane acquisition, random comparison | Kurlandski and Bloodgood (2022), section IV |
| 20 Newsgroups bydate train/test split | Kurlandski and Bloodgood (2022), section IV |

This implementation differs from the published setup. It uses binary category pairs rather than all 20 categories, pool-fitted TF-IDF with header/footer/quote removal rather than the paper's bag-of-words preprocessing, absolute batch and stop-set sizes rather than 0.5% and 50%, and finite 400/800-label budgets rather than a full-training endpoint. PCF uses epsilon .01 and three pairs here, while the 2019 paper also studies other settings. These choices are documented extensions, not an exact reproduction.

The TCNJ work used small-text. New LastLabel runs use small-text 1.4.1 as their required engine, with the study-specific adapters described in [METHODS.md](METHODS.md#small-text-engine). The original experiment code, library version, and preprocessing assets from the TCNJ work are unavailable. Undisclosed paper details are not inferred as facts.

## Extension rationale

- **Noise mechanisms:** symmetric, positive-only, and negative-only flips test whether stable predictions can hide systematic annotation errors. Rates 0, .05, .15, and .30 are declared stress levels, not estimated human error rates or paper settings. Compare realized corruption as well as nominal rates.
- **Learners:** retain linear SVM and the pilot's logistic baseline. Cross both with each noise mechanism so an apparent noise effect is not confounded with learner choice.
- **Tasks:** retain the two pilot synthetic tasks and two pilot text pairs. Add graphics versus Windows for another closely related technical pair and politics versus religion for a different topic domain. These are new task choices from the same corpus, not independent datasets or the papers' full benchmark suite.
- **Replication:** use 30 seeds in the main study, ten times the pilot's three. Under independent-replicate assumptions, standard error scales roughly with the inverse square root of the seed count. This is a precision-oriented design choice, not a power calculation or guarantee of significance. Follow-up stages use 20 seeds to bound cost. Record achieved interval widths.
- **Batch and stop-set sizes:** change one factor at a time around the pilot's batch 20 and stop set 400. Batch 5/50 and stop set 100/800 test smaller/larger alternatives. They are declared extensions, not values attributed to Bloodgood's papers.
- **Budget:** compare 400 and 800 labels with identical acquisition prefixes. The pilot's high fallback rate motivates asking whether the 400-label ceiling hides later stops. Doubling the budget is a bounded diagnostic, not a claim that 800 is optimal.
- **Easy set and probability confidence:** retain these as exploratory diagnostics. They are not the published SP stop-set recommendation or implementations of DC/NC.

## Stages

| Stage | Configuration | Trajectories | Matrix |
| --- | --- | ---: | --- |
| Smoke | `smoke.json` | 1 | Installation check |
| Completed pilot | `pilot.json` | 96 | Original four-task experiment |
| Robustness | `cluster.json` | 8,640 | 6 tasks x 30 seeds x 2 query policies x 4 noise rates x 6 learner/noise variants |
| Ablations | `cluster-ablations.json` | 4,800 | 6 tasks x 20 seeds x 2 policies x 2 noise rates x 10 learner/setting variants |
| Budget extension | `cluster-budget.json` | 1,920 | 6 tasks x 20 seeds x 2 policies x 2 noise rates x 4 learner/budget variants |

Main seeds are 100-129, ablation seeds 200-219, and budget seeds 300-319. Distinct ranges avoid reusing pilot seeds 0-2. Seed IDs themselves have no scientific significance.

Full threshold replay would produce 1,658,880 correlated decisions from the expanded study's 15,360 trajectories.

## Comparisons and interpretation

Primary stop-set contrasts remain remaining-minus-fixed and easy-minus-fixed within dataset, learner, acquisition policy, noise condition, and seed. Report positive F1, macro F1, labels, stopping coverage, and uncertainty together. Keep budget fallbacks in all averages.

Each expanded variant declares its `reference`. Noise comparisons use the same learner's symmetric-noise control. Ablations use the same learner's baseline. Budget comparisons use that learner's 400-label control. No variant crosses learners accidentally.

Compare the 400- and 800-label runs using paired absolute annotation counts and F1 as well as fractional savings. Savings fractions have different denominators. A larger budget also changes the hindsight peak reference, so premature/excess-label measures are not directly comparable across budgets without a common reference.

Report task-specific results. New seeds on the same text test documents do not create fresh held-out data. Do not pool correlated settings as independent replicates or select thresholds using test results and then claim confirmation on those same results. Label any post-hoc examples or follow-up choices as exploratory.

## Validation and case-study reporting

The expanded configuration was submitted on October 14, 2026. Do not alter its thresholds or comparisons after inspecting outcomes. Audit all stage manifests, task identities, query histories, label counts, and default-rule replays before drawing conclusions.

Use the main study to report remaining-minus-fixed and easy-minus-fixed differences in labels and F1 for each task, learner, policy, and noise condition. Resample matched seeds, not individual stopping decisions. The existing paired tables provide macro-F1 and label-count intervals. Paired positive-F1 intervals were added in the October 15 interpretation pass. Present both axes together rather than ranking policies by stop frequency.

For an interpretable first view, use all 30 seeds from every main-study task under the symmetric-noise linear-SVM variant, with both acquisition policies and the 0 and 15% noise levels. This is a descriptive subset chosen after submission for continuity with the pilot, not a new confirmatory experiment. Disclose it and retain the complete matrix alongside it. Do not select conditions based on their apparent effect size.

Inspect premature stops, budget fallbacks, minority-class degradation, and sensitivity to annotation noise. Explain task-specific exceptions and show representative trajectories with an explicit selection rule. Report uncertainty conditional on these task datasets. Bootstrap intervals are pointwise and do not adjust for the many comparisons, so avoid claims based on isolated intervals excluding zero.

Interpret the cost/performance trade-off before commissioning more runs. Any revised stopping rule or threshold needs separate development and confirmation data. More trajectories alone do not establish a useful stopping policy.

## Computing and reporting

All 15,360 training trajectories completed on October 14, 2026. The main-stage audit and reports are complete. All three stage audits, reports, and threshold replays are complete. Full scientific interpretation is not yet complete. See [CLUSTER.md](CLUSTER.md) for the upload and run procedure and [REFERENCES.md](REFERENCES.md) for the research foundations and software credits.

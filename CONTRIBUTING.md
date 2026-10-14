# Contributing

For bug reports, include the configuration, command, Python version, and traceback. For changes to a stopping rule, include its definition and a small hand-calculated test case.

Install the development dependencies and run the suite:

```sh
python -m pip install -e ".[dev]"
python -m pytest -q
python -m yapf --style .style.yapf --diff --recursive stoplab tests
```

Keep query selection and stopping independent of evaluation labels. Add regression tests for changes to equations, pairing, budget accounting, or result validation. Use new output directories after changing experiment code or configuration.

Document scientific changes in `docs/METHODS.md` and credit their sources in `docs/REFERENCES.md`. Use Conventional Commits, for example `fix: validate stopping thresholds`.

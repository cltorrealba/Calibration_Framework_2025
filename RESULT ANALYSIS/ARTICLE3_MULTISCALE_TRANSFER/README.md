# Article 3 multiscale transfer results

This directory stores immutable, goal-scoped evidence under `runs/<run-id>/`.
Goal 0 runs are deliberately lightweight: configuration, provenance, source
run inventory, checks, logs, report and gate/manifest JSON files only.

Raw data and large source outputs are never copied here. Source locations are
represented by environment-variable locators and repository-relative paths.
No `latest` alias is authoritative; every consumed run must be named explicitly
and approved before a model microbenchmark or later Goal can use it.

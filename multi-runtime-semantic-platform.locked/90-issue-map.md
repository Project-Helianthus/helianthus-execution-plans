# Issue Map

The canonical issue map is `92-m0-issue-matrix.yaml`. It contains the exact row ID,
repository owner, milestone, acceptance criteria, gates, rollback intent, and `depends_on`
list for each of 75 rows.

The hash-free golden in `tests/golden/msp-dependency-graph.yaml` protects the exact 101
edges. It does not determine readiness. An agent must reconcile the corresponding GitHub
issue and PR before choosing a row.

Historical accepted evidence and detailed amendments are available under
`multi-runtime-semantic-platform-history.draft/` for investigation only.

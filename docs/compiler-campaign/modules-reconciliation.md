# Modules reconciliation

Merge checkpoint: main `f46490a8`, including nest `363ea67a`, into
`campaign/modules` at `7ac90164`. Both gate registries and law families are
retained. Census policy takes both feature inventories, then regeneration
records the actual merged sources. Shared receipts retain main's bytes.

Verified at the merge checkpoint: seed proof entries `PROOF`, `catalog-PROOF`,
`check-PROOF`, `matrix-PROOF`, `fields-PROOF` all print `All terms check.`;
`gates:verify` runs 22 tests, OK; census regenerates 49 compiler files and
1,372 declaration occurrences (1,081 unique).

This checkpoint is intermediate. Full gates are unrun. Required next steps:
remove the dotted-binder parser stopgap and amend conflicting pins under D26;
freeze detached-brace and empty-datatype probes; align Base Empty; probe and
repair qualification of matrix nodes; re-express affected mutants without
changing their witnesses; run all deterministic gates. Live Perch and shared
receipt refresh belong to the coordinator.

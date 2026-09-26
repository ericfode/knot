# Compiler-support package campaign

The user requested separate build chats for the six priority packages, ongoing
Perch improvements, strong non-vacuous laws, and publication to Bend's package
repository when complete. These actions are authorized. Do the work through
verified publication; do not stop at a design or ask again for routine approval.

Read `docs/PACKAGE-CAMPAIGN.md`, `docs/LAW-QUALITY-GATE.md`, the stdlib inventory,
and the local Perch skill. The project is Bend 2 with direct self-hosting and a
required GPU execution path for its supported subset; the compiler may bootstrap
on CPU. A package's claimed backend support must match observed evidence.

Each chat owns exactly its `packages/<name>/` subtree and its dedicated
`.perch/rules/package_<name>.yaml`. All chats use the same checkout. Never switch
branches, reset/stash, stage the whole tree, edit another package, or commit
another chat's work. Root tooling and shared rules belong to the coordinator.
Do not publish sibling packages as accidental dependencies or copy their source
to bypass a dependency. Read their `INTERFACE.md` and `STATUS.md`; record exact
dependency hashes and use published content hashes for release.

Publish original package code with an explicit MIT-0 license, matching the hub's
default. Preserve licenses and notices for any incorporated third-party source;
do not relicense copied upstream code. Package names/aliases may be chosen by the
owner; use underscore filesystem paths. Content-hash publication needs no named
account login, so do not start a login flow just to attach a friendly name.

Use the shared pinned `scripts/bend-reference` and per-package build/output
directories. Publish `INTERFACE.md` early to make dependent work possible. Continue
independent spec/model/law work when a dependency is unfinished. Source, tests,
models and proofs must live in Bend; host scripts may build, drive experiments,
compare receipts and publish, not implement package semantics.

Keep laws meaningful and publish their evidence. Follow the shared law gate,
add calibrated package-specific Perch rules as mistakes are discovered, and state
when provider credentials prevent live calibration. Do not count a model verdict
as proof. Do not fabricate a universal theorem from finite examples.

The package is finished only after its promised behavior, semantic mutation
tests, applicable performance checks, proof boundary, publish closure, and fresh
remote consumer have been verified. Leave precise blockers and runnable commands
in STATUS.md if an external condition prevents completion.

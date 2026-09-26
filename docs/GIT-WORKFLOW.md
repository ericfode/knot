# Git checkpoints

Completed work belongs in reviewable commits. This checkout is shared by several
chats; a clean checkpoint does not require disturbing work still in progress.

1. Read `git status --short --branch` and the recent log before editing. Inspect
   the existing staged and unstaged changes. Identify the paths owned by this
   increment and preserve all others.
2. Finish one coherent increment. Run the relevant deterministic gates and the
   targeted Perch checks required by `AGENTS.md`. Existing evidence may be used
   only when it matches the sources being committed; distinguish historical
   evidence from checks rerun now. A documentation or Git hygiene change does
   not justify rerunning unchanged paid model reviews.
3. Stage explicit paths. Inspect `git diff --cached --stat`,
   `git diff --cached --check`, and the staged content. Check new files for
   credentials, dependency directories, caches, unintended binaries, and large
   artifacts. Preserve intentional generated examples and receipts; never edit
   recorded evidence solely to silence a whitespace diagnostic.
4. Commit with a message describing the resulting behavior or checkpoint state.
   Record material verification limits in the commit body or the increment's
   evidence document. Incomplete work may be checkpointed, but cannot be called
   implemented or verified without the corresponding evidence.
5. Inspect `git status --short --branch` and `git log -1 --oneline`. Report the
   commit ID and any remaining work. If another chat writes during staging,
   inspect that difference; do not repeatedly sweep its in-progress work into
   the commit. Coordinate a later checkpoint when authorized.

Never reset, stash, force-push, or change branches in the shared checkout to make
the status look clean. Do not amend another chat's commit. Local commits do not
imply a remote push; publishing requires the applicable user authorization.

The 2026-09-26 request to commit everything permits the initial repository-wide
checkpoint across existing ownership boundaries. It does not transfer package
ownership or make every future concurrent edit part of the coordinator's work.

# Refresh round: bring a reviewed branch up to current main

This branch was reviewed on 2026-09-27 and is waiting in the merge order: nest → modules → descent-2 → closures → literals-integ → generics → VM track. Main has moved since then: decisions D22–D26, gate-runner changes (a 1,800 s per-gate limit, the clang wrapper and a retry), prechecks, and the calibrated Perch rules.

1. Merge `main` (5571625f or later) into the branch with a merge commit, never a rebase.
   - Resolve every conflict so that both sides' intent survives.
   - For shared receipts of other gates, keep main's copy; the coordinator refreshes them.
   - Regenerate the census inventories (`npm run census:approve`, then `npm run census`) instead of hand-merging them, and paste the approval summary into the commit message.
2. Run `npm run -s gates`. Fix whatever the merge broke, without weakening any frozen expectation, law or mutant. Freeze from the seed first where a new expectation is needed (D7).
3. Read docs/COMPILER-CAMPAIGN.md (D1–D26) and docs/compiler-campaign/COORDINATOR-STATE.md on main. Check whether any decision made since this branch's last review changes its obligations:
   - D21: an open law stays required and must be recorded.
   - D24: a Default arm.
   - D26: this branch's pins that nest's frozen suites pin differently. List them with the verdict D26 selects; nest merges first.

   Address what is yours. List what belongs to the merge.
4. Probe this branch's own feature against the pinned seed with 20 or more new edge programs. Freeze any false acceptance or false Invalid you find, and fix it.

Report every gate's exact counts, what the merge changed, and every D26 item.

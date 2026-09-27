# Ten-round continuation

The user authorized a second phase after the original paired experiment:
preserve the original versions, then let both original author agents use Perch
feedback for up to ten rounds each. This phase changes the search procedure; it
does not rewrite the original one-shot experiment or its results.

## Fixed boundaries

- Continue the same author contexts, GPT-6 Astra at max reasoning. Retain each
  arm's original reading condition. No cross-arm inspection or communication.
- The public behavior in ../CONTRACT.md, independent gates, compiler, source
  rules, style rubric, cohort text and thresholds are unchanged. Its one-shot
  generation restriction is superseded only for this separately recorded phase.
- Original arms, snapshots, receipts and reports are read-only. Explicit source
  copies are in originals/; preserve.json records hashes of the entire original
  experiment and frozen inputs. Work only under the assigned iteration arm.
- The author may read its own baseline-style.json and baseline-semantic.json,
  the shared protocol and runner, and the references permitted by ../AUTHOR.md.
  The author may now invoke the common round runner and inspect its own outputs.
  Do not inspect the oracle implementation, fixtures, other arm, paired result
  report, other chats, memory, network sources or bend-tests. Behavior failures
  may be read from that arm's generated receipts; never tailor code to fixtures.
- No configuration, threshold, rule, evaluator or dependency changes. No hidden
  helpers, foreign code, unsafe constructs, special-case fixtures or self-praise
  aimed at the judge. A structural change must improve the actual reading
  experience. Fewer declarations alone is not a reading hypothesis.

## One round

1. Create round-01 through round-10 sequentially. Write hypothesis.md before
   editing: name the reading problem, proposed mechanism and correctness risk.
   Copy the prior candidate, or explicitly explain a fresh design, into life.bend.
2. Before the first local compiler check, save first.bend.snapshot. Retain full
   commands, stdout, stderr and exit status. At most one compiler-diagnostic
   repair and retry is permitted within the round. Keep any repaired snapshot.
   If still rejected, submit the failure and move to the next numbered round.
3. Run from the repository root:

       python3 research/life-blueberry/iteration/evaluate-round.py arm-a 1

   Substitute only the assigned arm and round number. The runner freezes the
   submitted source, runs the unchanged full behavior gate, then the targeted
   semantic rules and full-file three-axis style review. It uses neutral paths,
   retains commands and complete feedback, and reuses only hash-matching ratings.
   A compiler/runtime failure still consumes a round; no paid style check follows
   a deterministic failure. Never edit a submitted round or rerun it for luck.
4. Read feedback and write disposition.md, including confirmed, false-positive,
   duplicate or unresolved semantic findings with evidence. Preserve complete
   probability distributions and uncertainty. Send a short update to the parent.
5. Stop at the first complete pass, or after ten rounds. A pass requires unchanged
   deterministic gates, complete current Perch coverage, every declaration at all
   three style targets, and no unresolved semantic finding. No threshold finding
   is not a proof. If a provider fails, retain the failure and notify the parent;
   do not repeatedly retry an unavailable credential.

At completion write SUMMARY.md and selection.json in your assigned arm directory.
Record rounds used, selected round, source hash, whether the full bar was met,
all three axis counts, reading changes, semantic dispositions and remaining limits.
If no full pass exists, select a behavior-correct candidate with a stated reading
reason and label the unmet bar. Do not overwrite original life.bend or commit;
the parent owns integration, the final bounded law packet, and Git checkpoints.

Both arms have the same ten-round budget and feedback rules. Adaptive repeated
selection is not an independent replication or evidence of a causal exposure
effect. The original frozen results remain the baseline.

# Rubric v8 selection and acceptance (written before any candidate was scored)

Date: 2026-09-27. Judge: jev-1.13.0 via the production style path (runStyleRanking --live,
one isolated workspace per rendering, task contract supplied). Metric: analyze.py
"overall" = mean of declaration compression, declaration delight, composition memetic,
composition anticipation, composition payoff (normalized expected scores); a human
preference pair agrees when the preferred rendering's overall is higher by more than
0.01 (measured test-retest noise: max 0.007); within 0.01 counts half.

Baseline v6: dev pairs 17.5/34 (51%), dev duels 5.5/12 (46%); held-out pairs 13/25 (52%),
held-out duels 3.5/9 (39%); all duels 9/21 (43%).

Split: dev = bitpath, fuel (drafters saw only these anchors and renderings);
held-out = pipeline, slots (never shown to drafters; judged once per finalist).

Selection on dev: highest dev duel agreement; tie -> higher dev all-pairs agreement;
tie -> smaller rubric. At most one refinement round, still on dev only.

Held-out acceptance for adopting v8 as the production rubric:
  held-out duels >= 7/9 AND held-out all-pairs >= 19/25 (76%), AND dev duels >= 10/12.
If the finalist fails, it is not adopted automatically; results go to the user.

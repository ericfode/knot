# Taste duel: polarized renderings for human anchors

The user rated 18 real Knot declarations on an earlier anchor page, and all 18
came out "generic". The repository's code is too uniform to provoke a
preference. This set asks for an opinion by rendering the same behavior in six
deliberately opposed styles.

Page: <https://claude.ai/artifact/2R2TKB7uZwvH9oHhe8r4w1>. It is private to the
user. Answers are saved to its database, in collection `responses`:

| Document | Contents |
| --- | --- |
| `lineup-<task>` | a reaction per card, plus the best and worst pick |
| `d1` … `d9` | duel scores from −2 to 2, with reason chips; `d9` is `d1` with sides swapped |
| `final` | two free-text answers |

Read them back with the Artifact data tool, never by retyping.

## The set

There are four tasks drawn from Knot's recurring motifs, and six renderings of
each task:

| Task | Motif |
| --- | --- |
| `bitpath` | walk a bit path; one walk, two endings |
| `fuel` | give work its fuel; the unfinished future returned |
| `pipeline` | stop at the first error |
| `slots` | refusal returns the offer |

The six styles:

| Style | Pole |
| --- | --- |
| `deadpan` | maximally plain |
| `algebra` | one small idea absorbs every case |
| `mythic` | invented vocabulary and rhythm |
| `baroque` | deliberate ornament and ceremony |
| `golf` | compressed to cryptic |
| `literate` | a narrated story |

Each task was written by one agent and then pushed further by a separate
extremity critic. Every rendering was freshly recompiled with the pinned
Bend 2.0.29 compiler (`574b6d3`) and parses with the style parser. It also
passes 64 of 64 probe runs against an independent JavaScript oracle
(`oracle.mjs`, driven by `check.mjs`). Only the part above
`# ---- harness (not shown) ----` appears on the page.

The files are stored as `.bend.snapshot` so that style discovery never sends
them to the judge; they remain unseen, held-out controls. `mapping.json` holds
the opaque card ids, the task order and the duel plan. The page shows no style
names until the viewer asks for the reveal at the end.

## Reproduce

```sh
# Recompile a task and rerun its probes (pinned toolchain in the main checkout).
mkdir -p /tmp/duel/bitpath
for p in deadpan algebra mythic baroque golf literate; do
  cp bitpath/$p.bend.snapshot /tmp/duel/bitpath/$p.bend
  (cd /Users/ericfode/src/knot && bun tests/perch-performance/compile.ts /tmp/duel/bitpath/$p.bend /tmp/duel/bitpath/$p.mjs)
done
(cd bitpath && node check.mjs /tmp/duel/bitpath)

# Rebuild the published page and mapping byte for byte.
python3 build.py summaries.json /tmp/page.html /tmp/mapping.json
```

## Limits

- **Not a judge calibration.** These are taste probes for the user; no model
  has rated them.
- **Probes are finite.** 64 probe runs per rendering do not prove general
  equivalence.
- **Guideline overruns.** Some renderings exceed the ~70-line target
  (bitpath deadpan 77, baroque 79), and a few long lines may wrap.
- **Shared structure.** Several renderings implement delete as writing an
  empty value, and some rebuild through a similar collapse step. Their
  surfaces are far apart, but their structures are not fully independent.

## Round 1 answers (2026-09-27)

[`round1-responses.json`](round1-responses.json) exports the raw database
documents and decodes them with `mapping.json`. It covers four lineups and
nine duels between opposite styles. The final free-text answers were not
given.

**Lineups.** A dash means the card was not rated.

| Task | deadpan | algebra | mythic | baroque | golf | literate |
|---|---|---|---|---|---|---|
| bitpath | meh | **more, best** | meh | much, worst | much | much |
| fuel | meh | **more** | meh | much | much | meh |
| pipeline | meh | — | — | much, worst | much | **more** |
| slots | meh | **more** | meh | much | much | much |

**Duels.** The winner and the strength of the preference:

| Duel | Task | Result |
|---|---|---|
| d1 | bitpath | deadpan over mythic (slight) |
| d2 | bitpath | algebra ≫ baroque |
| d3 | fuel | mythic ≫ baroque |
| d4 | fuel | literate ≫ golf |
| d5 | pipeline | algebra ≫ mythic |
| d6 | pipeline | literate ≫ deadpan |
| d7 | slots | algebra ≫ golf |
| d8 | slots | baroque ≫ literate |
| d9 | bitpath | deadpan ≫ mythic (repeat of d1 with sides swapped; same direction, stronger) |

Readings. These are interpretations of one person's round, not a calibrated
model:

- Algebra won every duel it was in and was the "more" pick wherever rated. A
  single idea that absorbs the cases, with its laws stated, is the anchor.
- Invented vocabulary and rhythm (mythic) did not pull: it lost to deadpan
  twice. It beat only the deliberately ornamental baroque. This directly
  informs the v6 memetic axis, whose Contagious and Generative levels reward
  exactly that kind of hook.
- Compression pushed into obscurity (golf) and ornament (baroque) were
  rejected wherever they faced anything else. Baroque's one win was over the
  slots literate rendering.
- Narration is context-dependent. The pipeline literate rendering poses a
  puzzle and resolves it at the end; it won "more" and beat deadpan strongly.
  Literate renderings without that shape were "too much", and slots literate
  lost even to baroque. This bears on the Anticipation and Payoff axes: a
  setup that pays off may be valued, while prose volume is not.

Round 2 replaces the duels with single-factor ablations of the preferred
renderings. It asks which part of algebra carries the preference, and whether
the pipeline's puzzle setup and payoff, rather than prose volume, is what
makes that literate rendering work.

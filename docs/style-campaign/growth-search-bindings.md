# Growth, search and binding updates

Three first candidates are accepted as implementation improvements with style
debt: Vec `cd78dba`, Source `7bfae7e`, and compiler scope `9680908`.
None required a compiler-diagnostic retry. No package was republished, dependency
identity changed, independent assertion weakened, or historical failure erased.
None of the reviewed declarations meets all three style targets.

## Source: terminal states ignore fuel

Search previously repeated both terminal states for zero and successor fuel.
The accepted cases make their invariant visible:

```bend
  match fuel pair:
    case _ Tuple{lines,Found{line}}: (lines,Found{line})
    case _ Tuple{lines,BadIndex{}}: (lines,BadIndex{})
    case 0n Tuple{lines,Searching{lo,hi}}: (lines,BadIndex{})
    case 1n+f Tuple{lines,Searching{+lo,+hi}}:
      search(f,pos,search_step(lines,lo,hi,pos,U32.is_le((hi - lo : U32),1)))
```

Only pending search consumes fuel. The affine line store, interval arithmetic,
public results and failure behavior stay fixed. Compression target mass moves
0.38 → 0.56 (uncertain), delight 0.57 → 0.65 (meets), and memetic identity
0.31 → 0.33 (below). Neighbour regressions remain visible; there is no claim of
a family-wide style gain. The five-unit distributions are compression 2/1/2,
delight 4/0/1, memetic 0/5/0 (meets/below/uncertain).

Proof/type/quantity, native/JS conformance, malformed scalars, the preregistered
terminal-state probe, eleven semantic mutants and scaling through 131,072
scalars passed. An initial 26% JS slowdown did not reproduce in eight
alternating-order pairs (ratio 1.00224). Raw measurements remain; no speedup or
universal performance equivalence is claimed.

Semantic review completed 18 checks for the final source/packet. A local review
corrected a foreign-ID rejection claim that the first packet review missed:
`Source.locate` takes a position, not a cursor. Including that retained first
review, usage was 26 checks over three complete responses. A clean judgment
does not establish packet accuracy.

[Owner report and before/after receipts](../../packages/source/STYLE_CAMPAIGN.md)
and [coordinator verification](source-search-1-verification.json).

## Compiler: one metadata-preservation rule

`refine` and `replace` previously repeated the binding traversal and complete
record reconstruction. A closed template now owns that invariant; the wrappers
state the distinction:

```bend
def refine(bindings: List<&2,C.Binding>, +level: U32, +tag: U32) -> List<&2,C.Binding>:
  set_known(~U32,~(tag => token => type_id => C.Value{token,type_id,tag}),bindings,level,tag)

def replace(bindings: List<&2,C.Binding>, +level: U32, +term: C.Term) -> List<&2,C.Binding>:
  set_known(~C.Term,~(term => token => type_id => term),bindings,level,term)
```

The added call is justified by one shared preservation rule. Every matching
identity, including duplicates, is updated; order and unrelated metadata remain
unchanged. Independent baseline/candidate native/Bun evidence covers 54,720
complete records across 28 runs. Five existing regression suites and 34 semantic
mutants pass, with zero-hole trust inventories and unchanged generated Wasm
modules. This does not establish general self-hosting or a traversal speedup.

All three family declarations meet compression and delight and remain below
memetic identity. Refine memetic target mass moves 0.17 → 0.34; replace moves
0.10 → 0.33. Their small delight changes are weak preferences. The new shared
helper scores 0.96/0.77/0.15. The separately reviewed 18-declaration observer
also retains all deficits: compression 7/8/3, delight 9/3/6, memetic 0/16/2.
Semantic coverage is nine family checks and 36 observer checks, without findings.

[Owner report](../../research/compiler-style/STYLE_CAMPAIGN.md) and
[coordinator verification](compiler-family-1-verification.json).

## Vec and verification boundary

[Vec's report](vec-growth-1.md) retains the useful continuation rule and its
tradeoff: planner compression rose 0.78 → 0.90 while delight fell 0.61 → 0.52,
becoming uncertain. All twelve memetic results remain below or uncertain.

The coordinator checked frozen inputs and recorded execution outcomes,
regenerated current style request states without provider calls, and compared
the compiler's retained outputs with its fixed independent oracle. Owner
compilation and execution were not rerun. Parser context limits, full probability
distributions and model identities remain in the linked receipts.

The refreshed inventory retains new, stale, unranked and empty specimens. Its
dated baseline comparison is separate from these targeted receipts. Symbols is
next in the queue; the one-new-batch limit for this wake is already used by Source.

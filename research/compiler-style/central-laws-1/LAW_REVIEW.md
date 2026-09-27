# Five checker boundary laws

This packet covers only empty_sequence_preserves_uses, repeated_affine_level,
live_erased_occurrence, erased_occurrence_preserves_identity and
refined_constructor_is_fresh. The original quantified domains, quantities,
propositions, identifiers and normalization proofs are preserved. The candidate
changes equation layout only. These are helper/boundary equations, not a theorem
that the checker is sound, complete or adequately specified for every program.

## Fixed contract and domains

# Fixed five-law contract

The subject is the existing helper/boundary law family of the enum-profile
checker. Express the following exact observations and retain their proof bodies.
This is not a checker soundness or specification-completeness theorem.

1. For every reusable list of U32 uses and every syntax token, sequencing an
   empty list before uses returns Done of that same list. No validity or
   distinctness precondition is imposed on uses.
2. For every reusable syntax token, sequencing the two literal lists [0] and
   [0] returns Invalid(check, affine-reuse, at(token)). The domain is not
   generalized to arbitrary overlapping lists.
3. For every reusable token and every U32 level and type_id, an unknown
   occurrence with quantity zero in a live position fails with
   Invalid(check, erased-live, at(token)).
4. For every token and every U32 level and type_id, the same unknown quantity-zero
   occurrence in an erased position returns Checked(Reference(token, level,
   type_id), type_id, empty uses). Identity is retained.
5. For every token, type_id and tag, a known Value(token, type_id, tag) used at
   level zero, quantity one, in a live position returns that checked value with
   type_id and empty uses. It does not consume an old affine reference.

The exact quantified domains, quantities, propositions, error locations, public
identifiers and original normalization proofs are fixed. Preserve compiler
behavior and all literal independent observations. No extra assumptions, axioms,
wrappers, additional law claims or implementation change are required.

All domains are inhabited: S.Token{"x",S.At{0,1,1,0}}, U32 words 0 and 1,
and both empty and nonempty lists (for example [4,7]) are ordinary constructors.
There are no antecedents, additional assumptions, holes, new axioms or unsafe
inhabitants. The second equation fixes both input lists to [0] and quantifies
only token; it is not an arbitrary-overlap theorem. The quantities shown below
are the exact original annotations.

## Statements and original proof bodies

```bend
import Base
import ./syntax.bend as S
import ./core.bend as C
import ./scope.bend as E

law empty_sequence_preserves_uses:
  for +uses: List<&2,U32>
  for token: S.Token
  {E.sequential(Nil{},uses,token)
   == Done{uses}
   : Result<S.Error,List<&2,U32>>}

law repeated_affine_level:
  for +token: S.Token
  {E.sequential([0],[0],token)
   == Fail{S.Invalid{"check","affine-reuse",S.at(token)}}
   : Result<S.Error,List<&2,U32>>}

law live_erased_occurrence:
  for +token: S.Token
  for level: U32
  for type_id: U32
  {E.occurrence(None{},token,level,0,type_id,True{})
   == Fail{S.Invalid{"check","erased-live",S.at(token)}}
   : Result<S.Error,C.Checked>}

law erased_occurrence_preserves_identity:
  for token: S.Token
  for level: U32
  for type_id: U32
  {E.occurrence(None{},token,level,0,type_id,False{})
   == Done{C.Checked{C.Reference{token,level,type_id},type_id,Nil{}}}
   : Result<S.Error,C.Checked>}

law refined_constructor_is_fresh:
  for token: S.Token
  for type_id: U32
  for tag: U32
  {E.occurrence(Some{C.Value{token,type_id,tag}},token,0,1,type_id,True{})
   == Done{C.Checked{C.Value{token,type_id,tag},type_id,Nil{}}}
   : Result<S.Error,C.Checked>}

import Base
import ./check-LAWS.bend as L

def L.empty_sequence_preserves_uses(uses,token):
  {==}
def L.repeated_affine_level(token):
  {==}
def L.live_erased_occurrence(token,level,type_id):
  {==}
def L.erased_occurrence_preserves_identity(token,level,type_id):
  {==}
def L.refined_constructor_is_fresh(token,type_id,tag):
  {==}
```

## Implementations reached by the laws

```bend
def contains(ids: List<&2,U32>, +id: U32) -> Bool:
  match ids:
    case Nil{}: False{}
    case Con{h,t}: Bool.or(U32.is_eq(h,id),contains(t,id))

# Only live affine occurrences enter these sets. Sequential sets must be
# disjoint; alternatives take their union. No machine counter can wrap.

def sequential(xs: List<&2,U32>, +ys: List<&2,U32>, +token: S.Token) -> Result<S.Error,List<&2,U32>>:
  match xs:
    case Nil{}: Done{ys}
    case Con{+h,+t}:
      S.choose(Result<S.Error,List<&2,U32>>,contains(ys,h),u => C.invalid(List<&2,U32>,"affine-reuse",token),u =>
        S.bind(List<&2,U32>,List<&2,U32>,sequential(t,ys,token),rest => Done{Con{h,rest}}))

def occurrence(known: Maybe<&2,C.Term>, +token: S.Token, +level: U32, +q: U32, +type_id: U32, +live: Bool) -> Result<S.Error,C.Checked>:
  match known:
    case Some{C.Value{origin,source_type,tag}}: Done{C.Checked{C.Value{token,type_id,tag},type_id,Nil{}}}
    case Some{other}: C.internal(C.Checked,"compound-refinement")
    case None{}:
      S.choose(Result<S.Error,C.Checked>,Bool.and(live,U32.is_eq(q,0)),u => C.invalid(C.Checked,"erased-live",token),u =>
        Done{C.Checked{C.Reference{token,level,type_id},type_id,S.choose(List<&2,U32>,Bool.and(live,U32.is_eq(q,1)),u => [level],u => Nil{})}})
```

C.invalid constructs Fail{S.Invalid{"check",code,S.at(token)}}. S.choose uses
the indicated Bool to call one thunk; S.bind propagates Fail and otherwise
applies its continuation. C.Checked retains the term, type ID and list of
live affine uses. The supplied scope helpers are unchanged. S.Token and
S.At retain source text and location. Runtime source remains outside this diff.

## Observation coverage and adversarial review

| Law | Observation | Limit |
| --- | --- | --- |
| empty_sequence_preserves_uses | Full returned list, including contents/order | Empty left input only |
| repeated_affine_level | Exact error code and source location | Literal overlap at level zero |
| live_erased_occurrence | Exact failure for quantity zero in a live position | No theorem about all quantities |
| erased_occurrence_preserves_identity | Reference token/level/type, checked type and empty uses | Unknown erased occurrence only |
| refined_constructor_is_fresh | Value token/type/tag and empty uses | Selected known-value domain only |

A constant empty successful result violates the first law for nonempty uses.
Accepting quantity-zero live references violates the third law. Dropping the
reference identity while erasing violates the fourth law; adding an affine use
to the known value violates the fifth law. These are source-level hostile
counterexamples, not newly executed mutants. The original compiler checker gate
retains seven executed type-valid mutants and independent literal program
observations. Its mutation outcomes are not claimed as separate mutation
coverage of every selected equation.

## Deterministic evidence

The candidate compiled first-shot with no diagnostic retry. verification.json
checks identical lexical tokens for the complete law file, identical proof
bytes, and unchanged unselected law blocks. All five src proof entry points
returned All terms check. The existing tests/compiler-checker/check.py was
imported unchanged; only BUILD and RECEIPT destinations were redirected. It
passed 49 reference fixtures, 98 native/Bun observations, 10 depth observations,
16 catalog-bound observations, and all seven type-valid semantic mutants.
The literal expectations and mutation definitions were frozen before authorship.
No host implementation of the compiler, new proof claims or new behavior tests
were introduced. Finite observations and normalization proofs remain distinct.

The exact five-law/proof review projection removes unused checker/frontend
imports only; all theorem/proof blocks are exact source excerpts, and supplied
implementation modules are byte-identical. The full original source entry was
checked separately. Whole-file style context can include unrelated laws and
needs its own coverage disclosure.

## Input identities

- `src/check-LAWS.bend`: `9acd7671abffbc0e874485cf87b88d38bc39f9f75c5681c8ad303ef6ea158c52`
- `src/check-PROOF.bend`: `2fe6bce9d7f4e03042794864e8249ffbd2e9b0d4824453f633b4483ac8bf0a9d`
- `src/scope.bend`: `9581c3922f9d027e67b6b0a054b99b6b7b4062f59c3a0c72f9e7e3f1ea522dfd`
- `src/core.bend`: `eea976a956241715c1056fdbe4b3f3c6b4e4734a85fa3feb488629c203d7e973`
- `src/syntax.bend`: `94806a94dae794f5e83a82537c1e8b4b066bac14430a116027ec9f49f21bc5b1`
- `tests/compiler-checker/check.py`: `27ede49b2e14b5dcc8e9d1c18fd00852a80660db1b4851b6dc475695b5fcafda`
- `tests/compiler-checker/cases.json`: `bc7b249e2cb2a12e35dc52e08d2a94c025d6cb2bf7c7edefa665b325870e0456`

# Count admission and ordered byte joins — candidate packet

Scope: output-builder-grammar-1, an unreleased working revision. Public signatures
and INTERFACE/SPEC, laws, proof terms, independent list models, conformance and
performance assertion bodies are unchanged; frozen hashes are in invariants.json.
Text emit and byte emit remain emit(left,emit(right,suffix)); no byte/Char codec.

Public byte contracts: empty(cap), fragment(cap,bytes), append(b,bytes), byte(b,x),
compose(left,right), length(b), limit(b), finish(b). Exact ordered U32 lists in
0..255; stored length equals emitted length <= retained left cap. append validates
first encountered byte, then room at that byte, returning first error and no
partial builder. Empty append succeeds at capacity. Retained old builders remain
unchanged on success and failure. compose checks right.length <= left.cap-left.n
before addition; sufficient intermediate capacity is required for associativity.
Raw constructors and helpers require the established representation invariant.
No indices, fuel, identifiers, Array growth or effectful core are introduced.

Concrete implementation delta (all other source is unchanged):

```bend
# The admitted count must describe the suffix and fit the builder's room.
def join(admitted: Result<Error,U32>, builder: Builder, suffix: Tree) -> Result<Error,Builder>:
  match admitted builder:
    case Fail{err} Buffer{cap,n,prefix}:
      Fail{err}
    case Done{k} Buffer{cap,n,prefix}:
      Done{Buffer{cap,U32.add(n,k),Join{prefix,suffix}}}

def attach(result: Result<Error,U32>, b: Builder, values: List<&2,U32>) -> Result<Error,Builder>:
  join(result,b,Chunk{values})

def combine(ok: Bool, cap: U32, left_n: U32, right_n: U32, left: Tree, right: Tree) -> Result<Error,Builder>:
  join(guard(ok,Limit{},u => Done{right_n}),Buffer{cap,left_n,left},right)
```

Supporting flow: append(Buffer(cap,n,t),values) calls
attach(scan(values,cap-n,0), Buffer(cap,n,t), values). scan returns Done(count)
for Nil; on Con(h,t), guard(h<=255,InvalidByte(h), then guard(count<room,Limit,
then scan(t,room,count+1))). guard evaluates next(Unit) only for True.
compose(Buffer(cap,n,a),Buffer(other,m,b)) calls
combine(m<=cap-n,cap,n,m,a,b). Thus the count reaches join only after admission.
The new helper does not promise to validate arbitrary forged count/tree pairs.

Independent model: ordered lists of byte lists, flattened with right-associated
Base List.append; never calls production emit/finish. Abstraction maps Empty to
[], Chunk(xs) to [xs], Join(a,b) to list-concatenation(chunks(a),chunks(b)).
Unchanged universal BYTE_LAWS: list right identity/associativity, flatten of
joined fragment lists, emit(tree,suffix)=append(flatten(chunks(tree)),suffix),
finish(Buffer(cap,n,tree))=flatten(chunks(tree)). Text's universal append, compose,
identity/associativity and joint old/new snapshot observations remain checked.
Byte range/metadata safety is concrete normalization/runtime/source reasoning,
NOT a new universal operation-history theorem. Pinned proof closure has 27 filled
laws; no new axiom, unsafe declaration, hole, effect or proof claim.

Domains/witnesses: empty(0); fragment(4,[0,127,128,255]); old=fragment(3,[0,97]);
byte(old,255) succeeds, byte(old,256) fails InvalidByte; append(old,[1,2]) fails
Limit; old remains [0,97]. compose(empty(3),old) preserves [0,97]. Full cap zero
with byte 0 fails Limit; byte 256 at cap zero fails InvalidByte first. cap/count
maximum guard is tested without claiming allocation of four billion bytes.

Coverage: empty/fragment/finish via exact content and universal tree refinement;
append/byte via exact content, limits, invalid values and old/new observations;
compose via exact noncommutative order, left limit, both identities and sufficient
capacity groupings; length/limit via explicit expected values over capacities
0..64. Text checks include 512 triples, CR/LF/NUL/astral/combining values. Native
raw-max-Char extension remains distinct from JS scalar-text support.

Actual candidate gates: first proof/type/quantity compile passed, no diagnostic
retry. Native 14 named checks; JS 13. Nine mutants separately parsed/typechecked,
compiled, then failed their unchanged intended assertion. Dropping right bytes
now mutates only combine's right-tree argument to Empty, preserving the original
compose(empty(3),old) witness and byte-success-failure-persistence assertion.
Other mutants: discard/reverse/overwrite text; corrupt LF; accept 256; allow one
past capacity; use cap+n instead of cap-n. No survivor or syntax kill counted.

Linear work: join allocates one tree node and Buffer after count admission.
append scans only the incoming values; compose reads metadata; finish visits
all expanded K tree nodes and N emitted units once, O(N+K), including empty
fragments. Shared subtrees count per occurrence. Scaling at 1000/2000/4000/8000
chunks passed exact independent outputs and source census for tiny, uneven,
empty and byte fragments. Timings include the whole process; not an isolated
latency or allocation proof. Stack and host exhaustion remain runtime limits.

Trust: pinned Bend 2.0.29 parser/checker/conversion/termination and backend;
Base Equal, List/String append, Bool, U32/Word arithmetic. IO only in the harness.
Loaded Base unsafe Array fork/join are not called by this core/proof. No GPU,
Wasm, whole-book safety or universal metadata-history proof is inferred.

Hostile review: a successful count with discarded suffix must fail the original
content observation, despite preserved length. The adapted compose-only mutant
still does. A stale builder, reversed chunks, modulo length or altered first
error also contradict unchanged assertions. Additional join indirection is
accepted only because it centralizes the actual length/tree state transition;
style scores do not authorize weakening any property. This is a manual review,
not a formal claim that the property set is complete.

Candidate bytes.bend SHA-256: `c6ac3bc4c2a29e5745f657aa799a2b5387ea5536bd00a9e808a6dea6ea5f0d73`.

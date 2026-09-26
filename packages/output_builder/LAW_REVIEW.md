# OutputBuilder bounded law review packet

Scope: persistent text chunks and checked byte chunks. This packet records a
manual adversarial review and deterministic gates, not a completeness theorem.
Reference: Bend 2.0.29 at 574b6d39a235b539eb19a5c532993a0abb3d11ad.
All implementation/model/law/proof/test semantics are Bend. Host scripts only
build, compare command receipts, select mutations, and inspect publication.

## Contract, representation, independent oracle

Text API: empty(), fragment(String), append(Builder,String),
character(Builder,Char), compose(Builder,Builder), finish(Builder)->String.
Empty emits []; fragment emits its exact characters; append/compose concatenate
in order. No newlines, normalization or encoding are added. Immutable Data
values permit retaining old snapshots with +. Native accepts raw U32 Chars;
JS text requires Unicode scalars. These are distinct backend claims.

Bytes API: empty(U32 limit), fragment(limit,List<U32>), append(builder,list),
byte(builder,U32), compose(left,right), length, limit and finish->List<U32>.
Construction except empty returns Result<Error,Builder>. Every byte must be
<=255; count <= limit. At each fragment element, InvalidByte wins before the
capacity check; the first encountered error stops scanning. No partial result.
Compose keeps the left limit, compares right.length <= limit-left.length before
addition. Retained old values survive success/failure. Constructors and helpers
are language-visible but unchecked; callers forging Buffer must establish its
length/content/range invariant. The stable checked API constructs inhabited
valid states. No opacity claim or arbitrary-forged-buffer safety claim.

Independent oracle: model.join concatenates a plain fragment list; flatten
right-folds primitive append. Neither calls optimized finish/emit. The abstraction
maps Empty to [], Chunk(s) to [s], Join(a,b) to join(chunks(a),chunks(b)).
byte_model uses independent lists of byte lists analogously. Its observe helper
is an observation adapter over public results; literal expected results are the
oracle. Shared Base append is a primitive trust dependency, not a second call
to the builder under test.

## Actual laws and inhabited domains

Text universal laws (LAWS/PROOF): string right identity and associativity,
flatten(join(a,b)) = append(flatten(a),flatten(b)) are auxiliary algebra.
Behavior: emit(t,z) = append(flatten(chunks(t)),z); finish(t)=flatten(chunks(t));
finish(fragment(s))=s; finish(compose(a,b))=append(finish(a),finish(b));
finish(append(a,s))=append(finish(a),s); character appends exactly [c].
Left/right identity, observational associativity and empty-fragment identity
are universal equalities over the public finish observation. Snapshot law
jointly constrains old and new observations against the independent model.
Empty and mixed Unicode/CR/LF/NUL witness laws are concrete normalization.

Byte universal laws (BYTE_LAWS/BYTE_PROOF): list right identity/associativity,
flatten/join algebra, emit refinement with arbitrary suffix, and finish
refinement for every tree (metadata does not affect finish). Byte empty,
content [0,127,128,255], invalid 256, zero capacity, ordered composition and
maximum-U32 guard are concrete normalization, NOT universal checked-length
or validation proofs. These six closed equations complement runtime coverage.

All universal text/tree domains contain Empty, Chunk("a"), Join(Chunk("λ"),
Chunk("🙂\r\n")), suffix "!", lists [] and ["a","bc"], char LF and NUL.
Valid byte witnesses: empty(0), fragment(4,[0,127,128,255]), checked old
fragment(3,[0,97]). Invalid witnesses: byte(empty(0),0), byte(empty(4),256),
byte(empty(2^32-1),2^32-1). No Empty-typed parameters, axioms, unsafe witnesses
or contradictory preconditions. Capacity associativity runtime witnesses use
limit 6 and lengths 1,2,3, so both groupings are inhabited and fit.

## Public coverage matrix

| Operation | Laws | Independent runtime/domain evidence |
| --- | --- | --- |
| Text.empty | empty, identities, finish_model | empty in 512 triples; both identities |
| Text.fragment | fragment, finish_model | 8 samples: empty/ASCII/CRLF/Greek/astral/combining/NUL |
| Text.append | append, empty_fragment, snapshot | 512 triples; empty append; old/new snapshot |
| Text.character | character, witness | LF exact; native max-U32 Char |
| Text.compose | compose, associativity, identities | both groupings of 512 triples; reverse-order mutant |
| Text.finish | finish_model, emit_model | exact strings, never merely lengths |
| Bytes.empty | empty, finish_model | capacities 0..64; both composition identities |
| Bytes.fragment | content, finish_model | exact [0,97], [128,255], every capacity 0..64 |
| Bytes.append | content, full, invalid | full+empty, one-past, invalid-before-capacity, snapshot |
| Bytes.byte | full, invalid | 0/97/255/256/max-U32; exact byte lists |
| Bytes.compose | compose_content, tree refinement | order; insufficient left capacity; both sufficient-capacity groupings |
| Bytes.length | content, compose_content | expected counts 0..64; after byte/compose; overflow guard |
| Bytes.limit | concrete runtime | exact retained left capacity; unequal-capacity composition |
| Bytes.finish | finish_model | exact lists and retained old snapshots, including errors |

Low-level source names: text emit is universally refined. Byte emit is universally
refined; scan/guard/attach are exercised by append and byte witnesses; combine by
compose and maximum guard. Raw tree/Buffer constructors are not checked factories.
Model and proof functions are evidence, not advertised production operations.
There are no indices, identifiers, growth, codecs, or fuel. Resource exhaustion
is a runtime failure, never success. Omitted universal theorem: byte validation
and metadata preservation across arbitrary-length operation histories. Evidence
for that part is source guard analysis plus the named concrete/runtime checks.

## Semantic mutation results

Each mutant copied the unchanged conformance suite into its own build directory,
first passed parse/type checking as an implementation, compiled successfully,
and exited 1 at the specified assertion. No syntax/type/harness failures count.
The unchanged release source itself passes. Nine kills, no survivors.

- `discard-fragment`: semantic kill at `text-512-triples`; mutated SHA-256 `ce4d0585f455958643348254821b63694266d124fcfc57deac3e950f1eda8858`.
- `reverse-compose`: semantic kill at `text-512-triples`; mutated SHA-256 `5efed7afd79f39ccfbac2db39d881ae2340c51d91b3d2e9e81a029c549acff00`.
- `discard-prior`: semantic kill at `text-512-triples`; mutated SHA-256 `f3d5a95a6e6d695d3100762305a2789cab710393cc74b8cd945ec10164c8d0bc`.
- `newline-corruption`: semantic kill at `character-newline`; mutated SHA-256 `ea8e8da3a00649232234e3c6dffb77fed59bd10ff23f57272c97f7f0cdd4f412`.
- `reverse-emit`: semantic kill at `text-512-triples`; mutated SHA-256 `5f31a6834e86976b2d044e61591f6d00b3565d27909206ae1e081b474f4b1ffd`.
- `accept-256`: semantic kill at `byte-success-failure-persistence`; mutated SHA-256 `e7e2eb7612c74b6fc7bbc61aba8922b5f4fa9ae5e26be23a759418998a9d4118`.
- `one-past-capacity`: semantic kill at `byte-success-failure-persistence`; mutated SHA-256 `048f8aedb992e30c27f7275516fcbe0bf6dda450e89d5244bcd87c33038fa238`.
- `drop-right-bytes`: semantic kill at `byte-success-failure-persistence`; mutated SHA-256 `21971ece9c1c079ede624aa157c0e1913cf89c513210d5e3fa3e1fe7a17c66c9`.
- `wrong-remaining-room`: semantic kill at `byte-composition-order-limits`; mutated SHA-256 `a47dfc0ffd58f3751b56d7e226ed1cd8baa96f5bdff13c0ce04a3c3560908b2a`.

Witness details: discarding/reversing text breaks unequal nonempty strings in
text triples; newline corruption maps LF to CR; prior discard erases the prefix.
Allowing byte 256 breaks rejection after [0,97]; one-past admits [1,2] into one
remaining slot; dropping right bytes breaks compose(empty(3),old [0,97]); using
cap+n admits right [0,97] into a full left cap=2 builder [128,255].

## Cost review and measurements

Append(text) and compose allocate nodes without touching accumulated output.
Finish: emit(Empty,z)=z; emit(Chunk(s),z)=Base.append(s,z);
emit(Join(a,b),z)=emit(a,emit(b,z)). Each expanded node is visited once;
each character/byte occurrence is copied once. Work O(N+K), including empty
nodes, and stack bounded by tree depth plus longest fragment in the source
model. Byte append additionally validates each supplied byte once; composition
only checks metadata. Shared subtrees count once per emitted occurrence. Release
of retained structures may add linear destruction work. No repeated finish or
unbounded stack-safety guarantee.

Census is a source-level traversal count, not hardware instruction/allocation
instrumentation. Four increasing native workloads verify exact output against
an independently constructed string/list: tiny one-character fragments, empty
fragments, uneven pairs of 1 and 127 characters, and one-byte fragments.
- 1000 chunks: census tiny K,N / uneven K,N = 2001,1000,4001,128000; three total process times (seconds) = 0.1179, 0.0100, 0.0100.
- 2000 chunks: census tiny K,N / uneven K,N = 4001,2000,8001,256000; three total process times (seconds) = 0.1227, 0.0173, 0.0167.
- 4000 chunks: census tiny K,N / uneven K,N = 8001,4000,16001,512000; three total process times (seconds) = 0.1363, 0.0307, 0.0306.
- 8000 chunks: census tiny K,N / uneven K,N = 16001,8000,32001,1024000; three total process times (seconds) = 0.1655, 0.0607, 0.0603.

Times include process startup, generation, finish, oracle comparison and census;
they are not isolated finish latency. Cold-start variance is visible. Native C
emission uses the seed runtime's String/List layout and U32 primitive lowering.
No GPU/Wasm/WebGPU or JS large-depth scaling claim. Native conformance: 14 named
checks, including 512 string triples and 65 capacities. JS: 13 checks on scalar
text and bytes. Full JS raw-max-Char fixture fails because the seed rejects a
non-Unicode scalar; this is disclosed, not counted as a pass.

## Hostile review and trust

Tried constant/discard, reverse-order, stale-prefix and boundary mutants above.
A length-only specification would admit them; exact content assertions reject
them. Considered forged Buffer metadata: source visibility permits it, so the
representation invariant is an explicit checked-API domain boundary, not hidden
by documentation. Considered equal bytes with differing capacities: unrestricted
checked-result associativity is false; law/test scope now states sufficient
intermediate capacity. Considered arbitrarily many empty chunks: O(N) alone is
false; K is retained in the contract and measured.

All 27 law declarations are filled; pinned book_valid reports zero holes.
Trust: Bend parser, type/termination/conversion checker, compiler/native runtime,
Bun JS runtime, Base equality elimination, String/List append, Bool, U32/Word
arithmetic and comparisons. Runtime tests also trust IO and String equality.
Whole loaded Base includes unsafe Array.fork/Array.join and 42 foreign defs;
core/proofs do not call those unsafe array functions or foreign effects. Runtime
harness uses IO.print/IO.write through the native/JS effect bridge. No package
axioms, holes, unsafe declarations or foreign code. See closure.json inventory.

Nine locally matched Perch rules: eight shared law rules plus the package's
linear-assembly rule. Perch parsed the rule inventory; local glob coverage is
nonzero. Provider request fails before evaluation because PERCH_API_KEY is not
set. Completed model requests: 0, probabilities: unavailable, calibration:
unavailable. Draft rule is advisory; clean/broken/held-out packets are retained.
Deterministic gates remain the release decision. No model verdict is claimed.

## Frozen source identities

Exact reviewed upload closure includes both law/proof pairs, both models, API,
conformance and example, and MIT-0 LICENSE. Base is referenced, not copied. No
third-party source is incorporated into this closure. No sibling/private files.
- `BYTE_LAWS.bend`: `cffc93ff7f84fec0e39e26fabdd8ee1b74a93f34cbf875403acc7d44d76b599a`
- `BYTE_PROOF.bend`: `969180966cbeebb904be36ba3a84b69147a47c64f22eaaad14e82b4160a54df9`
- `LAWS.bend`: `7c0b887642a77a3b8522b9c05a66ae61045b618b6bd062510530f5a2a783b569`
- `LICENSE`: `7be3637ad6ba94d74378f1479b4798fcf6ccbfddc00f9d7313ae0aab089b0e87`
- `PROOF.bend`: `b6851d6a3738b754309c7d803f39c6c5e7e3d5eec6c376f83b8f61cc53d539f7`
- `byte_model.bend`: `d70023c2847de95e68f84db86f42c5fc7f1ed094166a492f2d108319ef43a396`
- `bytes.bend`: `b1c672949a72bcbc37509e31a1a20715eb73813904a50157328ded9ed0069ff1`
- `conformance.bend`: `f1f4bc8a01dbfa28fc62298ac3185fdcdca7e23569ed929ed8bf692ccd54ced5`
- `example.bend`: `8ab3b54a35ecd7e3ee1112fe0a80cb4d3c1c59930e906c116c564f7418c08ad3`
- `main.bend`: `4121b71f530bbb0d4cb05f7ff2ce3f2f65bbe5a5e3c1bb2f059a15b2c0491bb8`
- `model.bend`: `5a38de9bb16563d90077fd3e112084a420cc3b2cd55492a0e03c11d7c9101157`
- `release.bend`: `d13eb60779d4941ebbfdec4478345c61ec60dc0f8118f2ef3e7a1910966fd988`

Expected content identity: `0xc409b77d3230ca33374caf6b0993f0cb`. Publication and fresh-consumer
receipts belong in RELEASE.json; a proposed identity alone is not publication.

Publication completed: expected/returned identity matched; fresh remote native and
JS consumers passed, all 12 fetched file hashes matched. See RELEASE.json.

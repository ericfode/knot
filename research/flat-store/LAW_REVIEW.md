# Flat store: bounded law review

This Bend emitter generates a real 1,050-byte Wasm store module. It qualifies a
word-payload runtime component, not Knot source field lowering, generic heap
reclamation, self-hosting, or generated GPU execution. The source frontend and
its enum-only Wasm capability gate are unchanged.

## Contract and independent observation

The sole memory has exactly two pages. Header words are arena, capacity, ceiling,
free head, result slot, result generation, result word, disposer count. Each cell
is four U32 words: tag (0 vacant, 1 live, 2 retired), generation, payload, free
link. Cell i starts at byte 32+16*i. Capacity is 0..4096; bounds precede address
arithmetic. Last byte 65567 fits the reserved 131072 bytes. Sentinel 0xffffffff
is an absent slot/free link, not a forbidden arena or generation.

init(arena,capacity,ceiling) succeeds once per instance. Pre-init operations,
capacity failure and repeated init preserve every byte. Normal operation failures
may update result registers only. put(index,value) preserves the rejected incoming
word and every existing cell. alloc chooses the free head. take(arena,index,gen)
checks arena before bounds; retired always returns Retired, vacant distinguishes
matching Vacant from Stale. Successful take transfers once, increments a generation
below the ceiling and prepends that free slot; at the ceiling it permanently
retires. release performs take and increments a modular U32 disposer count only
on success. The returned serial and count witness a fixed word disposer, not a
general Type destructor. Put scans at most capacity links; valid alloc/take/release
are constant numbers of accesses. No measured speedup or throughput is claimed.

Statuses: 0 success, 1 Limit, 2 Full, 3 Bounds, 4 WrongArena, 5 Stale, 6 Vacant,
7 Occupied, 8 Retired, 9 NotInitialized, 10 AlreadyInitialized, 11 Corrupt.

The oracle imports the existing independent Data-list model, calls M.step, and
separately translates every logical cell and ordered free ID to words. It imports
no assembler/runtime function. The model calls no Store transition. The host
invokes exports, compares status and ALL logical words after EVERY command, then
compares ALL unused bytes with a fixed canary. It computes no store transition.
The same inputs and model were already independently qualified by the CPU owning
store's fixed literal fixtures; this is additional actual Wasm execution, not an
independent re-proof of that model. Hashes identify the exact shared vocabulary.

Exports are init/put/alloc/take/release/memory; there are no Wasm imports. Mutable
memory and host calls are privileged: forged images, cloned stores and reused
arena IDs are outside the construction contract. Corrupt is defensive, not a
complete hostile-image validator. Two reachable near-ceiling images are installed
explicitly, avoiding billions of setup cycles. Other states start at public init.
Global arena issuance, snapshot ownership transfer and physical reclamation remain
unimplemented obligations. Locator decoding yields three numbers, not authority.

## Coverage and proof boundary

| Public operation | Filled-law scope | Independent execution and invalid domains |
| --- | --- | --- |
| init | module encoding/limit only | capacity 0..4096, 4097 and U32.max; rejected/repeated init preserves bytes |
| put | no universal Wasm refinement theorem | free/occupied/retired, bounds, stale unrelated slots, incoming owner, free-order and canaries |
| alloc | no universal transition theorem | increasing order, reuse, zero/full, retired capacity |
| take | no universal transition theorem | arena-before-bounds, stale/double take, Vacant/Retired, max-1/max generation |
| release | no universal transition theorem | serial/count, rejection without disposal, unrelated slots and retirement |
| exported memory | fixed layout arithmetic witnesses only | exact 131072 bytes, grow rejection, every logical word and trailing canary |
| locator word codec | arbitrary U32 triplet round-trip; short/long arity reject | zero/max words, malformed lists; this is NOT a twelve-byte transport codec |
| address utility | capacity failure for arbitrary index; concrete first/last/padding equations | 0/1/3/4096/4097/U32.max capacity/index cases |
| assembler | arbitrary zero-fuel failure; literal instruction and error equations | canonical signed/unsigned LEB, store alignment/offset, nested blocks, byte/range/fuel/output limits |
| complete emitter | zero-capacity output failure | native/Bun byte equality, actual Wasm validation, 1049-byte cap rejection |

Fifteen laws are filled with no holes and no new axiom/unsafe declaration. Five
are universal in their displayed arguments (round-trip, short/long arity, oversized
capacity, zero fuel). Ten are concrete normalizations. None proves general Wasm
simulation, inductive free-chain preservation, arbitrary heap refinement, or
completion of the compiler milestone. The address helper and raw instruction IR
are internal construction APIs; the checked offset wrapper and fixed runtime
bodies establish their bounds. They are not a validator for arbitrary IR.

Safe inhabited witnesses include arena 41, capacities 0/1/2, words 7/9/11,
generation ceilings 0/1, malformed locator lists and U32.max words. No Empty or
contradictory premise appears. The runtime gate reuses 3,532 traces: 3,510 exhaustive
sequences of length 0..3 from eight fixed commands at capacities 0..2 and ceilings
0..1; fifteen named longer/literal-input witnesses; seven width workloads through
4096. Two near-ceiling traces bring the total to 3,534 instances and 13,621
step observations PER native/Bun emitter lane. Seven additional lifecycle checks
run per lane. Twenty-four fixed codec/encoding observations execute in native and
Bun. These are bounded finite results; oracle rendering is a simple O(n^2) model,
not the claimed complexity of the emitted store.

## Adversarial checks

All nine mutants seed-check, emit valid modules with the same exports and no
imports, then fail unchanged independent assertions. Syntax/validation errors,
timeouts, absent dependencies or host failures do not count as semantic kills.

| Mutation | Intended violated observation / actual witness |
| --- | --- |
| reuse generation | whole-cell generation after take; stale-after-reuse |
| accept padding | Bounds at logical capacity; distinct Corrupt is not acceptable |
| overwrite on rejection | occupied 7 remains while incoming 9 is returned |
| ignore arena | WrongArena precedes Bounds |
| wrap at ceiling | ceiling-zero release must retire, not become free |
| lose free tail | take preserves other free slots and their order |
| erase allocated payload | inserted 7 remains in the live cell |
| zero sentinel | empty header/result/free-chain markers retain U32.max |
| write on rejected reinit | after allocation, init with arena 42 returns 10 but changes no byte |

The first harness used an aliased Buffer for the reinitialization comparison.
Its historical receipt is retained and explicitly disqualified for that claim.
Frozen typed-array copies repair the assertion; the new write-on-reinit mutant
passes all model rows before being rejected for an unexpected memory write.
No transition code or original expected observation was changed to hide a failure.

A hostile host can clone an image and thereby duplicate represented ownership:
that is explicitly unsupported, not prevented by this module. A second lifetime
with a reused arena can likewise accept an escaped locator. These require a fresh
arena/transfer authority contract before integration. Word payloads neither model
shared Data roots nor disposal of captured affine resources. No GPU execution is
claimed. Compact heterogeneous fields, twelve-byte locator transport, general
Data lifetime and submitted-reader reclamation remain separate pending probes.

The pinned seed closure loads 42 Base foreign declarations plus unsafe Array.fork
and Array.join; no new unsafe primitive is introduced or called here. The seed
emitter, oracle and probe foreign-call lists contain only IO.print. Seed checking,
normalization, native primitive lowering, Wasm engine execution, and the privileged
host stay in the trust base. Full closure hashes are in receipts/trust.json.

## Complete law statements

S is compiler syntax/error, T the owning-store Locator, L the layout utility, A
the assembler and M the module builder. bytes finishes a checked ByteOutput builder.
These statements are all filled by PROOF.bend; the finite Wasm observations above
remain separate evidence.

```bend
law locator_round_trip:
  for +arena: U32
  for +index: U32
  for +generation: U32
  {L.decode_locator(L.encode_locator(T.Locator{arena,index,generation})) == Done{T.Locator{arena,index,generation}} : Result<L.Error,T.Locator>}

law missing_word_rejected:
  for arena: U32
  for index: U32
  {L.decode_locator([arena,index]) == Fail{L.LocatorArity{}} : Result<L.Error,T.Locator>}

law trailing_words_rejected:
  for arena: U32
  for index: U32
  for generation: U32
  for extra: U32
  for tail: List<&2,U32>
  {L.decode_locator(Con{arena,Con{index,Con{generation,Con{extra,tail}}}}) == Fail{L.LocatorArity{}} : Result<L.Error,T.Locator>}

law oversized_capacity_precedes_address:
  for index: U32
  {L.offset(4097,index) == Fail{L.CapacityLimit{}} : Result<L.Error,U32>}

law empty_has_no_address:
  {L.offset(0,0) == Fail{L.IndexBounds{}} : Result<L.Error,U32>}

law first_cell_follows_header:
  {L.offset(1,0) == Done{32} : Result<L.Error,U32>}

law last_cell_fits_reserved_memory:
  {L.offset(4096,4095) == Done{65552} : Result<L.Error,U32>}

law padding_is_not_a_cell:
  {L.offset(4096,4096) == Fail{L.IndexBounds{}} : Result<L.Error,U32>}

law zero_fuel_is_explicit:
  for chunk: A.Chunk
  for cap: U32
  {A.encode(0n,chunk,cap) == Fail{S.Exhausted{"emit",S.At{0,0,0,0}}} : Result<S.Error,B.Builder>}

law sentinel_is_signed_minus_one:
  {bytes(A.encode(1n,A.OneInstruction{A.CodeNegativeOne{}},2)) == Done{[65,127]} : Result<S.Error,List<&2,U32>>}

law store_encodes_alignment_and_offset:
  {bytes(A.encode(1n,A.OneInstruction{A.CodeMemory{54,128}},4)) == Done{[54,2,128,1]} : Result<S.Error,List<&2,U32>>}

law signed_positive_boundary:
  {bytes(A.encode(1n,A.OneInstruction{A.CodeWord{2147483647}},6)) == Done{[65,255,255,255,255,7]} : Result<S.Error,List<&2,U32>>}

law signed_overflow_is_explicit:
  {bytes(A.encode(1n,A.OneInstruction{A.CodeWord{2147483648}},6)) == Fail{S.Internal{"emit","signed-range"}} : Result<S.Error,List<&2,U32>>}

law output_limit_is_explicit:
  {bytes(A.encode(1n,A.OneInstruction{A.CodeNegativeOne{}},1)) == Fail{S.Exhausted{"emit",S.At{0,0,0,0}}} : Result<S.Error,List<&2,U32>>}

law module_limit_is_explicit:
  {M.emit(0) == Fail{S.Exhausted{"emit",S.At{0,0,0,0}}} : Result<S.Error,List<&2,U32>>}
```

## Reviewed source identities

- `LAWS.bend`: `3602fe79b1bccaef0b8f8dbb088d5c2226ac6c92cc1f77031dad30d75c77b6c6`
- `PROOF.bend`: `646685770ca7e7fc092a79b5dc8af8ba88c6b1b80c37cc6dd8677c438a0ba1f9`
- `assembly.bend`: `ca0461b3114329cc0523715e17293a375f532fbc7f0b08ce70e2cf833dffcf2d`
- `emit-cli.bend`: `56dd00d5098461bdac42018cab3f2b322580ad8be76c62a8734d684a18851ab7`
- `layout.bend`: `1c7ec2e03e4158593aa3d108ac7d97c3688a515ff1da1c0bebc3f2ff4cb976b6`
- `module.bend`: `b38c0c098132daaed1044be271ca0087050f59a2d443b26a09d5f141fc5ddb2e`
- `oracle.bend`: `8fb1e430b9a5a5e13f058fa88532e4758fcf63568de95e1f85a374b25c5d6e7a`
- `probes.bend`: `2e617b8aa430354f56ca94fbaa4dc9c25dd928c4e5015d8ab149189c386947b8`
- `runtime.bend`: `586c23498e231525743c4882d2162ef20a4d31c02c4fb60bd33446c4c6a165ac`

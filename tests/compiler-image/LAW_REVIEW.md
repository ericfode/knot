# Law review: increment `image`

Owner: this increment. Files: [src/image-OPEN.bend](../../src/image-OPEN.bend) (the open law),
[src/image-LAWS.bend](../../src/image-LAWS.bend) and [src/image-PROOF.bend](../../src/image-PROOF.bend)
(the closed laws and their proofs). D21 requires a law that cannot yet be proved in general to stay required,
never weakened, and recorded here and in `src/SPEC.md` with its evidence.

## The required law: open (D21)

```
law round_trip:
  for +fuel: Nat
  for +book: C.Book
  for +words: Y.Encoded
  for done: {I.encode(fuel,book) == Done{words} : Result<S.Error,Y.Encoded>}
  {I.recoded(fuel,book) == I.erase_tokens(fuel,book) : Result<S.Error,P.Plan>}
```

Partial correctness, as the coordinator ruled in review round 1: for every book and fuel, whenever `encode`
answers, decoding its words gives the plan that erasure gave at the same fuel, that is
`encode(fuel,book) == Done(w) -> decode(w) == erase_tokens(fuel,book)`. `recoded` is `decode` of the words of
`encode`. `encode` binds on `erase_tokens` and hands layout the same fuel, so an answer implies that erasure
succeeded at that fuel: the equation compares like with like, and no side condition on erasure is needed. A
refusal by layout is no answer, and the law says nothing of it.

`erase_tokens` cannot return a `C.Book` with its tokens blanked: the image also drops quantity-0 parameters,
fields, lets and arguments, renumbers levels as frame slots, and forgets datatype kinds and quantities 1 versus 2.
It projects into `Plan`, the image's own record tree (`src/image-plan.bend`).

The statement is a real `law`, in a file of its own because an open law fails the file that holds it. The gate
requires that `scripts/bend-reference src/image-OPEN.bend --check-only` type-checks and reports exactly one open
claim (`Error: 1 TODO found.`), so the law can be neither weakened nor lost unseen. It also instantiates the statement
(below). Its status stays **open**.

## The first statement was false (review round 1)

The law was first written `recoded(fuel,book) == erase_tokens(fuel,book)` for every fuel and book, and recorded as
true but unproved. The seed's kernel refutes it, on this increment's own books. It has three counterexample classes, each
pinned by closed ground laws in `src/image-LAWS.bend` (`!=` laws, proved by exhibiting a refusal against an answer):

| Class | Why | Closed laws |
|---|---|---|
| Fuel | `encode` gives layout the fuel erasure has, and layout needs more: erasure answers from fuel 1 on `flag_book` and layout from 3; from 13 and 19 on `mixed_book` | `flag_refuted_at_1`, `flag_refuted_at_2`, `mixed_refuted_at_13`, `mixed_refuted_at_18` (the ends of the windows 1 to 2 and 13 to 18) |
| Limits of SPEC section 4 | layout refuses an image past a limit at any fuel; erasure has no limit. An arity past 4,096 is the cheapest ground instance; the size limit (4,194,304 words) is observed by the gate on a checked book: `image-cli answers` prints `erase_tokens Done` and `recoded Exhausted` for the 4.8M-word synthetic book | `wide_refuted` (4,097 live parameters); the gate's heavy control |
| Names | decode reads bytes 1 to 127 only: an empty name, a zero byte and a wide Char are refused by decode as `name length`, `name padding` and `Unsupported image-name`, while layout wrote them | `accent_refuted`, and the three refusals below |

**Decision on names.** There were two ways to a true statement. (a) Make the encoder refuse a name that decode does
not read, as `Unsupported compile image-name`, the string that SPEC and the report already promised; the statement then
needs no side condition. (b) State the law for books with identifier names only. (a) was chosen: the ruled statement is kept as
ruled, the encoder no longer emits an image that the reference codec refuses (`vm/serializer.py` refuses an empty name,
a zero byte and invalid UTF-8; layout used to write any Char, including a surrogate and a code past U+10FFFF), and it
costs nothing observable: the lexer admits no non-ASCII byte and an identifier is never empty, so no checked book has
such a name, and all 96 accepted books stay byte-identical to the frozen references. The predicate is `P.spelled` in
`src/image-plan.bend`, used by `layout` (which refuses the plan before any word exists) and `name_byte`, used by
`decode`. A valid UTF-8 name that is not ASCII is admitted by the reference codec and refused by the Bend codec
(`Unsupported image-name`), as SPEC says; the crafted control `name-wide` pins it.

## Why there is no proof yet

A general proof is an induction over `C.Term` that carries three invariants through `erase_tokens`, `layout` and `decode`
at once: the slot numbering of `lower` (a live binder takes the next slot and `slots` is the exact maximum), the
offsets of the two-pass node placement (a record's offset is the words before it, in a section whose position
depends on the constants pool that the first pass builds), and the stack discipline of the decoder (a record takes
the newest entries its offsets name). The seed's kernel does not reduce `U32` arithmetic on a variable, so offsets and
counts cannot be left symbolic, which is why the ground laws below quantify only over words that are moved. Nobody has
written that induction; it is the obligation. It is true as stated: no counterexample is known, and the evidence below
is where one would appear.

## Evidence for the open law

1. The twenty-four closed laws below, checked by the seed (`All terms check.`).
2. **The gate instantiates the statement.** `check.py` reads `law round_trip` as written and proves it at 13 fuels and
   books: `flag_book` at 0, 1, 2, 3 and 64; `mixed_book` at 0, 12, 13, 18, 19 and 64; and the two books that layout
   refuses at any fuel (`wide_book` and a book whose datatype is named `é`). At each instance either the conclusion holds
   by evaluation (`equal`: the encoder answers and decodes to the erased plan, or both refuse alike), or the hypothesis is
   refuted (`refused`: the encoder does not answer, and a `Fail` is not a `Done`). Fuels 1, 2, 13 and 18 are `refused`,
   the windows in which the first statement was false. The same machinery must fail to prove the first statement at
   those four fuels, and a copy of the law with a wrong conclusion at fuel 64, so a false open law is refused.
3. `image-cli roundtrip` on each of the 96 frozen-suite books that the checker accepts: Bend's own
   `decode(encode(b))` and `erase_tokens(b)` print alike; and `image-cli plan` prints `erase_tokens(b)` as
   `vm/serializer.py` decodes the image the compiler wrote (both lanes).
4. The compiled bytes of those 96 books equal an independent reference frozen before the encoder existed
   (five witnesses were added afterwards), and the 111 golden images decode to the text of
   `serializer.decode` and re-encode to their own bytes.
5. Twenty-one mutants of the codec, each killed by a wrong observation; the laws refuse most of them too.

## The closed laws (twenty-four)

| Law | States | Covers |
|---|---|---|
| `erase_flag_book` | `erase_tokens` of a one-function enum book is the plan written by hand, for every source position | the minimal book |
| `erase_mixed_book` | the same for a book with reordered arms, an erased field, an erased parameter, an erased let, an erased call argument and an all-erased constructor | operand filtering, slot numbering, tag-ordered rows, `Value` for an all-erased constructor, a Let's type |
| `round_trip_flag_book` | `recoded` equals `erase_tokens`, for every position | the round trip on the minimal book |
| `round_trip_mixed_book` | the same on the mixed book | every form of this base, both directions |
| `round_trip_any_value` | the round trip for every type index, tag and result type of a value | words that are only moved |
| `round_trip_all_forms` | `decode` of `layout` of a plan carrying all thirteen forms is that plan: literals of each kind, an intrinsic, a foreign leaf, a keys-mode Case with a default, a tag-mode Case with a missing row, a closure with a capture, an invoke, arrow and opaque types | the codec beyond this base's core |
| `flag_refuted_at_1`, `flag_refuted_at_2` | the first statement is false: erasure answers and the image is refused for lack of fuel | the window on `flag_book` |
| `mixed_refuted_at_13`, `mixed_refuted_at_18` | the same, at the ends of the window on `mixed_book` | the window on `mixed_book` |
| `wide_refuted` | the first statement is false on a book with 4,097 live parameters | the limits of SPEC section 4 |
| `accent_refuted` | the first statement is false on a book whose datatype is named `é` | names |
| `empty_name_is_refused`, `nul_name_is_refused`, `wide_name_is_refused` | `encode` of a book with an empty name, a zero byte or a wide Char is `Unsupported compile image-name` | the names decode does not read |
| `magic_spells_kimg` | the magic word's bytes are `K I M G` | header |
| `empty_file_is_not_an_image` | `decode(Nil)` is `HostFailure image length` | the refusal of a file too short for a header |
| `all_erased_constructor_is_a_value` | for every type, tag and depth, an operand list with no live operand lowers a constructor to a `Value` | SPEC section 3: a Construct has at least one live field |
| `erased_let_is_its_body` | for every fuel, environment, token, level, type, value and body, an erased Let lowers as its body under an erased binder | erasure of lets |
| `erased_operand_is_dropped` | for every operand list, an erased parameter's operand is dropped | erasure of arguments and fields |
| `let_takes_its_bodys_type` | a Let node's type is its body's, whatever the initializer's | SPEC section 3 positional types |
| `absent_arm_is_a_missing_row` | a tag with no arm gives a `Missing` row | the dense tag table |
| `chunk_bytes_are_little_endian` | a word streams as its bytes low first | the writer's byte order |
| `empty_stream_ends` | a stream of nothing ends | the writer's termination |

The first five and `round_trip_all_forms` compare with a hand-written plan or with each other on fixed books,
written from vm/SPEC.md sections 1 and 3 before they were compared with the encoder's answer. They state the
same thing at ground instances; they are not a proof for all books, and this review does not claim so.

## What the laws do not cover

`decode` is structural; scope, type and arity rules are the VM validator's (`vm/serializer.py` `validate` is
run on every image written). Names are ASCII identifiers. The laws do not cover the chunked output, the header offsets for
an image whose sections have other sizes, or any refusal of a malformed image beyond an empty one: the gate's
crafted images and mutants do. Function names that repeat are refused by `validate` and not by the Bend codec; the checker
never lets a book carry them. No Perch call was made; semantic and style review of the four files remain the
coordinator's.

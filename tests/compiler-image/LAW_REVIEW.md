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
  {I.recoded(fuel,book) == I.erase_tokens(fuel,book) : Result<S.Error,P.Plan>}
```

In the task's words, `decode(encode(b)) = erase_tokens(b)`. `erase_tokens` cannot return a `C.Book` with its
tokens blanked: the image also drops quantity-0 parameters, fields, lets and arguments, renumbers levels as
frame slots, and forgets datatype kinds and quantities 1 versus 2. It projects into `Plan`, the image's own
record tree (`src/image-plan.bend`), and `recoded` is `decode` of the words of `encode`.

The statement is a real `law`, in a file of its own because an open law fails the file that holds it. The gate
requires that `scripts/bend-reference src/image-OPEN.bend --check-only` type-checks and reports exactly one open
claim (`Error: 1 TODO found.`), so the law can be neither weakened nor lost unseen. Its status stays **open**.

Why there is no proof yet. A general proof is an induction over `C.Term` that carries three invariants through
`erase_tokens`, `layout` and `decode` at once: the slot numbering of `lower` (a live binder takes the next slot
and `slots` is the exact maximum), the offsets of the two-pass node placement (a record's offset is the words
before it, in a section whose position depends on the constants pool that the first pass builds), and the stack
discipline of the decoder (a record takes the newest entries its offsets name). The seed's kernel does not
reduce `U32` arithmetic on a variable, so offsets and counts cannot be left symbolic, which is why the ground
laws below quantify only over words that are moved. Nobody has written that induction; it is the obligation.

## Evidence for the open law

1. The fifteen closed laws below, checked by the seed (`All terms check.`).
2. `image-cli roundtrip` on each of the 96 frozen-suite books that the checker accepts: Bend's own
   `decode(encode(b))` and `erase_tokens(b)` print alike; and `image-cli plan` prints `erase_tokens(b)` as
   `vm/serializer.py` decodes the image the compiler wrote (both lanes).
3. The compiled bytes of those 96 books equal an independent reference frozen before the encoder existed
   (676 books; five witnesses were added afterwards), and the 102 golden images decode to the text of
   `serializer.decode` and re-encode to their own bytes.
4. Nineteen mutants of the codec, each killed by a wrong observation; 13 of them are also refused by the laws.

## The closed laws (fifteen)

| Law | States | Covers |
|---|---|---|
| `erase_flag_book` | `erase_tokens` of a one-function enum book is the plan written by hand, for every source position | the minimal book |
| `erase_mixed_book` | the same for a book with reordered arms, an erased field, an erased parameter, an erased let, an erased call argument and an all-erased constructor | operand filtering, slot numbering, tag-ordered rows, `Value` for an all-erased constructor, a Let's type |
| `round_trip_flag_book` | `recoded` equals `erase_tokens`, for every position | the round trip on the minimal book |
| `round_trip_mixed_book` | the same on the mixed book | every form of this base, both directions |
| `round_trip_any_value` | the round trip for every type index, tag and result type of a value | words that are only moved |
| `round_trip_all_forms` | `decode` of `layout` of a plan carrying all thirteen forms is that plan: literals of each kind, an intrinsic, a foreign leaf, a keys-mode Case with a default, a tag-mode Case with a missing row, a closure with a capture, an invoke, arrow and opaque types | the codec beyond this base's core |
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
run on every image written). Names are ASCII. The laws do not cover the chunked output, the header offsets for
an image whose sections have other sizes, or any refusal of a malformed image beyond an empty one: the gate's
crafted images and mutants do. No Perch call was made; semantic and style review of the four files remain the
coordinator's.

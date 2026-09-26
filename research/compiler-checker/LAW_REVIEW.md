# Enum-profile checker review packet

This increment implements resolution and semantic checking in Bend 2, following
Bend 2.0.29 revision 574b6d39a235b539eb19a5c532993a0abb3d11ad. It does not implement
an evaluator, code generator, self-hosting, or GPU source lowering. Existing
frontend and adaptive-task prototypes remain separate, previously checked work.

## Contract and representation

`check(depth:Nat, root:syntax.Node) -> Result<syntax.Error,core.Book>` validates
all declarations and all function bodies, including unused ones. Its supported
input is the parser's enum-profile AST. Catalog, scope and traversal helpers are
implementation modules, not independently validated public package interfaces.
Calling a helper with fabricated indexes/scopes is outside their caller invariant.

A book contains nonempty, nullary Type/Data enums and fully typed first-order
functions. Global names and constructor declarations are unique. Parameters and
local bindings shadow by nearest lexical binder, including repeated parameter
names. Type and function indexes follow their own declaration order. Constructors
use declaration-order tags. The checked term records binder levels, type indexes,
callee indexes, quantities, ordered arguments, and explicit constructor-tag arms.
Its Sequence/Branch variants are traversal containers, never standalone checked
expressions. No successful term is an evaluator result.

Affine usage is a set of lexical levels: reference of a live quantity-1 binder
adds its level; quantity-2 Data references and erased contexts add none.
Sequential sets must be disjoint, then are concatenated. Alternative sets are
unioned. A local's level is removed when exiting its scope; its initializer uses
are sequenced before its remaining body uses, even when the local is unused.
Quantities remain per binder even for Data values. Transferring a Data value to
a reusable callee or local consumes the incoming affine reference once.

Matching consumes a live parameter. In each arm its subsequent occurrences become
fresh known nullary constructors; they no longer refer to the consumed binder.
Matching follows parameter order. Earlier/already matched binders and outer
parameters after a local binding cannot be matched. A branch may use a remaining
parameter once in each alternative. Each supported match has exactly one arm per
constructor. Overlapping arms are Unsupported, since the reference can accept
first-match overlap. Missing arms, wrong pattern types and affine reuse are Invalid.

Scope/type checks still run in erased initializers and arguments. Erased binder
use in a live position is Invalid. Forward live calls are Invalid; forward erased
calls are allowed. Self-calls are Unsupported. Reusable Type binders are Invalid.
Unknown names/types, constructor/call arity, and type mismatches fail explicitly.
No imports, fields, general recursion or dependent types are supported.

Source cap: 65,536 characters. Parser default depth: 512. Checker default depth:
512, override 0..4,096. Catalog caps: 256 types, functions, constructors per type,
parameters per function. Level cap: 4,096. Crossing a cap is Exhausted, not Invalid.
Checker fuel bounds recursive traversal depth, not total work. Source/catalog caps
bound structural list traversals; lookups and set merging are linear/quadratic.
These are prototype algorithms with no speed or stack-portability claim. The
current CLI prints Checked plus a canonical resolved-term observation, never Built.
No artifact is emitted. Internal malformed traversal states remain InternalFailure.

## Independent observations and coverage

`python3 tests/compiler-checker/check.py` passed for the source hashes below.
The harness implements no compiler semantics. It drives the Bend checker on Bun
and native, drives the pinned reference interpreter separately, and compares
literal expectations from cases.json. Successful observations check exact resolved
identities, ordered calls, quantities and branch trees, not just a success flag.

| Operation / property | Evidence | Explicit limits |
|---|---|---|
| catalog, name/type/constructor/function lookup | 49 reference fixture outcomes include forward types, duplicate globals/constructors, unknown types, arity and unused invalid definitions | Finite corpus, not completeness of source-language compatibility |
| nearest scope and lexical levels | Exact shadowing/parameter-shadow trees; nearest_binding_wins law; shadowing/type negative | Law fixes spelling x but quantifies tail and level |
| sequential/alternative affine use | branch-maximum and branch-duplicate; Data reuse/default-affine controls; used/unused initializer cases | No universal expression-level usage theorem |
| erasure | erased forwarding, forward erased call, erased binding, bad erased names/types and live uses | No execution/ABI erasure proof yet |
| pattern refinement/order/exhaustiveness | nested/reordered match, matched return/duplicate constructor uses, reverse order/repeated/after-let negatives, wrong/missing/overlapping patterns | Only nullary constructors, no fields or dependent refinements |
| resolved-term rendering and CLI | 98 exact native/Bun observations, matching exits/diagnostics; build entry checked | Rendering is an observation, not an evaluator |
| checker depth and catalog caps | 10 CLI observations: depths 0,1,3 fail; 4,5 accept Flag. 16 catalog helper observations: 256 accepts with length 256, 257 exhausts in both lanes | Catalog bounds use constructed ASTs; lexical-level cap not independently exercised at 4096 |

The 49 reference fixtures partition into 17 supported successes, 30 Invalid
cases, and two Unsupported cases (overlapping arms and recursive call). All 49
reference outcomes and intended diagnostic substrings are retained. The reference
accepts overlapping arms; this difference is intentional and explicit. It rejects
the particular recursion witness for lack of decrease; Unsupported does not claim
all excluded recursive programs are invalid. No timeout/parser failure stands in
for an expected quantity/type rejection.

## Laws, witnesses and proof boundary

`src/check-PROOF.bend` imports the complete earlier frontend proof entry and fills
seven additional laws. The actual checker reports All terms check, without holes,
new axioms or unsafe escapes. These are helper/boundary laws, not compiler correctness:

1. Empty sequential prefix preserves arbitrary use set exactly.
2. Sequencing [0] and [0] reports affine-reuse at the supplied token.
3. A live erased occurrence reports erased-live (arbitrary token/level/type).
4. An erased occurrence preserves the reference's level/type and has no live uses.
5. A refined affine occurrence constructs its exact known type/tag with no use.
6. Lookup at the head named x returns that binder, for arbitrary level and tail.
7. check(0, arbitrary AST) reports Exhausted, never success or Invalid.

Witnesses are ordinary tokens with inhabited At records; levels/tags 0 and 1;
empty and nonempty use sets; Flag{Off,On}; and nonempty binding environments with
shadowed spellings. There are no impossible preconditions. Laws 1 and 7 are boundary
laws, 2 is a concrete alias witness quantified over diagnostics, 3–6 specify helper
behavior. The literal whole-tree fixtures and independent reference outcomes reach
the public check operation; helper laws alone would not establish that composition.

## Semantic mutations and hostile review

Seven mutants first pass the complete checker CLI's syntax/type/quantity gate, then
compile and fail unchanged fixture expectations. No syntax error, timeout, missing
import or harness failure is counted as a semantic kill:

- Accept intersecting sequential sets: affine-reuse incorrectly accepted.
- Ignore live erased occurrence: erased-type-live incorrectly accepted.
- Do not refine a matched binder: matched-duplicate incorrectly rejected.
- Give a new local level zero: shadowing's exact resolved identities change.
- Accept missing match arms: missing-arm incorrectly accepted.
- Ignore expected type of a reference: shadowing-type incorrectly accepted.
- Keep erased argument context live: erased-forward incorrectly rejected.

A checker returning success for every input fails the rejection corpus. Returning a
fixed successful tree fails Flag versus nested/shadowed/call trees. Name-only lookup
fails the shadowing observations. Adding uses across alternative branches rejects
a valid branch-maximum program. Treating a matched affine parameter as still owned
rejects the matched-duplicate control; its branch constructors are fresh values.
Checking only executable positions would miss bad erased names/types. Checking only
main would miss unused-bad-function. These adversaries are concrete finite evidence;
we do not claim every listed public behavior has an independent universal theorem.

The compiler imports pinned Base for Data, primitive arithmetic/string/list operations
and IO; its native/FFI lowering remains trusted. No new native or unsafe semantic
primitive was added. A complete trusted IO closure inventory is still a milestone
gate. The source checker does not accept foreign code, effects or Base imports.

No style rank is claimed: there are no equivalent competing implementations in this
increment. The set algebra and explicit constructor refinement can be explained from
code without inventing a preference comparison.

## Reviewed input hashes
- `src/LAWS.bend`: `5db3a525420e9cff3448b0a7219ff71b10a8dc111d6e440007c2a0ae7e8fa76d`
- `src/PROOF.bend`: `c0313e180f55d3941f6bae25a7c4d4362f883495bb54dcb570ef62825eb43a80`
- `src/catalog.bend`: `d734d9cd3f7b6d9599a6663d19e6a8114497e53fd01255139905dc8cb41ce762`
- `src/check-LAWS.bend`: `3d3cccaed0e131f1ed185472dfe63cc4208ab3dbbf51a72c419b52ff0d599fde`
- `src/check-PROOF.bend`: `2fe6bce9d7f4e03042794864e8249ffbd2e9b0d4824453f633b4483ac8bf0a9d`
- `src/check-cli.bend`: `7cbcc66c6586a1a5e5997a8b0771d791219d368a0ebaa1febffa07702c3e5705`
- `src/check.bend`: `55818425ddbd7cdac13bc08543336aaf21f6df5fefd5613649f4332b69035d13`
- `src/checked-display.bend`: `6f6184f62376d5b527405e4304e38ed989fff960a258b9909226126d48050c79`
- `src/core.bend`: `c8341c310680b35e292e60fa2b1ab691e5ce0b07b26d695a07c03a652e8b4fc0`
- `src/diagnostic.bend`: `4a53c508ba8d05adfca9bb10a559979e096d5da9095605cf0d34a9c9bb389b73`
- `src/lex.bend`: `1e4668537a254764ecd5b0830511d7b9ee1a21e830d03ae7fea78a1d8578c4b3`
- `src/parse-cli.bend`: `7a4feaec7c67c3a8ed7909d46dbef4ca8f5897857b769976f9e2704e67400c90`
- `src/parse.bend`: `22cc65edc3ba1f50800426e1218c587a89e667a665b8779bdbb5a4ae7895a4ab`
- `src/scope.bend`: `4657604c5c0a5cf7aa61729188a36016926c3ee8ff06d93c488cdfaaa834a4dd`
- `src/syntax.bend`: `1747ef052e6ee974b2673078db92f9a352f8933a9ad54b573de059b0ae3c8d7b`
- `src/SPEC.md`: `d4cb2d11d95d672356ced1cf730b102bba2fe44cc90a167ad8770d16d3f69675`
- `tests/compiler-checker/cases.json`: `bc7b249e2cb2a12e35dc52e08d2a94c025d6cb2bf7c7edefa665b325870e0456`
- `tests/compiler-checker/check.py`: `b0c66fb800dfb25019270e8ddd9b71096727c77f5a768260eea5ba286130f578`
- `tests/compiler-checker/bounds.bend`: `2f1587776588778e6d7b44a7c17bbf057a7c9b8d9e91e3bf467ce93c8b0fc4a5`

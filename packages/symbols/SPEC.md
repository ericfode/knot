# Symbols contract

Abstract state is an ordered list of distinct exact Bend Strings and a limit.
`new` uses the Vec maximum 16,777,216; `bounded(k)` uses min(k,maximum).
Length is the number of distinct entries. `find(s)` is the first matching index
or None and preserves all observations. `intern(s)` returns that existing index
without growing; if absent and length < limit it appends s and returns the old
length; otherwise it returns Exhausted and preserves all observations.
`resolve(i)` returns exactly entry i if i < length, else InvalidId, preserving
all observations. Table metadata reads preserve entries and limit.

IDs are U32, in [0,length). The smaller explicit allocation policy prevents U32
wrap before increment. OOM is a host runtime failure, not a recoverable typed
Exhausted. Lifetime is one owned table lineage. A new table restarts at zero;
foreign IDs are a caller contract violation and are not detectably branded.

Names include empty, prefixes, NUL, ASCII, and Unicode. No normalization:
composed/decomposed spellings are distinct. Equality checks the complete string;
hash collisions cannot alias because the implementation does not hash names.
The working implementation uses a character trie. An optional Here binding at
each prefix root represents end-of-string, separately from every character
including NUL. Red-black Fork siblings order the next character; their same
children continue the suffix. Here never occurs along a less/more sibling edge.
Each prefix root, after its optional Here, is black; sibling paths have equal
black height and no red/red edge. Reverse storage uses Vec's public API.
The abstraction relation is: Vec contents equal the model's names in order, and
Trie contains exactly each name mapped to its position. Clients must not construct
internal Table state. The independent model uses only list search and append.

Complexity target under pinned native array lowering: length/limit O(1), resolve
O(1) slot access plus retaining its string value; insert amortized O(1) reverse
storage work, with occasional O(n) Vec growth. Forward lookup/update visits
O(sum_i log(s_i+1)) sibling nodes over the examined prefixes, where s_i is the
number of distinct next characters at that prefix, plus O(L+1) terminal/path
work. Less/more traversal is balanced; same traversal consumes a character.
This is a source-derived bound conditional on the representation invariant,
not a universal machine-checked balance theorem. Lookup reconstructs its owned
path. Native measurements show faster common-prefix workloads but up to 1.61x
the old Base Map time for sorted single-character names; see STYLE_CAMPAIGN.md.
Pure core contains no IO or unsafe declarations. Native/JS behavior and GPU
execution are distinct evidence categories; no GPU support claim is made.


Reproducibility and namespaces: IDs follow first successful intern order. The
same ordered sequence of names and limit yields the same IDs; reordered first
insertions can yield different IDs across builds. Callers must control traversal
order and must not serialize incidental allocation order as canonical artifact
order. This release provides no canonical remapping or cross-build identity.
One table has one exact-string namespace. Callers manage distinct namespaces
using separate tables plus an external namespace identity, or an injective
namespace/name encoding. A bare U32 from another table is not a valid scoped
reference, even when its number happens to resolve locally.

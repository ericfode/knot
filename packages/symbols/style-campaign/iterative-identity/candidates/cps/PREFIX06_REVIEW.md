# Independent balanced prefix-root trie review

Source: `packages/symbols/build/memetic-search/phase/06_prefix_root/main.bend`.
SHA-256: `8e44e7b0b147ad90cee9c049d62d44d8ba14bcbf0b7b07bc45044c24d2eacbeb`.
This read-only review found no concrete functional or balancing defect.
It is source reasoning plus additive finite oracle evidence, not a universal proof.

## Structural obligations

Each complete prefix is Vacant, a black-root character sibling tree, or Here
followed by such a tree. Here cannot occur on a less/more edge. That invariant is
essential to get's direct Fork+SNil -> None branch: unlike unbalanced04, there can
be no empty suffix hidden in a less child.

The insertion cases preserve this partition. LT and GT receive SCon again, so
lateral descent cannot create Here. New Here nodes arise only when inserting an
empty name at the complete root or into a same child after consuming a character.
Updating an existing Here replaces its ID without nesting another Here. Recursion
through Here modifies only its more tree. Trie.black crosses the optional Here
and blackens the character root, so neither the complete root nor a same-prefix
root retains a red root after Trie.put.

All four balance patterns are the standard red-red insertion rotations. In each
case the character and its same subtree stay together: x/xx, y/yy, z/zz and
char/same. The reconstructed order is preserved and every affine a/b/c/d subtree
occurs exactly once. Rotations involve only less/more edges. Consequently they do
not treat a next-character prefix root as part of a sibling red-black tree.

On equal-character insertion, only the independent same trie changes, and that
trie is blackened immediately. The outer sibling node's color and less/more
branches remain unchanged; no outer balance is required. On lateral insertion,
standard balance propagation handles the possible red-red edge, with the public
put blackening the final root.

## Observable behavior

The separate terminal does not alias Char code 0. All character comparisons use
U32.cmp, exactly as Base Char.cmp. Only EQ consumes the head. Get reconstructs the
chosen path, preserving observations. The public interning sequence still probes
before capacity and publishes the forward binding only after successful Vec.push;
old IDs and full-table repeats remain unchanged. Failure retains both stores.

## Costs

Assuming the red-black invariant, a prefix's character sibling descent is
logarithmic in that prefix's distinct next characters. A length-L query therefore
visits O(sum over encountered prefixes of log(k_prefix+1)) sibling nodes plus
at most one Here per prefix, bounded by O((L+1) log(n+1)). Native U32 comparisons
and node reconstruction are constant work per visited node; new suffix insertion
also creates O(remaining length) nodes. The same edges remain independent prefix
roots, so sorted first-character input no longer makes a linear sibling chain.
This bound relies on the invariant and does not replace the author's independent
finite invariant checker or the paired native benchmark.

Get still reconstructs paths and creates continuation closures. Complete names
remain in the pinned Vec, while the forward trie stores characters again. Neither
allocation counts nor memory use are measured by the current wall-time harness.
Long character depth can still cause a deep call chain even with balanced siblings.

## Additive evidence and backend domain

The fixture `review-extra/extra.bend` invokes the unchanged cases.check,
observe.run, model.run and protocol comparisons. It adds mixed NUL/prefix names,
ordered/reverse one-codepoint names, valid scalar boundaries, supplementary
Unicode prefixes, and all six orders of three nonempty child payloads with their
prefix terminal inserted before/after. The latter exercises the prefix-root
partition and movement of payload subtrees through all insertion orders without
asserting the candidate's internal shape.

Every operation observes reply, length, limit, and every reverse name via the
frozen observer. The valid-scalar suite contains 1268 commands. Native-only raw
U32 boundaries add 208 commands. Compiled JS rejects surrogate 55296 and maximum
U32 4294967295 before observation; native accepts the same oracle probes. This
lane difference was first demonstrated on the unchanged baseline. Preserve it
rather than claiming raw-U32 String interoperability on JS.

The existing universal package laws still do not prove arbitrary nonempty
forward-trie refinement or red-black balance. Their checked state is useful but
does not expand their original scope. Original representation-specific SPEC
text must be updated if the new structure is retained.

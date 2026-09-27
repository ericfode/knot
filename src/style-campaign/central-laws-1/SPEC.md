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

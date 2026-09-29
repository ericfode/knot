<!-- prechecks packet v1; rule=required-laws-met; increment=fields-wasm; head=3868b119f8ba; base=185b7d5ffad5; builder=scripts/prechecks/packets@3a2ef420dff1; sources: tests/compiler-fields-wasm/LAWS.bend@3868b119 sha256=f5ef175cc720ec4e8d2da95ae42f876fae92f295ed1b0d6dab3c53e10fe26aa9 -->
# Claim
Required laws (verbatim from the increment manifest):

- Five checked capability/representation/erasure helper laws, not general compiler or memory refinement.

# Evidence
Operation-to-law matrix computed from the sources:

| file | law | for-binders | PROOF filled | statement |
|---|---|---|---|---|
| tests/compiler-fields-wasm/LAWS.bend | enum_capability_preserved | 1 | yes | {W.capability(W.Enum{},types) == K.enum_profile(types) : Result<S.Error,Unit>} |
| tests/compiler-fields-wasm/LAWS.bend | fields_capability_follows_checking | 1 | yes | {W.capability(W.Fields{},types) == Done{Unit{}} : Result<S.Error,Unit>} |
| tests/compiler-fields-wasm/LAWS.bend | erased_constructor_still_has_a_cell | 4 | yes | {W.fielded(Con{C.Constructor{token,[C.Parameter{name,0,type_id}]},rest}) == True{} : Bool} |
| tests/compiler-fields-wasm/LAWS.bend | erased_argument_takes_no_slot | 13 | yes | {W.lower(1n+n,W.Cell{Con{head,tail},Con{C.Parameter{token,0,type_id},params},slots,tag},heap,functions,locals, |
| tests/compiler-fields-wasm/LAWS.bend | erased_pattern_keeps_offset_and_locals | 15 | yes | {W.lower(1n+n,W.Unpack{Con{C.Binding{token,level,0,type_id,parameter,known},tail},pointer,offset,body},heap,fu |

Recorded obligations and limits:

(none recorded)

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.

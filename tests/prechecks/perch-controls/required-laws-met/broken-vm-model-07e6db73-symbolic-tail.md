<!-- prechecks packet v1; rule=required-laws-met; increment=vm-model; head=07e6db733079; base=cea554abc93f; builder=scripts/prechecks/packets@3a2ef420dff1; sources: vm/LAWS.bend@07e6db73 sha256=ff62c0f9b9dcfa2e1a506a1c435224a95d2a707ef0f430d3a2b51c0454c0fee9 -->
# Claim
Required laws (verbatim from the increment manifest):

- the codec round trip, on a hand-written plan and on five golden images;
- four refusal reasons, and bounded validator soundness: every single-word mutation of `value-on`'s function, constant and node sections is refused or runs soundly;
- §4's resource limits on `value-on`'s function record: a `slots` of 65,537 is `Exhausted` kind 2 `slots`, one of 65,536 is within the limit (and refused by the validator's exactness), and an arity of 4,097 that the record cannot hold is the malformed `function record`, not the arity limit;
- symbolic machine equations over arbitrary states: an entry at fuel 0 is Exhausted, a finished machine is final, tail position, the Nat bounds, `x/0`, `x%0` and shifts by 32 or more;
- one audited run per fixture image (a Book per node family and a Program): its answer, the RC audit at every transition and zero live mortal cells after it;
- audited runs of plans encoded in the law: a tags-mode Case on Char selects Chr for the code of 'A'; a key-mode Case on Char admits and selects the key 0xffffffff; a key Branch and a Default answer a `none` parameter in a U32 Case (arm fit, §3); a Nat word spells its type's own constructor names; and completing Chr on a laundered Pair stops `HostFailure image ill-typed` with every count balanced;
- §8's byte measure: `text_size` counts UTF-8 bytes, not scalars.

# Evidence
Operation-to-law matrix computed from the sources:

| file | law | for-binders | PROOF filled | statement |
|---|---|---|---|---|
| vm/LAWS.bend | words_round_trip | 0 | yes | {W.pack(W.unpack([0,1,255,256,2147483648,4294967295,1196247371])) == [0,1,255,256,2147483648,4294967295,119624 |
| vm/LAWS.bend | plan_encodes_image | 0 | yes | {E.encode(flag_plan()) == value_on() : List<&2,U32>} |
| vm/LAWS.bend | image_decodes_plan | 0 | yes | {D.decode(value_on()) == Done{flag_plan()} : Result<W.Stop,W.Plan>} |
| vm/LAWS.bend | images_canonical | 0 | yes | {canonical(fixtures()) == True{} : Bool} # ---------------------------------------------------------------- va |
| vm/LAWS.bend | magic_refused | 0 | yes | {E.admit(H.replaced(value_on(),0,0)) == Fail{W.Refused{"image","magic"}} : Result<W.Stop,W.Plan>} |
| vm/LAWS.bend | opcode_refused | 0 | yes | {E.admit(H.replaced(value_on(),59,13)) == Fail{W.Refused{"image","node record"}} : Result<W.Stop,W.Plan>} |
| vm/LAWS.bend | tag_refused | 0 | yes | {E.admit(H.replaced(value_on(),61,2)) == Fail{W.Refused{"image","validator: main: value is not a nullary const |
| vm/LAWS.bend | layout_refused | 0 | yes | {E.admit(H.replaced(value_on(),4,W.none())) == Fail{W.Refused{"image","noncanonical"}} : Result<W.Stop,W.Plan> |
| vm/LAWS.bend | slots_past_limit | 0 | yes | {E.admit(H.replaced(value_on(),54,65537)) == Fail{W.Exhausted{2,"slots"}} : Result<W.Stop,W.Plan>} |
| vm/LAWS.bend | slots_at_limit | 0 | yes | {E.admit(H.replaced(value_on(),54,65536)) == Fail{W.Refused{"image","validator: main: slots 65536, reached 0"} |
| vm/LAWS.bend | arity_beyond_record | 0 | yes | {E.admit(H.replaced(value_on(),53,4097)) == Fail{W.Refused{"image","function record"}} : Result<W.Stop,W.Plan> |
| vm/LAWS.bend | mutations_sound | 0 | yes | {A.all_sound(A.mutations(13n,value_on(),49),100000n,1000000) == True{} : Bool} # ----------------------------- |
| vm/LAWS.bend | entry_needs_fuel | 8 | yes | {M.entered(code,M.Callee{f},ops,stack,heap,M.Meter{0,calls,quantum},out) == Fail{W.Exhausted{1,"fuel"}} : Resu |
| vm/LAWS.bend | finished_is_final | 6 | yes | {M.step(code,M.Machine{M.Finished{outcome},stack,heap,meter,out}) == Done{M.Machine{M.Finished{outcome},stack, |
| vm/LAWS.bend | tail_skips_scopes | 0 | yes | {M.tail([H.Scope{2},H.Scope{1},H.Call{0}]) == True{} : Bool} |
| vm/LAWS.bend | operands_are_not_tail | 0 | yes | {M.tail([H.Scope{1},H.Gather{0,2,Nil{}},H.Call{0}]) == False{} : Bool} |
| vm/LAWS.bend | nat_sum_bound | 1 | yes | {H.nat_sum(heap,4294967295,1) == Fail{W.Exhausted{2,"NatRange"}} : Result<W.Stop,H.Cell>} |
| vm/LAWS.bend | nat_product_bound | 1 | yes | {H.nat_product(heap,65536,65536) == Fail{W.Exhausted{2,"NatRange"}} : Result<W.Stop,H.Cell>} |
| vm/LAWS.bend | division_by_zero | 5 | yes | {H.computed(3n,code,heap,a,b,x,0) == Done{H.Cell{heap,1}} : Result<W.Stop,H.Cell>} |
| vm/LAWS.bend | remainder_by_zero | 5 | yes | {H.computed(4n,code,heap,a,b,x,0) == H.word_of(heap,x) : Result<W.Stop,H.Cell>} |
| vm/LAWS.bend | wide_shifts_vanish | 1 | yes | {H.shifted(True{},a,32) == 0 : U32} # ---------------------------------------------------------------- runs: a |
| vm/LAWS.bend | value_on_runs | 0 | yes | {ran(value_on()) == described(0,1,"On{}") : Summary} |
| vm/LAWS.bend | closure_captures_runs | 0 | yes | {ran(closure_captures()) == described(1,0,"Pair{On{},Off{}}") : Summary} |
| vm/LAWS.bend | recursion_map_runs | 0 | yes | {ran(recursion_map()) == described(1,1,"Push{Off{},Push{On{},Stop{}}}") : Summary} |
| vm/LAWS.bend | string_append_mortal_runs | 0 | yes | {ran(string_append_mortal()) == described(0,1,"True{}") : Summary} |
| vm/LAWS.bend | foreign_print_runs | 0 | yes | {ran(foreign_print()) == Summary{M.Emitted{},True{},0,[M.text("vm")]} : Summary} # --------------------------- |
| vm/LAWS.bend | char_case_selects_chr | 0 | yes | {ran(E.encode(char_book("pick",W.Case{2,0,1,0,[Some{W.Branch{0,1,1,W.Value{2,1}}}],None{}},2,65))) == describe |
| vm/LAWS.bend | key_max_selected | 0 | yes | {ran(E.encode(char_book("top",W.Case{2,0,1,1,[Some{W.Branch{4294967295,1,0,W.Value{2,1}}}],Some{W.Default{W.Va |
| vm/LAWS.bend | arms_fit_their_case | 0 | yes | {ran(E.encode(key_arms())) == described(0,1,"True{}") : Summary} # §8 bounds the tree's UTF-8 bytes: 'A', 'ü', |
| vm/LAWS.bend | text_size_counts_bytes | 0 | yes | {M.text_size([65,252,8364,128512]) == 10 : U32} # main() -> Nat = 2n over Nat{Z, ü}: a Nat word spells its typ |
| vm/LAWS.bend | nat_spells_its_names | 0 | yes | {ran(E.encode(named_nat())) == described(0,1,"ü{ü{Z{}}}") : Summary} # main() -> Flag = let c = Chr{id(Pair{Of |
| vm/LAWS.bend | chr_inspects_its_operand | 0 | yes | {stop_of(ran(E.encode(laundered_chr()))) == Some{W.Refused{"image","ill-typed"}} : Maybe<&2,W.Stop>} |

Recorded obligations and limits:

(none recorded)

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.

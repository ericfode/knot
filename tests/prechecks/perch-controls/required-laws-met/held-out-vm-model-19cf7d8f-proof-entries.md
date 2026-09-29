<!-- prechecks packet v1; rule=required-laws-met; increment=vm-model; head=19cf7d8f71ff; base=5517f2638f3e; builder=scripts/prechecks/packets@3a2ef420dff1; sources: vm/LAWS.bend@19cf7d8f sha256=8bbc21f67c5c4bfe563e1b3f85e0b3341c227d59d6a3e3139a82451b3641df89 -->
# Claim
Required laws (verbatim from the increment manifest):

- vm-model adds checked proof entries for the codec round trip, bounded validator soundness, the RC edge audit and zero leaks.

# Evidence
Operation-to-law matrix computed from the sources:

| file | law | for-binders | PROOF filled | statement |
|---|---|---|---|---|
| vm/LAWS.bend | words_round_trip | 0 | yes | {W.pack(W.unpack([0,1,255,256,2147483648,4294967295,1196247371])) == [0,1,255,256,2147483648,4294967295,119624 |
| vm/LAWS.bend | plan_encodes_image | 0 | yes | {E.encode(flag_plan()) == value_on() : List<&2,U32>} |
| vm/LAWS.bend | image_decodes_plan | 0 | yes | {D.decode(value_on()) == Done{flag_plan()} : Result<String,W.Plan>} |
| vm/LAWS.bend | images_canonical | 0 | yes | {canonical(fixtures()) == True{} : Bool} # ---------------------------------------------------------------- va |
| vm/LAWS.bend | magic_refused | 0 | yes | {E.admit(H.replaced(value_on(),0,0)) == Fail{W.Refused{"image","magic"}} : Result<W.Stop,W.Plan>} |
| vm/LAWS.bend | opcode_refused | 0 | yes | {E.admit(H.replaced(value_on(),59,13)) == Fail{W.Refused{"image","node record"}} : Result<W.Stop,W.Plan>} |
| vm/LAWS.bend | tag_refused | 0 | yes | {E.admit(H.replaced(value_on(),61,2)) == Fail{W.Refused{"image","validator: main: value is not a nullary const |
| vm/LAWS.bend | layout_refused | 0 | yes | {E.admit(H.replaced(value_on(),4,W.none())) == Fail{W.Refused{"image","noncanonical"}} : Result<W.Stop,W.Plan> |
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

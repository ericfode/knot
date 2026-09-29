import Base
import ./syntax.bend as S
import ./matrix.bend as M
import ./scope.bend as E
import ./matrix-LAWS.bend as L
import ./recursion-PROOF.bend as Earlier
import ./lowering-PROOF.bend as Lowering

def L.selection_congruence(keep,arm,pattern,body,tail,wanted,proof):
  match keep:
    case False{}: proof
    case True{}:
      Equal.cong(List<&2,S.Token>,List<&2,S.Token>,xs => Con{arm,xs},L.identities(tail),wanted,proof)

def L.specialization_preserves_first_match(rows,ctor,fields,level):
  match rows:
    case Nil{}: {==}
    case Con{S.Arm{arm,S.Sequence{Con{S.Constructor{token,args},rest}},body},tail}:
      L.selection_congruence(String.eq(S.text(token),S.text(ctor)),arm,
        S.Sequence{List.append(&2,S.Node,args,rest)},body,M.specialize(tail,ctor,fields,level),L.selected(tail,ctor),
        L.specialization_preserves_first_match(tail,ctor,fields,level))
    case Con{S.Arm{arm,S.Sequence{Con{S.Variable{token},rest}},body},tail}:
      Equal.cong(List<&2,S.Token>,List<&2,S.Token>,xs => Con{arm,xs},
        L.identities(M.specialize(tail,ctor,fields,level)),L.selected(tail,ctor),
        L.specialization_preserves_first_match(tail,ctor,fields,level))
    case Con{S.Arm{arm,S.Sequence{Con{S.Promotion{token},rest}},body},tail}:
      Equal.cong(List<&2,S.Token>,List<&2,S.Token>,xs => Con{arm,xs},
        L.identities(M.specialize(tail,ctor,fields,level)),L.selected(tail,ctor),
        L.specialization_preserves_first_match(tail,ctor,fields,level))
    case Con{S.Arm{arm,S.Sequence{Con{S.Call{a0,a1},rest}},body},tail}: L.specialization_preserves_first_match(tail,ctor,fields,level)
    case Con{S.Arm{arm,S.Sequence{Con{S.Binding{a0,a1,a2,a3,a4},rest}},body},tail}: L.specialization_preserves_first_match(tail,ctor,fields,level)
    case Con{S.Arm{arm,S.Sequence{Con{S.Match{a0,a1,a2},rest}},body},tail}: L.specialization_preserves_first_match(tail,ctor,fields,level)
    case Con{S.Arm{arm,S.Sequence{Con{S.Arm{a0,a1,a2},rest}},body},tail}: L.specialization_preserves_first_match(tail,ctor,fields,level)
    case Con{S.Arm{arm,S.Sequence{Con{S.Matrix{a0,a1,a2,a3},rest}},body},tail}: L.specialization_preserves_first_match(tail,ctor,fields,level)
    case Con{S.Arm{arm,S.Sequence{Con{S.Decision{a0,a1,a2,a3,a4},rest}},body},tail}: L.specialization_preserves_first_match(tail,ctor,fields,level)
    case Con{S.Arm{arm,S.Sequence{Con{S.Remainder{a0,a1,a2},rest}},body},tail}: L.specialization_preserves_first_match(tail,ctor,fields,level)
    case Con{S.Arm{arm,S.Sequence{Con{S.Alias{a0,a1,a2,a3},rest}},body},tail}: L.specialization_preserves_first_match(tail,ctor,fields,level)
    case Con{S.Arm{arm,S.Sequence{Con{S.Parameter{a0,a1,a2},rest}},body},tail}: L.specialization_preserves_first_match(tail,ctor,fields,level)
    case Con{S.Arm{arm,S.Sequence{Con{S.Datatype{a0,a1,a2},rest}},body},tail}: L.specialization_preserves_first_match(tail,ctor,fields,level)
    case Con{S.Arm{arm,S.Sequence{Con{S.Function{a0,a1,a2,a3},rest}},body},tail}: L.specialization_preserves_first_match(tail,ctor,fields,level)
    case Con{S.Arm{arm,S.Sequence{Con{S.Sequence{a0},rest}},body},tail}: L.specialization_preserves_first_match(tail,ctor,fields,level)
    case Con{S.Arm{arm,S.Sequence{Nil{}},body},tail}: L.specialization_preserves_first_match(tail,ctor,fields,level)
    case Con{S.Arm{arm,S.Variable{a0},body},tail}: L.specialization_preserves_first_match(tail,ctor,fields,level)
    case Con{S.Arm{arm,S.Promotion{a0},body},tail}: L.specialization_preserves_first_match(tail,ctor,fields,level)
    case Con{S.Arm{arm,S.Constructor{a0,a1},body},tail}: L.specialization_preserves_first_match(tail,ctor,fields,level)
    case Con{S.Arm{arm,S.Call{a0,a1},body},tail}: L.specialization_preserves_first_match(tail,ctor,fields,level)
    case Con{S.Arm{arm,S.Binding{a0,a1,a2,a3,a4},body},tail}: L.specialization_preserves_first_match(tail,ctor,fields,level)
    case Con{S.Arm{arm,S.Match{a0,a1,a2},body},tail}: L.specialization_preserves_first_match(tail,ctor,fields,level)
    case Con{S.Arm{arm,S.Arm{a0,a1,a2},body},tail}: L.specialization_preserves_first_match(tail,ctor,fields,level)
    case Con{S.Arm{arm,S.Matrix{a0,a1,a2,a3},body},tail}: L.specialization_preserves_first_match(tail,ctor,fields,level)
    case Con{S.Arm{arm,S.Decision{a0,a1,a2,a3,a4},body},tail}: L.specialization_preserves_first_match(tail,ctor,fields,level)
    case Con{S.Arm{arm,S.Remainder{a0,a1,a2},body},tail}: L.specialization_preserves_first_match(tail,ctor,fields,level)
    case Con{S.Arm{arm,S.Alias{a0,a1,a2,a3},body},tail}: L.specialization_preserves_first_match(tail,ctor,fields,level)
    case Con{S.Arm{arm,S.Parameter{a0,a1,a2},body},tail}: L.specialization_preserves_first_match(tail,ctor,fields,level)
    case Con{S.Arm{arm,S.Datatype{a0,a1,a2},body},tail}: L.specialization_preserves_first_match(tail,ctor,fields,level)
    case Con{S.Arm{arm,S.Function{a0,a1,a2,a3},body},tail}: L.specialization_preserves_first_match(tail,ctor,fields,level)
    case Con{S.Variable{a0},tail}: L.specialization_preserves_first_match(tail,ctor,fields,level)
    case Con{S.Promotion{a0},tail}: L.specialization_preserves_first_match(tail,ctor,fields,level)
    case Con{S.Constructor{a0,a1},tail}: L.specialization_preserves_first_match(tail,ctor,fields,level)
    case Con{S.Call{a0,a1},tail}: L.specialization_preserves_first_match(tail,ctor,fields,level)
    case Con{S.Binding{a0,a1,a2,a3,a4},tail}: L.specialization_preserves_first_match(tail,ctor,fields,level)
    case Con{S.Match{a0,a1,a2},tail}: L.specialization_preserves_first_match(tail,ctor,fields,level)
    case Con{S.Matrix{a0,a1,a2,a3},tail}: L.specialization_preserves_first_match(tail,ctor,fields,level)
    case Con{S.Decision{a0,a1,a2,a3,a4},tail}: L.specialization_preserves_first_match(tail,ctor,fields,level)
    case Con{S.Remainder{a0,a1,a2},tail}: L.specialization_preserves_first_match(tail,ctor,fields,level)
    case Con{S.Alias{a0,a1,a2,a3},tail}: L.specialization_preserves_first_match(tail,ctor,fields,level)
    case Con{S.Parameter{a0,a1,a2},tail}: L.specialization_preserves_first_match(tail,ctor,fields,level)
    case Con{S.Datatype{a0,a1,a2},tail}: L.specialization_preserves_first_match(tail,ctor,fields,level)
    case Con{S.Function{a0,a1,a2,a3},tail}: L.specialization_preserves_first_match(tail,ctor,fields,level)
    case Con{S.Sequence{a0},tail}: L.specialization_preserves_first_match(tail,ctor,fields,level)

def L.irrefutable_specialization(arm,name,rest,body,rows,ctor,fields,level): {==}
def L.irrefutable_default(arm,name,rest,body,rows,level): {==}
def L.first_row_selected(token,arm,body,rows,types,scope): {==}
def L.lowering_work_exhaustion(token,columns,rows,types,scope): {==}
def L.irrefutable_lowering_witness(): {==}
def L.exhaustive_matrix_witness(): {==}
def L.irrefutable_first_row_witness(): {==}
def L.erased_alias_stays_erased(name,alias,known): {==}
def L.alias_preserves_descent_and_identity(name,alias): {==}
def L.parameter_alias_promotes(name,alias): {==}
def L.let_alias_keeps_quantity(name,alias,mark,known): {==}
def L.destructured_promotion_is_unbound(name,other): {==}
def L.later_match_binds_promotion(name,other): {==}
def L.leaf_binds_promotion(name): {==}
def L.leaf_closes_frontier(name): {==}
def L.destructured_promotion_witness(): {==}
def L.destructured_field_promotion_witness(): {==}
def L.bound_promotion_witness(): {==}
def L.split_binds_promotion_witness(): {==}
def L.empty_match_binds_promotion_witness(): {==}
def L.refined_flat_let_witness(): {==}
def L.refined_matrix_let_witness(): {==}
def L.residual_let_witness(): {==}
def L.annotated_let_witness(): {==}

def L.remainder_omits_split(head,tail,ctor,split):
  Equal.cong(Bool,List<&2,S.Token>,found =>
    S.choose(List<&2,S.Token>,found,u => M.remaining(tail,ctor),u => Con{head,M.remaining(tail,ctor)}),
    S.matches(head,S.text(ctor)),True{},split)
def L.remainder_keeps_other(head,tail,ctor,other):
  Equal.cong(Bool,List<&2,S.Token>,found =>
    S.choose(List<&2,S.Token>,found,u => M.remaining(tail,ctor),u => Con{head,M.remaining(tail,ctor)}),
    S.matches(head,S.text(ctor)),False{},other)
def L.remainder_drops_split_rows(arm,token,args,rest,body,rows,ctor,split):
  Equal.cong(Bool,List<&2,S.Node>,found =>
    S.choose(List<&2,S.Node>,found,u => M.without(rows,ctor),u =>
      Con{S.Arm{arm,S.Sequence{Con{S.Constructor{token,args},rest}},body},M.without(rows,ctor)}),
    S.matches(token,S.text(ctor)),True{},split)
def L.irrefutable_remainder(arm,name,rest,body,rows,ctor): {==}
def L.anonymous_reference_is_free(scope,at):
  match scope:
    case E.Scope{bindings,next,open,live,smaller}: {==}
def L.default_reference_stays_live(name,level,q,type_id,live): {==}
def L.empty_reference_stays_live(name,level,q,type_id,live): {==}
def L.pending_binder_witnesses_nothing(token,level,q,type_id,param,known,tail,types,pending,inside):
  Equal.cong(Bool,Bool,inside =>
    Bool.or(Bool.and(Bool.not(inside),Bool.and(U32.is_ne(q,0),E.empty(known,types,type_id))),E.witnessed(tail,types,pending)),
    E.contains(pending,level),True{},inside)
def L.erased_empty_is_not_dead(name): {==}
def L.live_empty_is_dead(name): {==}
def L.introduced_empty_witness(): {==}
def L.pending_empty_witness(): {==}
def L.let_alias_available(name,token): {==}
def L.terminal_expansion_preserves_budget(name,types,scope,work): {==}
def L.leaf_expansion_spends_one(token,arm,name,types,scope): {==}
def L.reference_is_not_rebuilt(token,level,type_id,tail,bindings,smaller): {==}
def L.rebuilt_descendant_witness(): {==}
def L.rebuilt_root_witness(): {==}
def L.changed_field_witness(): {==}
def L.retyped_constant_witness(): {==}
def L.rebuilt_descendant_call_witness(token,uses): {==}
def L.discarded_unknown_constructor_witness(): {==}
def L.discarded_valid_row_witness(): {==}
def L.short_row_witness(): {==}
def L.extra_field_witness(): {==}
def L.first_row_marks_witness(): {==}
def L.unmarked_first_row_witness(): {==}

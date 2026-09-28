import Base
import ./syntax.bend as S
import ./matrix.bend as M
import ./matrix-LAWS.bend as L
import ./recursion-PROOF.bend as Earlier

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
    case Con{S.Alias{a0,a1,a2,a3},tail}: L.specialization_preserves_first_match(tail,ctor,fields,level)
    case Con{S.Parameter{a0,a1,a2},tail}: L.specialization_preserves_first_match(tail,ctor,fields,level)
    case Con{S.Datatype{a0,a1,a2},tail}: L.specialization_preserves_first_match(tail,ctor,fields,level)
    case Con{S.Function{a0,a1,a2,a3},tail}: L.specialization_preserves_first_match(tail,ctor,fields,level)
    case Con{S.Sequence{a0},tail}: L.specialization_preserves_first_match(tail,ctor,fields,level)

def L.irrefutable_specialization(arm,name,rest,body,rows,ctor,fields,level): {==}
def L.irrefutable_default(arm,name,rest,body,rows,level): {==}
def L.first_row_selected(token,arm,body,rows,types,scope): {==}
def L.lowering_work_exhaustion(token,columns,rows,types,scope): {==}
def L.irrefutable_lowering_selects_first(): {==}
def L.exhaustive_matrix_has_no_missing_branch(): {==}
def L.erased_alias_stays_erased(name,alias,known,aliases): {==}
def L.alias_preserves_descent_and_identity(name,alias,aliases): {==}

def L.default_completes_missing_branch(name,fields,ctors,explicit,absent):
  Equal.cong(Bool,List<&2,S.Token>,found =>
    S.choose(List<&2,S.Token>,found,u => M.defaults(ctors,explicit),u => Con{name,M.defaults(ctors,explicit)}),
    M.named(explicit,name),False{},absent)

def L.default_does_not_repeat_explicit_branch(name,fields,ctors,explicit,present):
  Equal.cong(Bool,List<&2,S.Token>,found =>
    S.choose(List<&2,S.Token>,found,u => M.defaults(ctors,explicit),u => Con{name,M.defaults(ctors,explicit)}),
    M.named(explicit,name),True{},present)
def L.default_completion_witness(): {==}

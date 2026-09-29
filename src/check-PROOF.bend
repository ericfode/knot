import Base
import ./PROOF.bend as Front
import ./check-LAWS.bend as L
import ./syntax.bend as S
import ./core.bend as C
import ./scope.bend as E
import ./check.bend as K
import ./catalog.bend as G
import ./literal-matrix.bend as M
import ./literal-offset.bend as N

def L.empty_sequence_preserves_uses(uses,token):
  {==}
def L.single_argument_keeps_uses(uses,token):
  match uses:
    case Nil{}: {==}
    case Con{h,t}:
      %L.single_argument_keeps_uses(t,token) : {Done{Con{h,t}} == S.bind(List<&2,U32>,List<&2,U32>,_,rest => Done{Con{h,rest}}) : Result<S.Error,List<&2,U32>>}
      {==}
def L.repeated_affine_level(token):
  {==}
def L.live_erased_occurrence(token,level,type_id):
  {==}
def L.erased_occurrence_preserves_identity(token,level,type_id):
  {==}
def L.refined_constructor_is_fresh(token,type_id,tag):
  {==}
def L.refined_value_needs_annotation(token,uses,type_id,tag):
  {==}
def L.refined_construct_needs_annotation(token,fields,args,uses,type_id,tag):
  {==}
def L.unrefined_binder_is_inferable(token,uses,level,type_id):
  {==}
def L.annotation_admits_constructor(token,tag):
  {==}
def L.nearest_binding_wins(tail,level):
  {==}
def L.no_checker_budget(node):
  {==}
def L.dead_arm_invalid(phase,code,at):
  {==}
def L.dead_arm_exhausted(phase,at):
  {==}
def L.installed_literal_type(token,target,spelling):
  {==}
def L.spelled_own_literal(token,fields):
  {==}
def L.unspelled_literal(token,fields):
  {==}
def L.word_spells_any_target(token,number,ctors):
  {==}
def L.untargeted_literal(token,spelling):
  {==}
def L.offset_spelling(token,current,bindings,next,live,smaller):
  {==}
def L.offset_lowering(token,count,tail,current,scope,n,term,uses,bounded,tailed):
  %tailed : {S.bind(C.Checked,C.Checked,_,inner => K.offset(inner,count,G.ConstructorRef{0,1},S.Token{"Succ",S.at(token)},0,[C.Parameter{S.Token{"pred",S.At{0,0,0,0}},1,0}])) ==
    Done{C.Checked{N.successors(U32.to_nat(count),term,S.Token{"Succ",S.at(token)},0,1,[C.Parameter{S.Token{"pred",S.At{0,0,0,0}},1,0}]),0,uses}} : Result<S.Error,C.Checked>}
  %bounded : {S.choose(Result<S.Error,C.Checked>,_,u => C.exhausted(C.Checked,S.Token{"Succ",S.at(token)}),u =>
      Done{C.Checked{N.successors(U32.to_nat(count),term,S.Token{"Succ",S.at(token)},0,1,[C.Parameter{S.Token{"pred",S.At{0,0,0,0}},1,0}]),0,uses}}) ==
    Done{C.Checked{N.successors(U32.to_nat(count),term,S.Token{"Succ",S.at(token)},0,1,[C.Parameter{S.Token{"pred",S.At{0,0,0,0}},1,0}]),0,uses}} : Result<S.Error,C.Checked>}
  {==}
def L.offset_bound(token,count,tail,current,scope,n,term,uses,beyond,tailed):
  %tailed : {S.bind(C.Checked,C.Checked,_,inner => K.offset(inner,count,G.ConstructorRef{0,1},S.Token{"Succ",S.at(token)},0,[C.Parameter{S.Token{"pred",S.At{0,0,0,0}},1,0}])) ==
    Fail{S.Exhausted{"check",S.at(token)}} : Result<S.Error,C.Checked>}
  %beyond : {S.choose(Result<S.Error,C.Checked>,_,u => C.exhausted(C.Checked,S.Token{"Succ",S.at(token)}),u =>
      Done{C.Checked{N.successors(U32.to_nat(count),term,S.Token{"Succ",S.at(token)},0,1,[C.Parameter{S.Token{"pred",S.At{0,0,0,0}},1,0}]),0,uses}}) ==
    Fail{S.Exhausted{"check",S.at(token)}} : Result<S.Error,C.Checked>}
  {==}

def L.binders_meet_registered_constructors(at): {==}

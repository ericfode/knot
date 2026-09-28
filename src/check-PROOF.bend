import Base
import ./PROOF.bend as Front
import ./syntax.bend as S
import ./core.bend as C
import ./scope.bend as E
import ./check-LAWS.bend as L

def L.empty_sequence_preserves_uses(uses,token):
  {==}
def L.repeated_affine_level(token):
  {==}
def L.live_erased_occurrence(token,level,type_id):
  {==}
def L.erased_occurrence_preserves_identity(token,level,type_id):
  {==}
def L.refined_constructor_is_fresh(token,type_id,tag):
  {==}
def L.nearest_binding_wins(tail,level):
  {==}
def L.def_reference(R,F,token,error,datatype,function,absent,present,untyped,defined):
  %Equal.sym(Result<S.Error,R>,datatype(token),Fail{absent},untyped) :
    {E.unbound(C.Binding,R,_,token,"type-level-term",
      E.unbound(C.Binding,F,function(token),token,"def-reference",Fail{error}))
     == Fail{S.Unsupported{"check","def-reference",S.at(token)}} : Result<S.Error,C.Binding>}
  %Equal.sym(Result<S.Error,F>,function(token),Done{present},defined) :
    {E.unbound(C.Binding,F,_,token,"def-reference",Fail{error})
     == Fail{S.Unsupported{"check","def-reference",S.at(token)}} : Result<S.Error,C.Binding>}
  {==}
def L.no_checker_budget(node):
  {==}

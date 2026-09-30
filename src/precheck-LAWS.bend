import Base
import ./syntax.bend as S
import ./core.bend as C
import ./scope.bend as E
import ./descent.bend as D
import ./matrix.bend as M
import ./parse-patterns.bend as V
import ./residual.bend as R
import ./check.bend as K

def x() -> S.Token:
  S.Token{"x",S.At{4,5,1,4}}

# Helper equations and ground normalization; no general checker theorem.
law wildcard_has_no_value:
  for +at: S.At
  for bindings: List<&2,C.Binding>
  for next: U32
  for open: List<&2,U32>
  for live: Bool
  for aliases: List<&2,D.Alias>
  {E.lookup(E.Scope{bindings,next,open,live,aliases},S.Token{"_",at}) ==
    Fail{S.Invalid{"check","free-name",at}} : Result<S.Error,C.Binding>}

law empty_variable_column_is_unsupported:
  for name: S.Token
  for data: Bool
  for +token: S.Token
  for next: Unit -> Result<S.Error,S.Node>
  {M.variable_type(C.Datatype{name,data,Nil{}},token,next) ==
    Fail{S.Unsupported{"check","empty-datatype",S.at(token)}} : Result<S.Error,S.Node>}

law repeated_uses_saturate:
  {R.join(R.Usage{1,False{}},R.Usage{1,False{}},False{}) == R.Usage{2,False{}} : R.Usage}

law exclusive_uses_take_maximum:
  {R.join(R.Usage{1,False{}},R.Usage{1,False{}},True{}) == R.Usage{1,False{}} : R.Usage}

law shadow_hides_residual_name:
  {R.hide([x()],x()) == Nil{} : List<&2,S.Token>}

law repeated_residual_occurrences:
  {R.measure(8n,R.Term{S.Call{S.Token{"both",S.At{0,4,1,0}},[S.Variable{x()},S.Variable{x()}]}},[x()],0,x()) ==
    Done{R.Usage{2,False{}}} : Result<S.Error,R.Usage>}

law forward_pattern_has_no_constructor:
  {V.arity([S.Constructor{S.Token{"On",S.At{20,22,3,0}},Nil{}}],S.Token{"On",S.At{4,6,1,4}}) == None{} : Maybe<&2,Nat>}

law source_exhaustion_gets_boundary:
  {K.located(Fail{S.Exhausted{"check",S.At{0,0,0,0}}},x()) ==
    Fail{S.Exhausted{"check",S.At{4,5,1,4}}} : Result<S.Error,C.Checked>}

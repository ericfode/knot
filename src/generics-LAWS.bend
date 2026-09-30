import Base
import ./syntax.bend as S
import ./core.bend as C
import ./types.bend as T
import ./generics.bend as G

# Boundary equations; recursive reconstruction and checker soundness are separate.
law reconstructed_needs_type:
  for +name: S.Token
  for +level: U32
  for +q: U32
  for +typ: T.Expr
  for +param: Bool
  for +term: C.Term
  for +token: S.Token
  for +env: G.Environment
  for next: C.Term -> T.Expr -> Result<S.Error,G.Checked>
  {G.variable(G.Binding{name,level,q,typ,param,Some{term}},token,None{},env,next)
    == C.invalid(G.Checked,"annotation-required",token) : Result<S.Error,G.Checked>}

law unrefined_inference:
  for +name: S.Token
  for +level: U32
  for +q: U32
  for +typ: T.Expr
  for +param: Bool
  for +token: S.Token
  for +env: G.Environment
  for next: C.Term -> T.Expr -> Result<S.Error,G.Checked>
  {G.variable(G.Binding{name,level,q,typ,param,None{}},token,None{},env,next)
    == G.occurrence(G.Binding{name,level,q,typ,param,None{}},token,env,next) : Result<S.Error,G.Checked>}

law annotated_occurrence:
  for +binding: G.Binding
  for +token: S.Token
  for +wanted: T.Expr
  for +env: G.Environment
  for next: C.Term -> T.Expr -> Result<S.Error,G.Checked>
  {G.variable(binding,token,Some{wanted},env,next)
    == G.occurrence(binding,token,env,next) : Result<S.Error,G.Checked>}

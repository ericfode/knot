import Base
import ./syntax.bend as S
import ./core.bend as C
import ./generic-catalog.bend as G
import ./generic-catalog-LAWS.bend as L

def L.empty_family(token,q,kind,params,generic): {==}
def L.type_level_definition(fuel,token,name,families,symbols,found):
  %Equal.sym(Maybe<&2,G.Symbol>,G.named(symbols,token),Some{G.Definition{name}},found) :
    {G.named_type(_,token,u =>
      S.bind(G.Named,G.Typed,G.family_named(families,token,0),reference =>
        G.bare(reference,token,mode => G.resolve(fuel,mode,families,symbols))))
     == Fail{S.Unsupported{"check","type-level-definition",S.at(token)}} : Result<S.Error,G.Typed>}
  {==}
def L.pattern_order(families,token,reference,found,later):
  %Equal.sym(Result<S.Error,G.ConstructorRef>,G.constructor_named(families,token,0),Done{reference},found) :
    {S.bind(G.ConstructorRef,G.ConstructorRef,_,+r =>
      S.choose(Result<S.Error,G.ConstructorRef>,G.visible(token,G.declaration(r)),u => Done{r},u =>
        C.invalid(G.ConstructorRef,"unknown-constructor",token)))
     == Fail{S.Invalid{"check","unknown-constructor",S.at(token)}} : Result<S.Error,G.ConstructorRef>}
  %Equal.sym(Bool,G.visible(token,G.declaration(reference)),False{},later) :
    {S.choose(Result<S.Error,G.ConstructorRef>,_,u => Done{reference},u =>
      C.invalid(G.ConstructorRef,"unknown-constructor",token))
     == Fail{S.Invalid{"check","unknown-constructor",S.at(token)}} : Result<S.Error,G.ConstructorRef>}
  {==}

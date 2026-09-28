import Base
import ./types-PROOF.bend as Types
import ./syntax.bend as S
import ./core.bend as C
import ./generic-catalog.bend as G
import ./type-erasure.bend as E
import ./wasm.bend as W
import ./type-erasure-LAWS.bend as L

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
def L.nominal_identity(index): {==}
def L.application_erases_argument(function,argument): {==}
def L.parameter_retains_quantity(token,q,typ): {==}
def L.plain_fields(token,params): {==}
def L.plain_arguments(token,args): {==}
def L.plain_bindings(token,params): {==}
def L.generic_fields(token,params): {==}
def L.generic_arguments(token,args): {==}
def L.generic_bindings(token,params): {==}
def L.generic_nullary_is_boxed(token,typ,tag): {==}
def L.plain_nullary_is_ordinal(token,typ,tag): {==}

def L.generic_constructor_uses_memory(token,params):
  match params:
    case Nil{}: {==}
    case Con{head,tail}: {==}

def L.generic_branch_uses_memory(token,params,tag,body):
  match params:
    case Nil{}: {==}
    case Con{head,tail}: {==}

def L.marker_retains_live_signature(token,params):
  match params:
    case Nil{}: {==}
    case Con{G.Parameter{name,+q,typ},+tail}:
      Equal.cong(List<&2,U32>,List<&2,U32>,
        xs => S.choose(List<&2,U32>,U32.is_eq(q,0),u => xs,u => Con{127,xs}),
        W.live_types(E.fields(token,tail,True{})),W.live_types(E.parameters(tail)),
        L.marker_retains_live_signature(token,tail))

def L.erased_argument_commutes(fuel,token,typ,params,head,args,level,caller,callee,body,frames,book): {==}
def L.erased_field_commutes(fuel,type_id,tag,token,typ,params,head,args,env,values,frames,book): {==}
def L.erased_pattern_commutes(fuel,token,level,typ,parameter,known,params,values,env,body,frames,book): {==}

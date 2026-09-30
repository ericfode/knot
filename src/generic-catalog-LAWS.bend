import Base
import ./syntax.bend as S
import ./types.bend as T
import ./generic-catalog.bend as G

# The generic catalog keeps the monomorphic catalog's empty-datatype boundary.
law empty_family:
  for token: S.Token
  for q: T.Expr
  for kind: T.Expr
  for params: List<&2,G.Parameter>
  for generic: Bool
  {G.header_kind(G.Typed{T.Sort{q},kind},token,params,Nil{},generic)
    == Fail{S.Unsupported{"check","empty-datatype",S.at(token)}} : Result<S.Error,G.Family>}

# A type name that resolves to a definition computes a type: Unsupported,
# whatever families the book declares.
law type_level_definition:
  for fuel: Nat
  for +token: S.Token
  for name: S.Token
  for families: List<&2,G.Family>
  for symbols: List<&2,G.Symbol>
  for found: {G.named(symbols,token) == Some{G.Definition{name}} : Maybe<&2,G.Symbol>}
  {G.resolve(1n+fuel,G.Expression{S.Variable{token}},families,symbols)
    == Fail{S.Unsupported{"check","type-level-definition",S.at(token)}} : Result<S.Error,G.Typed>}

# A constructor pattern above its datatype's declaration is unknown, as in
# the seed, although the datatype is declared later in the book.
law pattern_order:
  for families: List<&2,G.Family>
  for +token: S.Token
  for reference: G.ConstructorRef
  for found: {G.constructor_named(families,token,0) == Done{reference} : Result<S.Error,G.ConstructorRef>}
  for later: {G.visible(token,G.declaration(reference)) == False{} : Bool}
  {G.pattern_constructor(families,token)
    == Fail{S.Invalid{"check","unknown-constructor",S.at(token)}} : Result<S.Error,G.ConstructorRef>}

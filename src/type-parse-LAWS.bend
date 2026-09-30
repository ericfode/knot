import Base
import ./syntax.bend as S
import ./type-parse.bend as T
import ./type-parse.bend as P

# After a type argument only `,` and `>` continue the list. Any other token
# makes the argument a term (`Tag<On{}>`): Unsupported, never Invalid.
law term_argument:
  for +n: Nat
  for +head: S.Node
  for +token: S.Token
  for +rest: List<&2,S.Token>
  for close: {S.matches(token,">") == False{} : Bool}
  for comma: {S.matches(token,",") == False{} : Bool}
  {T.run(1n+n,T.ItemTail{head},Con{token,rest})
    == Fail{S.Unsupported{"parse","term-argument",S.at(token)}} : Result<S.Error,T.Parsed>}

# A marked bare binder is a parameter missing its type, never a quantity:
# rejected at the separator, where the seed expects `:`.
law marked_binder:
  for +fuel: Nat
  for +q: U32
  for +name: S.Token
  for +at: S.At
  for +rest: List<&2,S.Token>
  for word: {S.identifier(name) == True{} : Bool}
  for marked: {U32.is_eq(q,1) == False{} : Bool}
  {T.parameter_parts(fuel,True{},q,Con{name,Con{S.Token{",",at},rest}})
    == Fail{S.Invalid{"parse","parameter",at}} : Result<S.Error,T.Parsed>}

# A gap inside `&2` is Unsupported, never read as the glued literal.
law spaced_quantity:
  for +token: S.Token
  for +value: S.Token
  for +rest: List<&2,S.Token>
  for gap: {P.glued(token,value) == False{} : Bool}
  {P.read_quantity(token,Con{value,rest})
    == Fail{S.Unsupported{"parse","spacing",S.at(value)}} : Result<S.Error,P.Parsed>}

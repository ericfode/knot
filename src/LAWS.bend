import Base
import ./syntax.bend as S
import ./lex.bend as L
import ./parse.bend as P
import ./type-parse.bend as T

# These are focused frontend boundary laws, not parser/checker soundness.
law empty_source:
  for fuel: Nat
  {L.tokenize(fuel,"") == Done{[S.Token{"<eof>",S.At{0,0,1,0}}]} : Result<S.Error,List<&2,S.Token>>}

law word_source:
  for extra: Nat
  {L.tokenize(1n+extra,"a") == Done{[S.Token{"a",S.At{0,1,1,0}},S.Token{"<eof>",S.At{1,1,1,1}}]} : Result<S.Error,List<&2,S.Token>>}

law no_character_budget:
  for c: Char
  for tail: String
  {L.tokenize(0n,SCon{c,tail}) == Fail{S.Exhausted{"lex",S.At{0,0,1,0}}} : Result<S.Error,List<&2,S.Token>>}

law no_parser_budget:
  for +tokens: List<&2,S.Token>
  {P.parse(0n,tokens) == Fail{S.Exhausted{"parse",S.here(tokens)}} : Result<S.Error,P.Parsed>}

# Parser-only header acceptance; the catalog separately requires constructors.
# The parameter type touches the closing `>`, as lexed from `Type>`.
law generic_header:
  for +at: S.At
  {P.run(32n,P.Header{S.Token{"type",at},S.Token{"Box",at}},
      [S.Token{"<",at},S.Token{"-",at},S.Token{"A",at},S.Token{":",at},S.Token{"Type",S.At{13,17,1,13}},
       S.Token{">",S.At{17,18,1,17}},S.Token{"is",at},S.Token{"Type",at},S.Token{":",at},S.Token{"<eof>",at}])
    == Done{P.Parsed{S.Generic{S.Token{"Box",at},
      [S.TypedParameter{S.Token{"A",at},0,
        S.TypeKind{S.Token{"Type",S.At{13,17,1,13}},S.Quantity{S.Token{"Type",S.At{13,17,1,13}},1}}}],
      S.TypeKind{S.Token{"Type",at},S.Quantity{S.Token{"Type",at},1}},Nil{}},[S.Token{"<eof>",at}]}}
    : Result<S.Error,P.Parsed>}

law multiple_scrutinees:
  for +at: S.At
  for +rest: List<&2,S.Token>
  {P.run(1n,P.MatchTail{S.Token{"match",at},S.Variable{S.Token{"a",at}},0},Con{S.Token{"b",at},rest})
    == Fail{S.Unsupported{"parse","match-scrutinees",at}} : Result<S.Error,P.Parsed>}

law template_binder:
  for +at: S.At
  for +rest: List<&2,S.Token>
  {P.run(1n,P.Parameters{")"},Con{S.Token{"~",at},Con{S.Token{"x",at},Con{S.Token{":",at},rest}}})
    == Fail{S.Unsupported{"parse","template-binder",at}} : Result<S.Error,P.Parsed>}

law nonleading_template_binder:
  for +at: S.At
  for +head: S.Node
  for +rest: List<&2,S.Token>
  {P.run(1n,P.ListTail{")",head,True{},False{}},Con{S.Token{",",at},Con{S.Token{"~",at},rest}})
    == Fail{S.Invalid{"parse","parameter",at}} : Result<S.Error,P.Parsed>}

law destructuring_binding:
  for +at: S.At
  for +fields: List<&2,S.Node>
  for +rest: List<&2,S.Token>
  for plain: {Bool.or(P.starts(rest,"="),P.starts(rest,">")) == False{} : Bool}
  {P.reply(S.Constructor{S.Token{"Cell",at},fields},Con{S.Token{"=",at},rest})
    == Fail{S.Unsupported{"parse","destructuring-binding",at}} : Result<S.Error,P.Parsed>}

law equality_is_not_binding:
  for +at: S.At
  for +fields: List<&2,S.Node>
  for +rest: List<&2,S.Token>
  {P.reply(S.Constructor{S.Token{"Cell",at},fields},Con{S.Token{"=",at},Con{S.Token{"=",at},rest}})
    == Fail{S.Invalid{"parse","end-of-body",at}} : Result<S.Error,P.Parsed>}

law arrow_is_not_binding:
  for +at: S.At
  for +fields: List<&2,S.Node>
  for +rest: List<&2,S.Token>
  {P.reply(S.Constructor{S.Token{"Cell",at},fields},Con{S.Token{"=",at},Con{S.Token{">",at},rest}})
    == Fail{S.Invalid{"parse","end-of-body",at}} : Result<S.Error,P.Parsed>}

law parameter_type_application:
  for +at: S.At
  for +rest: List<&2,S.Token>
  {P.parameter(Con{S.Token{"xs",at},Con{S.Token{":",at},Con{S.Token{"List",at},Con{S.Token{"<",at},rest}}}})
    == Fail{S.Unsupported{"parse","parameter-type",at}} : Result<S.Error,P.Parsed>}

# A result type application is no longer a classified prefix; it enters the
# typed-result grammar, which parses the whole type expression.
law return_type_application:
  for +n: Nat
  for +at: S.At
  for +rest: List<&2,S.Token>
  {P.run(1n+n,P.FunctionTail{S.Token{"main",at},S.Sequence{Nil{}}},
    Con{S.Token{"-",at},Con{S.Token{">",at},Con{S.Token{"List",at},Con{S.Token{"<",at},rest}}}})
    == P.run(n,P.TypedResult{S.Token{"main",at},S.Sequence{Nil{}}},
    Con{S.Token{"-",at},Con{S.Token{">",at},Con{S.Token{"List",at},Con{S.Token{"<",at},rest}}}})
    : Result<S.Error,P.Parsed>}

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

law local_import:
  for +at: S.At
  for +rest: List<&2,S.Token>
  {P.run(1n,P.Header{S.Token{"import",at},S.Token{".",at}},Con{S.Token{"/",at},rest})
    == Fail{S.Unsupported{"parse","import",at}} : Result<S.Error,P.Parsed>}

law hash_import:
  for +at: S.At
  for +rest: List<&2,S.Token>
  {P.run(1n,P.Header{S.Token{"import",at},S.Token{"0x77a1a37baca5d86f62241cab956a1fb1",at}},Con{S.Token{"/",at},rest})
    == Fail{S.Unsupported{"parse","import",at}} : Result<S.Error,P.Parsed>}

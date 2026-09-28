import Base
import ./syntax.bend as S
import ./lex.bend as L
import ./parse.bend as P

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

# Prefix classification does not validate the unconsumed suffix.
law generic_header:
  for +at: S.At
  for +rest: List<&2,S.Token>
  {P.run(1n,P.Header{S.Token{"type",at},S.Token{"Box",at}},Con{S.Token{"<",at},rest})
    == Fail{S.Unsupported{"parse","generic-datatype",at}} : Result<S.Error,P.Parsed>}

# Two scrutinees form one ordered column sequence; an empty arm list is parsed.
law multiple_scrutinees:
  for +at: S.At
  {P.run(4n,P.MatchTail{S.Token{"match",at},S.Variable{S.Token{"a",at}},0},
      [S.Token{"b",at},S.Token{":",at},S.Token{"<eof>",at}])
    == Done{P.Parsed{S.Match{S.Token{"match",at},
      S.Sequence{[S.Variable{S.Token{"a",at}},S.Variable{S.Token{"b",at}}]},Nil{}},
      [S.Token{"<eof>",at}]}} : Result<S.Error,P.Parsed>}

law template_binder:
  for +at: S.At
  for +rest: List<&2,S.Token>
  {P.run(1n,P.Parameters{")"},Con{S.Token{"~",at},Con{S.Token{"x",at},Con{S.Token{":",at},rest}}})
    == Fail{S.Unsupported{"parse","template-binder",at}} : Result<S.Error,P.Parsed>}

law destructuring_binding:
  for +at: S.At
  for +fields: List<&2,S.Node>
  for +rest: List<&2,S.Token>
  {P.reply(S.Constructor{S.Token{"Cell",at},fields},Con{S.Token{"=",at},rest})
    == Fail{S.Unsupported{"parse","destructuring-binding",at}} : Result<S.Error,P.Parsed>}

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

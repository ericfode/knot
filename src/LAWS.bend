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

law return_type_application:
  for +at: S.At
  for +rest: List<&2,S.Token>
  {P.run(1n,P.FunctionTail{S.Token{"main",at},S.Sequence{Nil{}}},
    Con{S.Token{"-",at},Con{S.Token{">",at},Con{S.Token{"List",at},Con{S.Token{"<",at},rest}}}})
    == Fail{S.Unsupported{"parse","type-application",at}} : Result<S.Error,P.Parsed>}

law longer_result_type:
  for +at: S.At
  for +rest: List<&2,S.Token>
  {(P.run(1n,P.FunctionTail{S.Token{"main",at},S.Sequence{Nil{}}},
      Con{S.Token{"-",at},Con{S.Token{">",at},Con{S.Token{"IO",at},Con{S.Token{"(",at},rest}}}}),
    P.run(1n,P.FunctionTail{S.Token{"main",at},S.Sequence{Nil{}}},
      Con{S.Token{"-",at},Con{S.Token{">",at},Con{S.Token{"(",at},Con{S.Token{"Light",at},rest}}}}))
    == (Fail{S.Unsupported{"parse","result-type",at}},Fail{S.Unsupported{"parse","result-type",at}})
    : Result<S.Error,P.Parsed> & Result<S.Error,P.Parsed>}

law spaced_result_arrow:
  {P.run(1n,P.FunctionTail{S.Token{"main",S.At{4,8,1,4}},S.Sequence{Nil{}}},
    [S.Token{"-",S.At{11,12,1,11}},S.Token{">",S.At{13,14,1,13}},S.Token{"Light",S.At{15,20,1,15}},
     S.Token{":",S.At{20,21,1,20}},S.Token{"<eof>",S.At{21,21,1,21}}])
    == Fail{S.Invalid{"parse","function-result",S.At{11,12,1,11}}} : Result<S.Error,P.Parsed>}

law binding_type_application:
  for +at: S.At
  for +rest: List<&2,S.Token>
  {P.run(1n,P.AnnotatedBinding{S.Token{"xs",at},1,2},Con{S.Token{"List",at},Con{S.Token{"<",at},rest}})
    == Fail{S.Unsupported{"parse","type-application",at}} : Result<S.Error,P.Parsed>}

law parameter_type_operator:
  for +at: S.At
  for +rest: List<&2,S.Token>
  {(P.parameter(Con{S.Token{"p",at},Con{S.Token{":",at},Con{S.Token{"Light",at},Con{S.Token{"&",at},rest}}}}),
    P.parameter(Con{S.Token{"p",at},Con{S.Token{":",at},Con{S.Token{"Light",at},Con{S.Token{"|",at},rest}}}}))
    == (Fail{S.Unsupported{"parse","parameter-type",at}},Fail{S.Unsupported{"parse","parameter-type",at}})
    : Result<S.Error,P.Parsed> & Result<S.Error,P.Parsed>}

law binding_type_operator:
  for +at: S.At
  for +rest: List<&2,S.Token>
  {(P.run(1n,P.AnnotatedBinding{S.Token{"x",at},1,2},Con{S.Token{"Light",at},Con{S.Token{"&",at},rest}}),
    P.run(1n,P.AnnotatedBinding{S.Token{"f",at},1,2},Con{S.Token{"Light",at},Con{S.Token{"-",at},rest}}))
    == (Fail{S.Unsupported{"parse","binding-type",at}},Fail{S.Unsupported{"parse","binding-type",at}})
    : Result<S.Error,P.Parsed> & Result<S.Error,P.Parsed>}

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

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

law binding_type_application:
  for +at: S.At
  for +rest: List<&2,S.Token>
  {P.run(1n,P.AnnotatedBinding{S.Token{"xs",at},1,2},Con{S.Token{"List",at},Con{S.Token{"<",at},rest}})
    == Fail{S.Unsupported{"parse","type-application",at}} : Result<S.Error,P.Parsed>}

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

law malformed_name:
  for +at: S.At
  {P.names([S.Token{"f",at},S.Token{"x.",at}]) == Fail{S.Invalid{"parse","name",at}} : Result<S.Error,Unit>}

law name_shapes:
  {[P.malformed("x."),P.malformed("x..y"),P.malformed("x.1"),P.malformed("x.1a"),P.malformed("a.b_1"),P.malformed("_"),P.malformed("1.5"),P.malformed("<eof>")]
    == [True{},True{},True{},True{},False{},False{},False{},False{}] : List<&2,Bool>}

law dotted_binder_needs_a_parameter:
  for +at: S.At
  {P.binders(2n,S.Variable{S.Token{"x.y",at}},True{},Nil{})
    == Fail{S.Invalid{"parse","pattern-binder",at}} : Result<S.Error,Unit>}

law dotted_binder_repeats_a_parameter:
  for +at: S.At
  {P.binders(2n,S.Variable{S.Token{"x.y",at}},True{},[S.Parameter{S.Token{"x.y",at},1,S.Token{"U32",at}}])
    == Done{Unit{}} : Result<S.Error,Unit>}

law dotted_reference_binds_nothing:
  for +at: S.At
  {P.binders(2n,S.Variable{S.Token{"x.y",at}},False{},Nil{}) == Done{Unit{}} : Result<S.Error,Unit>}

law offset_tail_after_newline:
  for +rest: List<&2,S.Token>
  {P.run(2n,P.LiteralTail{S.Literal{S.Token{"1n",S.At{0,2,1,0}},1,1,Nil{}},True{}},
    Con{S.Token{"+",S.At{2,3,1,2}},Con{S.Token{"\n",S.At{3,4,1,3}},Con{S.Token{"p",S.At{6,7,2,2}},Con{S.Token{":",S.At{7,8,2,3}},rest}}}})
    == Done{P.Parsed{S.Offset{S.Token{"1n",S.At{0,2,1,0}},1,S.Variable{S.Token{"p",S.At{6,7,2,2}}}},Con{S.Token{":",S.At{7,8,2,3}},rest}}}
    : Result<S.Error,P.Parsed>}

# The seed reads a term after line breaks: around a list's items and a case pattern.
law list_across_lines:
  for +at: S.At
  for +rest: List<&2,S.Token>
  {P.run(5n,P.Term{False{}},Con{S.Token{"f",at},Con{S.Token{"(",at},Con{S.Token{"\n",at},Con{S.Token{"x",at},Con{S.Token{"\n",at},
    Con{S.Token{",",at},Con{S.Token{"\n",at},Con{S.Token{"y",at},Con{S.Token{"\n",at},Con{S.Token{")",at},rest}}}}}}}}}})
    == Done{P.Parsed{S.Call{S.Token{"f",at},[S.Variable{S.Token{"x",at}},S.Variable{S.Token{"y",at}}]},rest}} : Result<S.Error,P.Parsed>}

# The seed checks no arm-body column: `at` places the body anywhere.
law arm_across_lines:
  for +at: S.At
  {P.run(5n,P.Arms{0,0},[S.Token{"case",S.At{0,4,1,4}},S.Token{"\n",at},S.Token{"p",at},S.Token{"\n",at},S.Token{":",at},
    S.Token{"\n",at},S.Token{"q",at},S.Token{"<eof>",at}])
    == Done{P.Parsed{S.Sequence{[S.Arm{S.Token{"case",S.At{0,4,1,4}},S.Variable{S.Token{"p",at}},S.Variable{S.Token{"q",at}}}]},
      [S.Token{"<eof>",at}]}} : Result<S.Error,P.Parsed>}

# Under a `case` in column 4, a match takes only cases right of it, even from column 2.
law cases_right_of_parent:
  for +at: S.At
  for +rest: List<&2,S.Token>
  {P.run(3n,P.BodyAt{4},Con{S.Token{"match",S.At{0,5,1,2}},Con{S.Token{"m",at},Con{S.Token{":",at},Con{S.Token{"\n",at},
    Con{S.Token{"case",S.At{0,4,1,4}},rest}}}}})
    == Done{P.Parsed{S.Match{S.Token{"match",S.At{0,5,1,2}},S.Variable{S.Token{"m",at}},Nil{}},Con{S.Token{"case",S.At{0,4,1,4}},rest}}}
    : Result<S.Error,P.Parsed>}

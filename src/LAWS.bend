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

# A name is words joined by dots; a malformed word is rejected where it ends.
law name_words_witness:
  {[S.words("a.b_1.c",True{},0),S.words("x.",True{},0),S.words("a..b",True{},0),S.words("a.1",True{},0)]
    == [3,0,0,0] : List<&2,U32>}

law malformed_word_source:
  for extra: Nat
  {L.tokenize(2n+extra,"a.") == Fail{S.Invalid{"lex","name",S.At{0,2,1,0}}} : Result<S.Error,List<&2,S.Token>>}

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

law comma_scrutinees:
  for +at: S.At
  {P.run(4n,P.MatchTail{S.Token{"match",at},S.Variable{S.Token{"a",at}},0},
      [S.Token{",",at},S.Token{"b",at},S.Token{":",at},S.Token{"<eof>",at}])
    == Done{P.Parsed{S.Match{S.Token{"match",at},
      S.Sequence{[S.Variable{S.Token{"a",at}},S.Variable{S.Token{"b",at}}]},Nil{}},
      [S.Token{"<eof>",at}]}} : Result<S.Error,P.Parsed>}

# A header runs to its colon; its line breaks separate nothing, and the
# tokens after the colon keep their layout.
law header_joins_lines:
  for +at: S.At
  for +rest: List<&2,S.Token>
  {P.header(Con{S.Token{"\n",at},Con{S.Token{"a",at},Con{S.Token{"\n",at},Con{S.Token{":",at},rest}}}})
    == Con{S.Token{"a",at},Con{S.Token{":",at},rest}} : List<&2,S.Token>}

# Touching compares offsets: `On{`, `On {` and `On` / `{` on the next line.
law touches_witness:
  {[S.touches(S.Token{"On",S.At{9,11,1,9}},S.Token{"{",S.At{11,12,1,11}}),
    S.touches(S.Token{"On",S.At{9,11,1,9}},S.Token{"{",S.At{12,13,1,12}}),
    S.touches(S.Token{"On",S.At{9,11,1,9}},S.Token{"{",S.At{18,19,2,6}})]
    == [True{},False{},False{}] : List<&2,Bool>}

# A brace opens fields only where it touches the name, in patterns and bodies
# alike; a space, comment or line break between them detaches it.
law touching_brace:
  for pattern: Bool
  for +x: S.At
  for +y: S.At
  for +z: S.At
  for +rest: List<&2,S.Token>
  for touch: {S.touches(S.Token{"On",x},S.Token{"{",y}) == True{} : Bool}
  {P.run(2n,P.Term{pattern},Con{S.Token{"On",x},Con{S.Token{"{",y},Con{S.Token{"}",z},rest}}})
    == Done{P.Parsed{S.Constructor{S.Token{"On",x},Nil{}},rest}} : Result<S.Error,P.Parsed>}

law detached_brace:
  for pattern: Bool
  for +x: S.At
  for +y: S.At
  for +rest: List<&2,S.Token>
  for gap: {S.touches(S.Token{"On",x},S.Token{"{",y}) == False{} : Bool}
  {P.run(1n,P.Term{pattern},Con{S.Token{"On",x},Con{S.Token{"{",y},rest}})
    == Fail{S.Invalid{"parse","detached-brace",y}} : Result<S.Error,P.Parsed>}

# The joined case header `On` / `{}:` keeps its offsets, so its brace stays detached.
law joined_brace_witness:
  {P.run(1n,P.Term{True{}},P.header([S.Token{"On",S.At{9,11,1,9}},S.Token{"\n",S.At{11,12,1,11}},
      S.Token{"{",S.At{18,19,2,6}},S.Token{"}",S.At{19,20,2,7}},S.Token{":",S.At{20,21,2,8}}]))
    == Fail{S.Invalid{"parse","detached-brace",S.At{18,19,2,6}}} : Result<S.Error,P.Parsed>}

def indented(text: String) -> S.Token: S.Token{text,S.At{0,0,1,2}}

law line_broken_scrutinees_witness:
  {P.run(8n,P.BodyAt{2},[indented("match"),indented("\n"),indented("a"),indented("\n"),indented("b"),indented(":"),indented("<eof>")])
    == Done{P.Parsed{S.Match{indented("match"),S.Sequence{[S.Variable{indented("a")},S.Variable{indented("b")}]},Nil{}},
      [indented("<eof>")]}} : Result<S.Error,P.Parsed>}

# A pattern or live let binds one word; a dotted name refers to a declaration.
law dotted_pattern_binder:
  for +at: S.At
  for +rest: List<&2,S.Token>
  {P.run(1n,P.Term{True{}},Con{S.Token{"a.b",at},Con{S.Token{":",at},rest}})
    == Fail{S.Invalid{"parse","pattern-binder",at}} : Result<S.Error,P.Parsed>}

law dotted_let_binder:
  for +at: S.At
  for +rest: List<&2,S.Token>
  {P.run(1n,P.BindingStart{1,2},Con{S.Token{"a.b",at},Con{S.Token{"=",at},rest}})
    == Fail{S.Invalid{"parse","binding-name",at}} : Result<S.Error,P.Parsed>}

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

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

# The seed reads `+` and `-` as a marker only where a name follows directly, and
# a `+` after a term opens another column only then.
law marks_witness:
  {[S.marks(S.Token{"+",S.At{9,10,1,9}},S.Token{"b",S.At{10,11,1,10}}),
    S.marks(S.Token{"+",S.At{9,10,1,9}},S.Token{"b",S.At{11,12,1,11}}),
    S.marks(S.Token{"+",S.At{9,10,1,9}},S.Token{"\n",S.At{10,11,1,10}})]
    == [True{},False{},False{}] : List<&2,Bool>}

law detached_plus:
  for +keyword: S.Token
  for +pattern: S.Node
  for +parent: U32
  for +column: U32
  for +rest: List<&2,S.Token>
  {P.run(1n,P.RowTail{keyword,pattern,parent,column},Con{S.Token{"+",S.At{9,10,1,9}},Con{S.Token{"b",S.At{11,12,1,11}},rest}})
    == Fail{S.Invalid{"parse","expected-:",S.At{9,10,1,9}}} : Result<S.Error,P.Parsed>}

def indented(text: String) -> S.Token: S.Token{text,S.At{0,0,1,2}}

law line_broken_scrutinees_witness:
  {P.run(8n,P.BodyAt{2,True{}},[indented("match"),indented("\n"),indented("a"),indented("\n"),indented("b"),indented(":"),indented("<eof>")])
    == Done{P.Parsed{S.Match{indented("match"),S.Sequence{[S.Variable{indented("a")},S.Variable{indented("b")}]},Nil{}},
      [indented("<eof>")]}} : Result<S.Error,P.Parsed>}

# After a let the seed reads a spaced `+` as an operator on its value; first in
# a body it follows no value and may be spaced.
law detached_marker:
  for +rest: List<&2,S.Token>
  {P.run(1n,P.BodyAt{2,False{}},Con{S.Token{"+",S.At{20,21,3,2}},Con{S.Token{"u",S.At{22,23,3,4}},rest}})
    == Fail{S.Invalid{"parse","detached-marker",S.At{20,21,3,2}}} : Result<S.Error,P.Parsed>}

law first_marker:
  for +rest: List<&2,S.Token>
  {P.run(1n,P.BodyAt{2,True{}},Con{S.Token{"+",S.At{20,21,3,2}},Con{S.Token{"u",S.At{22,23,3,4}},rest}})
    == Fail{S.Exhausted{"parse",S.At{22,23,3,4}}} : Result<S.Error,P.Parsed>}

# A dotted binder rebinds a name only where that name is in scope, which the
# parser cannot see: in a pattern, a `+` promotion, a let and a typed let it is
# unsupported, while a token that is no name at all stays invalid.
law dotted_pattern_binder:
  for +at: S.At
  for +rest: List<&2,S.Token>
  {P.run(1n,P.Term{True{}},Con{S.Token{"a.b",at},Con{S.Token{":",at},rest}})
    == Fail{S.Unsupported{"parse","dotted-binder",at}} : Result<S.Error,P.Parsed>}

law dotted_promotion_binder:
  for +at: S.At
  for +rest: List<&2,S.Token>
  {P.run(1n,P.Term{True{}},Con{S.Token{"+",at},Con{S.Token{"a.b",at},rest}})
    == Fail{S.Unsupported{"parse","dotted-binder",at}} : Result<S.Error,P.Parsed>}

law dotted_let_binder:
  for +at: S.At
  for +rest: List<&2,S.Token>
  {P.run(1n,P.BindingStart{1,2},Con{S.Token{"a.b",at},Con{S.Token{"=",at},rest}})
    == Fail{S.Unsupported{"parse","dotted-binder",at}} : Result<S.Error,P.Parsed>}

law dotted_typed_let_binder:
  for +at: S.At
  for +rest: List<&2,S.Token>
  {P.run(1n,P.BindingStart{1,2},Con{S.Token{"a.b",at},Con{S.Token{":",at},rest}})
    == Fail{S.Unsupported{"parse","dotted-binder",at}} : Result<S.Error,P.Parsed>}

law unnamed_binder_is_invalid:
  for +at: S.At
  for +rest: List<&2,S.Token>
  {P.run(1n,P.BindingStart{1,2},Con{S.Token{"(",at},Con{S.Token{"=",at},rest}})
    == Fail{S.Invalid{"parse","binding-name",at}} : Result<S.Error,P.Parsed>}

# The seed reads a line break inside call or constructor arguments as
# whitespace, and a second arm on the line of an arm's body as the next arm; a
# term here ends at a line break. Both are unsupported, while a line break
# after a complete body still ends it.
law line_break_in_arguments:
  for +at: S.At
  for +rest: List<&2,S.Token>
  {P.run(1n,P.Arguments{"}",False{}},Con{S.Token{"\n",at},rest})
    == Fail{S.Unsupported{"parse","line-break",at}} : Result<S.Error,P.Parsed>}

law line_break_after_element:
  for +at: S.At
  for +head: S.Node
  for +rest: List<&2,S.Token>
  {P.run(1n,P.ListTail{")",head,False{},False{}},Con{S.Token{"\n",at},rest})
    == Fail{S.Unsupported{"parse","line-break",at}} : Result<S.Error,P.Parsed>}

law same_line_arm:
  for +at: S.At
  for +value: S.Node
  for +rest: List<&2,S.Token>
  {P.body_end(value,Con{S.Token{"case",at},rest})
    == Fail{S.Unsupported{"parse","same-line-arm",at}} : Result<S.Error,P.Parsed>}

law body_ends_at_line_break:
  for +at: S.At
  for +value: S.Node
  for +rest: List<&2,S.Token>
  {P.body_end(value,Con{S.Token{"\n",at},rest})
    == Done{P.Parsed{value,Con{S.Token{"\n",at},rest}}} : Result<S.Error,P.Parsed>}

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
    Con{S.Token{"-",S.At{15,16,1,15}},Con{S.Token{">",S.At{16,17,1,16}},Con{S.Token{"List",at},Con{S.Token{"<",at},rest}}}})
    == Fail{S.Unsupported{"parse","type-application",at}} : Result<S.Error,P.Parsed>}

# A return arrow is one lexeme: split into `-` and `>` the seed rejects it.
law split_arrow:
  for +at: S.At
  for +rest: List<&2,S.Token>
  {P.run(1n,P.FunctionTail{S.Token{"main",at},S.Sequence{Nil{}}},
    Con{S.Token{"-",S.At{15,16,1,15}},Con{S.Token{">",S.At{17,18,1,17}},Con{S.Token{"F",at},Con{S.Token{":",at},rest}}}})
    == Fail{S.Invalid{"parse","function-result",S.At{15,16,1,15}}} : Result<S.Error,P.Parsed>}

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

# A numeral opens a literal pattern and a line's first token a statement only at a
# name, `match` or a marker; Knot answers Unsupported where the seed accepts more.
law numeral_witness:
  {[S.numeral("0n"),S.numeral("10n"),S.numeral("n0"),S.numeral("+"),S.numeral("")] ==
    [True{},True{},False{},False{},False{}] : List<&2,Bool>}

law statement_witness:
  {[S.statement(S.Token{"v",S.At{9,10,1,9}}),S.statement(S.Token{"match",S.At{9,10,1,9}}),S.statement(S.Token{"+",S.At{9,10,1,9}}),
    S.statement(S.Token{"case",S.At{9,10,1,9}}),S.statement(S.Token{"def",S.At{9,10,1,9}}),S.statement(S.Token{")",S.At{9,10,1,9}})] ==
    [True{},True{},True{},False{},False{},False{}] : List<&2,Bool>}

law numeral_column_is_unsupported:
  for +at: S.At
  for +rest: List<&2,S.Token>
  {P.run(1n,P.Term{True{}},Con{S.Token{"0n",at},Con{S.Token{":",at},rest}}) == Fail{S.Unsupported{"parse","term-form",at}} : Result<S.Error,P.Parsed>}

law same_line_statement:
  for +at: S.At
  for +rest: List<&2,S.Token>
  {P.line_end(Con{S.Token{"v",at},rest}) == Fail{S.Unsupported{"parse","same-line-statement",at}} : Result<S.Error,List<&2,S.Token>>}

law let_ends_at_line_break:
  for +at: S.At
  for +rest: List<&2,S.Token>
  {P.line_end(Con{S.Token{"\n",at},rest}) == Done{rest} : Result<S.Error,List<&2,S.Token>>}

law split_before_colon_witness:
  {[P.split([S.Token{"\n",S.At{9,10,1,9}},S.Token{":",S.At{20,21,2,8}}]),P.split([S.Token{"\n",S.At{9,10,1,9}},S.Token{"=",S.At{20,21,2,8}}]),
    P.split([S.Token{"\n",S.At{9,10,1,9}},S.Token{"v",S.At{20,21,2,8}}]),P.split([S.Token{":",S.At{9,10,1,9}}])] ==
    [True{},True{},False{},False{}] : List<&2,Bool>}

# A call's parenthesis opens on its callee's line. On a later line, in a header that joins its
# lines, it opens the next column (Knot has no term for it), as the seed reads it.
law same_line_witness:
  {[S.same_line(S.Token{"h",S.At{9,10,1,9}},S.Token{"(",S.At{11,12,1,11}}),S.same_line(S.Token{"h",S.At{9,10,1,9}},S.Token{"(",S.At{20,21,2,2}})] ==
    [True{},False{}] : List<&2,Bool>}

law paren_on_a_later_line_is_no_call:
  {P.run(1n,P.Term{False{}},[S.Token{"h",S.At{9,10,1,9}},S.Token{"(",S.At{20,21,2,2}}]) ==
    Done{P.Parsed{S.Variable{S.Token{"h",S.At{9,10,1,9}}},[S.Token{"(",S.At{20,21,2,2}}]}} : Result<S.Error,P.Parsed>}

law parenthesis_opens_a_column:
  {[P.opens([S.Token{"(",S.At{9,10,1,9}}]),P.opens([S.Token{":",S.At{9,10,1,9}}])] == [True{},False{}] : List<&2,Bool>}

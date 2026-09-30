import Base
import ./syntax.bend as S
import ./parse.bend as P

# Layout at a header delimiter preserves its parse, including its refusal.
law datatype_colon_layout:
  for +n: Nat
  for +name: S.Token
  for +at: S.At
  for +rest: List<&2,S.Token>
  {P.run(1n+n,P.TypeKind{name},Con{S.Token{"Data",at},Con{S.Token{"\n",at},rest}})
    == P.run(1n+n,P.TypeKind{name},Con{S.Token{"Data",at},rest}) : Result<S.Error,P.Parsed>}

law generic_colon_layout:
  for +n: Nat
  for +name: S.Token
  for +params: S.Node
  for +at: S.At
  for +body: List<&2,S.Token>
  {P.run(3n+n,P.GenericKind{name,params},
      Con{S.Token{"Type",at},Con{S.Token{"\n",at},Con{S.Token{":",at},body}}})
    == P.run(3n+n,P.GenericKind{name,params},
      Con{S.Token{"Type",at},Con{S.Token{":",at},body}}) : Result<S.Error,P.Parsed>}

law result_arrow_layout:
  for +n: Nat
  for +name: S.Token
  for +at: S.At
  for +rest: List<&2,S.Token>
  {P.run(3n+n,P.Header{S.Token{"def",at},name},
      Con{S.Token{"(",at},Con{S.Token{")",at},Con{S.Token{"\n",at},rest}}})
    == P.run(3n+n,P.Header{S.Token{"def",at},name},
      Con{S.Token{"(",at},Con{S.Token{")",at},rest}}) : Result<S.Error,P.Parsed>}

law parameters_layout:
  for +n: Nat
  for +close: String
  for +at: S.At
  for +rest: List<&2,S.Token>
  {P.run(1n+n,P.Parameters{close},Con{S.Token{"\n",at},rest})
    == P.run(1n+n,P.Parameters{close},rest) : Result<S.Error,P.Parsed>}

law parameter_tail_layout:
  for +n: Nat
  for +close: String
  for +head: S.Node
  for +at: S.At
  for +rest: List<&2,S.Token>
  {P.run(1n+n,P.ListTail{close,head,True{},False{}},Con{S.Token{"\n",at},rest})
    == P.run(1n+n,P.ListTail{close,head,True{},False{}},rest) : Result<S.Error,P.Parsed>}

# An ordinary binder ends the leading template region across layout too.
law nonleading_template_layout:
  for +n: Nat
  for +head: S.Node
  for +at: S.At
  for +mark: S.At
  for +rest: List<&2,S.Token>
  {P.run(1n+n,P.ListTail{")",head,True{},False{}},
      Con{S.Token{",",at},Con{S.Token{"\n",at},Con{S.Token{"~",mark},rest}}})
    == Fail{S.Invalid{"parse","parameter",mark}} : Result<S.Error,P.Parsed>}

law declaration_name_layout:
  for +n: Nat
  for +at: S.At
  for +name: S.Token
  for +rest: List<&2,S.Token>
  {P.run(1n+n,P.Declaration{},Con{S.Token{"def",at},Con{S.Token{"\n",at},Con{name,rest}}})
    == P.run(1n+n,P.Declaration{},Con{S.Token{"def",at},Con{name,rest}}) : Result<S.Error,P.Parsed>}

# A named type's header closer retains its source-adjacency requirement.
law named_header_close_gap:
  for +name: S.Token
  for +q: U32
  for +rest: List<&2,S.Token>
  {P.parameter_end(name,q,S.Token{"T",S.At{0,1,1,0}},
      Con{S.Token{"\n",S.At{1,2,1,1}},Con{S.Token{">",S.At{2,3,2,0}},rest}})
    == P.unsupported(Con{S.Token{">",S.At{2,3,2,0}},rest},"spacing") : Result<S.Error,P.Parsed>}

import Base
import ./syntax.bend as S
import ./literal.bend as Q

type Parsed is Data:
  Parsed{value: S.Node, rest: List<&2,S.Token>}

type Mode is Data:
  Book{}
  Declaration{}
  Constructors{parent: U32, column: U32}
  Parameters{close: String}
  Arguments{close: String, pattern: Bool}
  Term{pattern: Bool}
  LiteralTail{node: S.Node, pattern: Bool}
  Body{parent: U32}
  StartBody{parent: U32}
  BodyAt{parent: U32, first: Bool}
  Arms{parent: U32, column: U32}
  Header{keyword: S.Token, name: S.Token}
  TypeKind{name: S.Token}
  FunctionTail{token: S.Token, parameters: S.Node}
  MatchTail{token: S.Token, value: S.Node, column: U32}
  RowTail{token: S.Token, pattern: S.Node, parent: U32, column: U32}
  BindingStart{quantity: U32, parent: U32}
  AnnotatedBinding{token: S.Token, quantity: U32, parent: U32}
  BindingTail{token: S.Token, quantity: U32, annotation: Maybe<&2,S.Token>, value: S.Node, parent: U32}
  ListTail{close: String, head: S.Node, parameters: Bool, pattern: Bool}

def invalid(+ts: List<&2,S.Token>, code: String) -> Result<S.Error,Parsed>:
  Fail{S.Invalid{"parse",code,S.here(ts)}}

def unsupported(+ts: List<&2,S.Token>, code: String) -> Result<S.Error,Parsed>:
  Fail{S.Unsupported{"parse",code,S.here(ts)}}

def starts(ts: List<&2,S.Token>, word: String) -> Bool:
  match ts:
    case Nil{}: False{}
    case Con{head,tail}: S.matches(head,word)

# An offset's `+` touches its literal: `1n+p`, never `1n +p`.
def touches(left: S.At, right: S.At) -> Bool:
  match left right:
    case S.At{start,end,line,column} S.At{next,stop,row,col}: U32.is_eq(end,next)

# `kn+t` is k successors around t, so `0n+t` is t itself, as the seed reads it.
def offset(+token: S.Token, +count: U32, +tail: S.Node) -> S.Node:
  S.choose(S.Node,U32.is_eq(count,0),u => tail,u => S.Offset{token,count,tail})

# A name or a literal starts the next column, argument or field: whitespace separates them, as in the seed.
def scrutinee(ts: List<&2,S.Token>) -> Bool:
  match ts:
    case Nil{}: False{}
    case Con{+head,tail}: Bool.or(S.identifier(head),Q.starts(S.text(head)))

# After a term, `a +b` opens another column and `a + b` is an operator.
def promotes(ts: List<&2,S.Token>) -> Bool:
  match ts:
    case Con{+plus,Con{next,rest}}: Bool.and(S.matches(plus,"+"),S.marks(plus,next))
    case _: False{}

# A line break, then a name: whitespace to the seed.
def broken(+ts: List<&2,S.Token>) -> Bool:
  Bool.and(starts(ts,"\n"),scrutinee(S.skip_lines(ts)))

# The seed accepts a repeated promotion, `++y`, and a name after a line break,
# which the parser cannot tell: each is unsupported; other unbindable names are invalid.
def binder_failure(+ts: List<&2,S.Token>, +name: S.Token, code: String, promoted: Bool) -> Result<S.Error,Parsed>:
  S.choose(Result<S.Error,Parsed>,Bool.and(promoted,S.matches(name,"+")),u => unsupported(ts,"repeated-promotion"),u =>
  S.choose(Result<S.Error,Parsed>,broken(ts),u => unsupported(ts,"line-break"),u =>
    invalid(ts,code)))

def then(result: Result<S.Error,Parsed>,
  next: S.Node -> List<&2,S.Token> -> Result<S.Error,Parsed>) -> Result<S.Error,Parsed>:
  match result:
    case Fail{e}: Fail{e}
    case Done{Parsed{value,rest}}: next(value,rest)

def prepend(head: S.Node, tail: S.Node, rest: List<&2,S.Token>) -> Result<S.Error,Parsed>:
  match tail:
    case S.Sequence{items}: Done{Parsed{S.Sequence{Con{head,items}},rest}}
    case _: Fail{S.Internal{"parse","expected-sequence"}}

def wrap_call(+token: S.Token, constructor: Bool, value: S.Node,
  +rest: List<&2,S.Token>) -> Result<S.Error,Parsed>:
  match value:
    case S.Sequence{+items}:
      S.choose(Result<S.Error,Parsed>,constructor,u =>
        Done{Parsed{S.Constructor{token,items},rest}},u =>
        Done{Parsed{S.Call{token,items},rest}})
    case _: Fail{S.Internal{"parse","expected-arguments"}}

def wrap_type(token: S.Token, reusable: Bool, value: S.Node,
  rest: List<&2,S.Token>) -> Result<S.Error,Parsed>:
  match value:
    case S.Sequence{items}: Done{Parsed{S.Datatype{token,reusable,items},rest}}
    case _: Fail{S.Internal{"parse","expected-constructors"}}

def parameter_named(params: List<&2,S.Node>, +name: String) -> Bool:
  match params:
    case Nil{}: False{}
    case Con{S.Parameter{token,q,typ},tail}: Bool.or(S.matches(token,name),parameter_named(tail,name))
    case Con{other,tail}: parameter_named(tail,name)

def constructor_named(params: List<&2,S.Node>, +name: String) -> Bool:
  match params:
    case Nil{}: False{}
    case Con{S.Constructor{token,args},tail}: Bool.or(S.matches(token,name),constructor_named(tail,name))
    case Con{other,tail}: constructor_named(tail,name)

# A binder is judged against the names in scope, `params`: parameters, the lets above it, and
# constructors once registered. The seed reads a dotted name as a global unless the scope binds that
# exact name, so only a bound name may be dotted where a pattern or a live let binds; an erased
# let's name is a name, however it is spelled, and binds it below; and a registered constructor
# is no binder at all.
def binder(+code: String, +name: S.Token, +erased: Bool, +params: List<&2,S.Node>) -> Result<S.Error,Unit>:
  S.choose(Result<S.Error,Unit>,Bool.and(Bool.and(String.contains(S.text(name),"."),Bool.not(parameter_named(params,S.text(name)))),Bool.not(erased)),u =>
    Fail{S.Invalid{"parse",code,S.at(name)}},u =>
  S.choose(Result<S.Error,Unit>,constructor_named(params,S.text(name)),u =>
    Fail{S.Invalid{"check","constructor-pattern-binder",S.at(name)}},u => Done{Unit{}}))

# The seed reads an annotation that spells a binder in scope as that variable, not as the type.
def shaded(annotation: Maybe<&2,S.Token>, params: List<&2,S.Node>) -> Result<S.Error,Unit>:
  match annotation:
    case None{}: Done{Unit{}}
    case Some{+typ}:
      S.choose(Result<S.Error,Unit>,parameter_named(params,S.text(typ)),u =>
        Fail{S.Unsupported{"parse","annotation-shadow",S.at(typ)}},u => Done{Unit{}})

# The variables a pattern binds are in scope in its arm's body.
def bound(fuel: Nat, node: S.Node) -> List<&2,S.Node>:
  match fuel node:
    case 0n _: Nil{}
    case 1n+n S.Variable{+token}: [S.Parameter{token,1,token}]
    case 1n+n S.Promotion{+token}: [S.Parameter{token,2,token}]
    case 1n+n S.Offset{token,count,tail}: bound(n,tail)
    case 1n+n S.Constructor{token,args}: bound(n,S.Sequence{args})
    case 1n+n S.Sequence{Nil{}}: Nil{}
    case 1n+ +n S.Sequence{Con{head,tail}}: List.append(&2,S.Node,bound(n,head),bound(n,S.Sequence{tail}))
    case 1n+n _: Nil{}

# The binders of a body in source order: a let name, or a variable at a pattern position.
def binders(fuel: Nat, node: S.Node, +pattern: Bool, +params: List<&2,S.Node>) -> Result<S.Error,Unit>:
  match fuel node:
    case 0n _: Fail{S.Exhausted{"parse",S.At{0,0,0,0}}}
    case 1n+n S.Promotion{token}: binder("pattern-binder",token,False{},params)
    case 1n+ +n S.Variable{+token}:
      S.choose(Result<S.Error,Unit>,pattern,u => binder("pattern-binder",token,False{},params),u => Done{Unit{}})
    case 1n+n S.Offset{token,count,tail}: binders(n,tail,pattern,params)
    case 1n+n S.Constructor{token,args}: binders(n,S.Sequence{args},pattern,params)
    case 1n+ +n S.Binding{+token,+q,ann,value,body}:
      S.bind(Unit,Unit,shaded(ann,params),u =>
        S.bind(Unit,Unit,binder("binding-name",token,U32.is_eq(q,0),params),u =>
          binders(n,body,False{},Con{S.Parameter{token,q,token},params})))
    case 1n+n S.Match{token,value,arms}: binders(n,S.Sequence{arms},False{},params)
    case 1n+ +n S.Arm{token,+head,body}:
      S.bind(Unit,Unit,binders(n,head,True{},params),u => binders(n,body,False{},List.append(&2,S.Node,bound(n,head),params)))
    case 1n+n S.Sequence{Nil{}}: Done{Unit{}}
    case 1n+ +n S.Sequence{Con{head,tail}}:
      S.bind(Unit,Unit,binders(n,head,pattern,params),u => binders(n,S.Sequence{tail},pattern,params))
    case 1n+n _: Done{Unit{}}

# The seed registers a file's constructors in source order, so each body meets those declared
# before it. A single file is judged here; qualification judges a bundle book.
def registered(decls: List<&2,S.Node>, +seen: List<&2,S.Node>) -> Result<S.Error,Unit>:
  match decls:
    case Nil{}: Done{Unit{}}
    case Con{S.Datatype{token,data,ctors},rest}: registered(rest,List.append(&2,S.Node,ctors,seen))
    case Con{S.Function{token,params,result,body},rest}:
      S.bind(Unit,Unit,binders(65536n,body,False{},List.append(&2,S.Node,params,seen)),u => registered(rest,seen))
    case Con{other,rest}: registered(rest,seen)

# A parameter's name shadows the type of that name in the annotations after it, its own included.
def reads(+name: S.Token, params: List<&2,S.Node>, +result: S.Token) -> Bool:
  match params:
    case Nil{}: String.eq(S.text(name),S.text(result))
    case Con{S.Parameter{token,q,+typ},tail}: Bool.or(String.eq(S.text(name),S.text(typ)),reads(name,tail,result))
    case Con{other,tail}: reads(name,tail,result)

def shadows(params: List<&2,S.Node>, +result: S.Token) -> Result<S.Error,Unit>:
  match params:
    case Nil{}: Done{Unit{}}
    case Con{S.Parameter{+name,q,typ},+tail}:
      S.choose(Result<S.Error,Unit>,reads(name,Con{S.Parameter{name,q,typ},tail},result),u =>
        Fail{S.Unsupported{"parse","parameter-shadow",S.at(name)}},u => shadows(tail,result))
    case Con{other,tail}: shadows(tail,result)

def wrap_function(token: S.Token, params: S.Node, +result: S.Token,
  +body: S.Node, rest: List<&2,S.Token>) -> Result<S.Error,Parsed>:
  match params:
    case S.Sequence{+items}:
      S.bind(Unit,Parsed,shadows(items,result),u =>
        S.bind(Unit,Parsed,binders(65536n,body,False{},items),u => Done{Parsed{S.Function{token,items,result,body},rest}}))
    case _: Fail{S.Internal{"parse","expected-parameters"}}

# A singleton keeps the original parser observation; further columns append.
def columns(head: S.Node, +tail: S.Node) -> S.Node:
  match head:
    case S.Sequence{items}: S.Sequence{List.append(&2,S.Node,items,[tail])}
    case _: S.Sequence{[head,tail]}

def wrap_match(token: S.Token, value: S.Node, arms: S.Node,
  rest: List<&2,S.Token>) -> Result<S.Error,Parsed>:
  match arms:
    case S.Sequence{items}: Done{Parsed{S.Match{token,value,items},rest}}
    case _: Fail{S.Internal{"parse","expected-arms"}}

def expect(+ts: List<&2,S.Token>, +word: String) -> Result<S.Error,List<&2,S.Token>>:
  match ts:
    case Nil{}: Fail{S.Invalid{"parse","unexpected-end",S.here(ts)}}
    case Con{+h,+t}:
      S.choose(Result<S.Error,List<&2,S.Token>>,S.matches(h,word),u => Done{t},u =>
        Fail{S.Invalid{"parse",String.append("expected-",word),S.at(h)}})

# A line break before a let's `=` is whitespace to the seed, which the parser cannot tell apart.
def assign(+ts: List<&2,S.Token>) -> Result<S.Error,List<&2,S.Token>>:
  S.choose(Result<S.Error,List<&2,S.Token>>,Bool.and(starts(ts,"\n"),starts(S.skip_lines(ts),"=")),u =>
    Fail{S.Unsupported{"parse","line-break",S.here(ts)}},u => expect(ts,"="))

def parameter_end(+name: S.Token, +quantity: U32, +typ: S.Token, +rest: List<&2,S.Token>) -> Result<S.Error,Parsed>:
  match rest:
    case Con{h,t}:
      S.choose(Result<S.Error,Parsed>,Bool.or(S.matches(h,"<"),Bool.or(S.matches(h,"-"),S.matches(h,"("))),u =>
        unsupported(rest,"parameter-type"),u => Done{Parsed{S.Parameter{name,quantity,typ},rest}})
    case Nil{}: invalid(rest,"parameter")

def parameter_parts(+quantity: U32, +ts: List<&2,S.Token>) -> Result<S.Error,Parsed>:
  match ts:
    case Con{+name,Con{+colon,Con{+typ,+rest}}}:
      S.choose(Result<S.Error,Parsed>,Bool.and(S.identifier(name),Bool.or(S.matches(colon,","),S.matches(colon,"}"))),u =>
        unsupported(ts,"bare-quantity-field"),u =>
      S.choose(Result<S.Error,Parsed>,Bool.and(S.identifier(name),S.matches(colon,":")),u =>
        S.choose(Result<S.Error,Parsed>,S.identifier(typ),u => parameter_end(name,quantity,typ,rest),u =>
          unsupported(Con{typ,rest},"parameter-type")),u => invalid(ts,"parameter")))
    case _: invalid(ts,"parameter")

def parameter(+ts: List<&2,S.Token>) -> Result<S.Error,Parsed>:
  match ts:
    case Con{+h,+t}:
      S.choose(Result<S.Error,Parsed>,S.matches(h,"-"),u => parameter_parts(0,t),u =>
      S.choose(Result<S.Error,Parsed>,S.matches(h,"+"),u => parameter_parts(2,t),u =>
        parameter_parts(1,ts)))
    case _: invalid(ts,"parameter")

def template_parameter(+ts: List<&2,S.Token>) -> Result<S.Error,Parsed>:
  match ts:
    case Con{marker,Con{+name,Con{+colon,tail}}}:
      S.choose(Result<S.Error,Parsed>,Bool.and(S.identifier(name),S.matches(colon,":")),u =>
        unsupported(ts,"template-binder"),u => invalid(ts,"parameter"))
    case _: invalid(ts,"parameter")

# The seed reads a second arm on the line of an arm's body as the next arm.
def body_end(value: S.Node, +ts: List<&2,S.Token>) -> Result<S.Error,Parsed>:
  match ts:
    case Con{h,t}:
      S.choose(Result<S.Error,Parsed>,Bool.or(S.matches(h,"\n"),S.matches(h,"<eof>")),u =>
        Done{Parsed{value,ts}},u =>
      S.choose(Result<S.Error,Parsed>,S.matches(h,"case"),u => unsupported(ts,"same-line-arm"),u =>
      S.choose(Result<S.Error,Parsed>,S.matches(h,"+"),u => unsupported(ts,"operator"),u =>
        invalid(ts,"end-of-body"))))
    case _: invalid(ts,"unexpected-end")

# A let's value ends at its line; a `+` after it is an operator, which Knot does not check.
def line_end(+ts: List<&2,S.Token>) -> Result<S.Error,List<&2,S.Token>>:
  match ts:
    case Nil{}: Fail{S.Invalid{"parse","unexpected-end",S.here(ts)}}
    case Con{+h,+t}:
      S.choose(Result<S.Error,List<&2,S.Token>>,S.matches(h,"\n"),u => Done{t},u =>
        S.choose(Result<S.Error,List<&2,S.Token>>,S.matches(h,"+"),u =>
          Fail{S.Unsupported{"parse","operator",S.at(h)}},u => Fail{S.Invalid{"parse","expected-newline",S.at(h)}}))

def reply(+value: S.Node, +ts: List<&2,S.Token>) -> Result<S.Error,Parsed>:
  match value:
    case S.Constructor{token,items}:
      match ts:
        case Con{+head,+tail}:
          S.choose(Result<S.Error,Parsed>,S.matches(head,"="),u =>
            S.choose(Result<S.Error,Parsed>,Bool.or(starts(tail,"="),starts(tail,">")),u =>
              body_end(value,ts),u => unsupported(ts,"destructuring-binding")),u => body_end(value,ts))
        case Nil{}: body_end(value,ts)
    case _: body_end(value,ts)

def operator_tail(ts: List<&2,S.Token>) -> Bool:
  match ts:
    case Nil{}: False{}
    case Con{+h,+t}:
      S.choose(Bool,S.matches(h,"\n"),u => False{},u =>
        Bool.or(Bool.or(S.matches(h,"+"),Bool.or(S.matches(h,"*"),Bool.or(S.matches(h,"<"),S.matches(h,"-")))),operator_tail(t)))

def term_failure(+ts: List<&2,S.Token>) -> Result<S.Error,Parsed>:
  match ts:
    case Con{+h,t}:
      S.choose(Result<S.Error,Parsed>,Bool.or(S.matches(h,")"),Bool.or(S.matches(h,"}"),
        Bool.or(S.matches(h,":"),Bool.or(S.matches(h,","),Bool.or(S.matches(h,"\n"),S.matches(h,"<eof>")))))),u =>
          invalid(ts,"expected-term"),u => S.choose(Result<S.Error,Parsed>,Bool.and(S.matches(h,"("),operator_tail(ts)),u => unsupported(ts,"operator"),u => unsupported(ts,"term-form")))
    case _: invalid(ts,"unexpected-end")

# A match or case header runs to its colon; its line breaks separate no
# columns, as in the seed. Joined tokens keep their offsets, so a brace on the
# next line never touches a name. Tokens after the colon keep their layout.
def header(ts: List<&2,S.Token>) -> List<&2,S.Token>:
  match ts:
    case Nil{}: Nil{}
    case Con{+h,+t}:
      S.choose(List<&2,S.Token>,S.matches(h,":"),u => Con{h,t},u =>
        S.choose(List<&2,S.Token>,S.matches(h,"\n"),u => header(t),u => Con{h,header(t)}))

# One recursive dispatcher makes the parser's depth budget explicit and avoids
# unchecked mutual recursion. Every recursive invocation decreases fuel.
def run(fuel: Nat, mode: Mode, +tokens: List<&2,S.Token>) -> Result<S.Error,Parsed>:
  match fuel mode:
    case 0n _: Fail{S.Exhausted{"parse",S.here(tokens)}}
    case 1n+ +n Book{}:
      run(n,Declaration{},S.skip_lines(tokens))
    case 1n+ +n Declaration{}:
      match tokens:
        case Con{+head,Con{+name,+tail}}:
          S.choose(Result<S.Error,Parsed>,S.matches(head,"<eof>"),u =>
            Done{Parsed{S.Sequence{Nil{}},tokens}},u =>
          S.choose(Result<S.Error,Parsed>,U32.is_eq(S.column(head),0),u =>
            then(run(n,Header{head,name},tail),value => rest =>
              then(run(n,Book{},rest),more => end => prepend(value,more,end))),u =>
            invalid(tokens,"top-level-indentation")))
        case Con{+head,Nil{}}:
          S.choose(Result<S.Error,Parsed>,S.matches(head,"<eof>"),u =>
            Done{Parsed{S.Sequence{Nil{}},tokens}},u => invalid(tokens,"unexpected-end"))
        case _: invalid(tokens,"unexpected-end")
    case 1n+ +n Constructors{+parent,+column}:
      # Caller has already skipped blank lines.
      match tokens:
        case Con{+name,+tail}:
          S.choose(Result<S.Error,Parsed>,Bool.or(S.matches(name,"<eof>"),U32.is_le(S.column(name),parent)),u =>
            Done{Parsed{S.Sequence{Nil{}},tokens}},u =>
          S.choose(Result<S.Error,Parsed>,Bool.and(S.identifier(name),Bool.or(U32.is_eq(column,0),U32.is_eq(S.column(name),column))),u =>
            S.bind(List<&2,S.Token>,Parsed,expect(tail,"{"),open =>
              then(run(n,Parameters{"}"},S.skip_lines(open)),fields => closed =>
                then(wrap_call(name,True{},fields,closed),value => end =>
                  then(body_end(value,end),ctor => after =>
                    then(run(n,Constructors{parent,S.column(name)},S.skip_lines(after)),more => end => prepend(ctor,more,end)))))),u =>
            unsupported(tokens,"constructor-fields-or-indentation")))
        case _: invalid(tokens,"unexpected-end")
    case 1n+ +n Parameters{+close}:
      match tokens:
        case Con{+h,+t}:
          S.choose(Result<S.Error,Parsed>,S.matches(h,close),u =>
            Done{Parsed{S.Sequence{Nil{}},t}},u =>
          S.choose(Result<S.Error,Parsed>,Bool.and(String.eq(close,")"),S.matches(h,"~")),u =>
            template_parameter(tokens),u =>
            then(parameter(tokens),p => rest => run(n,ListTail{close,p,True{},False{}},S.skip_lines(rest)))))
        case _: invalid(tokens,"unexpected-end")
    case 1n+ +n Arguments{+close,+pattern}:
      match tokens:
        case Con{+h,+t}:
          S.choose(Result<S.Error,Parsed>,S.matches(h,close),u =>
            Done{Parsed{S.Sequence{Nil{}},t}},u =>
            then(run(n,Term{pattern},tokens),arg => rest => run(n,ListTail{close,arg,False{},pattern},S.skip_lines(rest))))
        case _: invalid(tokens,"unexpected-end")
    case 1n+ +n ListTail{+close,+head,+parameters,+pattern}:
      match tokens:
        case Con{+h,+t}:
          S.choose(Result<S.Error,Parsed>,S.matches(h,close),u =>
            Done{Parsed{S.Sequence{Con{head,Nil{}}},t}},u =>
          S.choose(Result<S.Error,Parsed>,S.matches(h,","),u =>
            # A parameter tail is reachable only after an ordinary binder.
            S.choose(Result<S.Error,Parsed>,Bool.and(parameters,starts(t,"~")),u =>
              invalid(t,"parameter"),u =>
              then(run(n,Bool.pick(Mode,parameters,Parameters{close},Arguments{close,pattern}),S.skip_lines(t)),more => rest => prepend(head,more,rest))),u =>
            S.choose(Result<S.Error,Parsed>,Bool.and(Bool.not(parameters),Bool.or(scrutinee(tokens),Bool.and(pattern,promotes(tokens)))),u => unsupported(tokens,"argument-whitespace"),u =>
            S.choose(Result<S.Error,Parsed>,Bool.and(Bool.not(pattern),Bool.and(S.matches(h,"+"),Bool.not(promotes(tokens)))),u => unsupported(tokens,"operator"),u =>
              invalid(tokens,"argument-separator")))))
        case _: invalid(tokens,"unexpected-end")
    case 1n+ +n Term{+pattern}:
      match tokens:
        case Con{+name,Con{+open,+tail}}:
          S.choose(Result<S.Error,Parsed>,Bool.and(pattern,S.matches(name,"+")),u =>
            S.choose(Result<S.Error,Parsed>,S.identifier(open),u => Done{Parsed{S.Promotion{open},tail}},u => binder_failure(tokens,open,"pattern-binder",True{})),u =>
          S.choose(Result<S.Error,Parsed>,S.identifier(name),u =>
          S.choose(Result<S.Error,Parsed>,S.matches(open,"("),u =>
            then(run(n,Arguments{")",pattern},S.skip_lines(tail)),args => rest => wrap_call(name,False{},args,rest)),u =>
          S.choose(Result<S.Error,Parsed>,S.matches(open,"{"),u =>
            # Fields open at a brace touching the name, as in the seed.
            S.choose(Result<S.Error,Parsed>,S.touches(name,open),u =>
              then(run(n,Arguments{"}",pattern},S.skip_lines(tail)),args => rest => wrap_call(name,True{},args,rest)),u =>
              invalid(Con{open,tail},"detached-brace")),u =>
            Done{Parsed{S.Variable{name},Con{open,tail}}})),u =>
            S.choose(Result<S.Error,Parsed>,Q.starts(S.text(name)),u =>
              S.bind(S.Node,Parsed,Q.parse(name),node => run(n,LiteralTail{node,pattern},Con{open,tail})),u => term_failure(tokens))))
        case _: invalid(tokens,"term")
    case 1n+ +n LiteralTail{S.Literal{+token,1,+count,+text},+pattern}:
      S.choose(Result<S.Error,Parsed>,starts(tokens,"+"),u =>
        S.choose(Result<S.Error,Parsed>,touches(S.at(token),S.here(tokens)),u =>
        S.choose(Result<S.Error,Parsed>,Bool.and(pattern,U32.is_gt(count,256)),u => invalid(tokens,"nat-offset-pattern"),u =>
          S.bind(List<&2,S.Token>,Parsed,expect(tokens,"+"),tail =>
            then(run(n,Term{pattern},S.skip_lines(tail)),value => rest => Done{Parsed{offset(token,count,value),rest}}))),u =>
        unsupported(tokens,"operator")),u =>
        Done{Parsed{S.Literal{token,1,count,text},tokens}})
    case 1n+ +n LiteralTail{node,pattern}: Done{Parsed{node,tokens}}
    case 1n+ +n Body{+parent}:
      run(n,StartBody{parent},S.skip_lines(tokens))
    # The seed checks no body column: an arm body or a let's next line may stand anywhere. Knot
    # keeps a function body (parent 0) off column 0, and a match's cases right of its parent.
    case 1n+ +n StartBody{+parent}:
      match tokens:
        case Con{+h,t}:
          S.choose(Result<S.Error,Parsed>,Bool.and(Bool.or(S.matches(h,"case"),S.matches(h,"def")),U32.is_le(S.column(h),parent)),u =>
            invalid(tokens,"body-indentation"),u =>
          S.choose(Result<S.Error,Parsed>,Bool.or(U32.is_gt(parent,0),U32.is_gt(S.column(h),0)),u =>
            run(n,BodyAt{parent,True{}},tokens),u => invalid(tokens,"body-indentation")))
        case _: invalid(tokens,"body")
    case 1n+ +n BodyAt{+parent,+first}:
      match tokens:
        case Con{+h,Con{+second,+tail}}:
          S.choose(Result<S.Error,Parsed>,S.matches(h,"match"),u =>
            then(run(n,Term{False{}},header(Con{second,tail})),value => rest =>
              run(n,MatchTail{h,value,U32.max(S.column(h),parent)},rest)),u =>
          S.choose(Result<S.Error,Parsed>,Bool.or(S.matches(h,"+"),S.matches(h,"-")),u =>
            # After a let, the seed reads a spaced marker as an operator on its value.
            S.choose(Result<S.Error,Parsed>,Bool.or(first,S.marks(h,second)),u =>
              run(n,BindingStart{Bool.pick(U32,S.matches(h,"+"),2,0),parent},Con{second,tail}),u =>
              invalid(tokens,"detached-marker")),u =>
          S.choose(Result<S.Error,Parsed>,Bool.or(S.matches(second,"="),S.matches(second,":")),u =>
            run(n,BindingStart{1,parent},tokens),u =>
            then(run(n,Term{False{}},tokens),value => rest => reply(value,rest)))))
        case _: invalid(tokens,"body")
    case 1n+ +n Header{+keyword,+name}:
      S.choose(Result<S.Error,Parsed>,Bool.and(S.matches(keyword,"import"),Bool.and(starts(tokens,"/"),
        Bool.or(Bool.or(S.matches(name,"."),S.matches(name,"..")),String.starts_with(S.text(name),"0x")))),u =>
        unsupported(Con{name,tokens},"import"),u =>
      S.choose(Result<S.Error,Parsed>,S.identifier(name),u =>
      S.choose(Result<S.Error,Parsed>,S.matches(keyword,"type"),u =>
      S.choose(Result<S.Error,Parsed>,starts(tokens,"<"),u =>
        unsupported(tokens,"generic-datatype"),u =>
        S.bind(List<&2,S.Token>,Parsed,expect(tokens,"is"),kind =>
          run(n,TypeKind{name},kind))),u =>
      S.choose(Result<S.Error,Parsed>,S.matches(keyword,"def"),u =>
        S.bind(List<&2,S.Token>,Parsed,expect(tokens,"("),args =>
          then(run(n,Parameters{")"},S.skip_lines(args)),params => rest => run(n,FunctionTail{name,params},rest))),u =>
        unsupported(Con{keyword,tokens},"declaration-form"))),u => invalid(tokens,"declaration-name")))
    case 1n+ +n TypeKind{+name}:
      match tokens:
        case Con{+kind,+tail}:
          S.choose(Result<S.Error,Parsed>,Bool.or(S.matches(kind,"Type"),S.matches(kind,"Data")),u =>
            S.bind(List<&2,S.Token>,Parsed,expect(tail,":"),body =>
              then(run(n,Constructors{0,0},S.skip_lines(body)),ctors => rest => wrap_type(name,S.matches(kind,"Data"),ctors,rest))),u =>
            unsupported(tokens,"kind"))
        case _: invalid(tokens,"kind")
    case 1n+ +n FunctionTail{+name,S.Sequence{+params}}:
      match tokens:
        case Con{+dash,Con{+arrow,Con{+typ,Con{+colon,+body}}}}:
          S.choose(Result<S.Error,Parsed>,Bool.and(S.matches(dash,"-"),Bool.and(S.matches(arrow,">"),Bool.and(S.touches(dash,arrow),S.identifier(typ)))),u =>
            S.choose(Result<S.Error,Parsed>,S.matches(colon,"<"),u =>
              unsupported(Con{colon,body},"type-application"),u =>
            S.choose(Result<S.Error,Parsed>,S.matches(colon,":"),u =>
              then(run(n,Body{0},body),value => rest => wrap_function(name,S.Sequence{params},typ,value,rest)),u =>
              invalid(tokens,"function-result"))),u =>
            invalid(tokens,"function-result"))
        case _: invalid(tokens,"function-result")
    case 1n+ +n FunctionTail{token,other}:
      Fail{S.Internal{"parse","declaration-mode"}}
    case 1n+ +n MatchTail{+token,+value,+column}:
      S.choose(Result<S.Error,Parsed>,starts(tokens,","),u =>
        S.bind(List<&2,S.Token>,Parsed,expect(tokens,","),tail =>
          then(run(n,Term{False{}},tail),item => after =>
            run(n,MatchTail{token,columns(value,item),column},after))),u =>
      S.choose(Result<S.Error,Parsed>,scrutinee(tokens),u =>
        then(run(n,Term{False{}},tokens),more => rest =>
          run(n,MatchTail{token,columns(value,more),column},rest)),u =>
      S.bind(List<&2,S.Token>,Parsed,expect(tokens,":"),arms =>
        then(run(n,Arms{column,0},S.skip_lines(arms)),items => rest => wrap_match(token,value,items,rest)))))
    case 1n+ +n BindingStart{+quantity,+parent}:
      match tokens:
        case Con{+name,Con{+separator,+tail}}:
          S.choose(Result<S.Error,Parsed>,S.identifier(name),u =>
          S.choose(Result<S.Error,Parsed>,S.matches(separator,":"),u =>
            run(n,AnnotatedBinding{name,quantity,parent},tail),u =>
            S.bind(List<&2,S.Token>,Parsed,assign(Con{separator,tail}),rhs =>
              then(run(n,Term{False{}},S.skip_lines(rhs)),value => rest => run(n,BindingTail{name,quantity,None{},value,parent},rest)))),u =>
            binder_failure(tokens,name,"binding-name",U32.is_ne(quantity,0)))
        case _: invalid(tokens,"binding")
    case 1n+ +n AnnotatedBinding{+name,+quantity,+parent}:
      match tokens:
        case Con{+typ,+tail}:
          S.choose(Result<S.Error,Parsed>,S.identifier(typ),u =>
            S.choose(Result<S.Error,Parsed>,starts(tail,"<"),u =>
              unsupported(tail,"type-application"),u =>
            S.bind(List<&2,S.Token>,Parsed,assign(tail),rhs =>
              then(run(n,Term{False{}},S.skip_lines(rhs)),value => rest => run(n,BindingTail{name,quantity,Some{typ},value,parent},rest)))),u =>
            unsupported(tokens,"binding-type"))
        case _: invalid(tokens,"binding-type")
    case 1n+ +n BindingTail{+token,+quantity,+annotation,+value,+parent}:
      S.bind(List<&2,S.Token>,Parsed,line_end(tokens),body =>
        then(run(n,BodyAt{parent,False{}},S.skip_lines(body)),next => rest =>
          Done{Parsed{S.Binding{token,quantity,annotation,value,next},rest}}))
    case 1n+ +n RowTail{+keyword,+pattern,+parent,+column}:
      S.choose(Result<S.Error,Parsed>,starts(tokens,","),u =>
        S.bind(List<&2,S.Token>,Parsed,expect(tokens,","),tail =>
          then(run(n,Term{True{}},tail),more => rest =>
            run(n,RowTail{keyword,columns(pattern,more),parent,column},rest))),u =>
      S.choose(Result<S.Error,Parsed>,Bool.or(scrutinee(tokens),promotes(tokens)),u =>
        then(run(n,Term{True{}},tokens),more => rest =>
          run(n,RowTail{keyword,columns(pattern,more),parent,column},rest)),u =>
        S.bind(List<&2,S.Token>,Parsed,expect(tokens,":"),body =>
          then(run(n,Body{S.column(keyword)},body),value => after =>
            then(run(n,Arms{parent,column},S.skip_lines(after)),more => end =>
              prepend(S.Arm{keyword,pattern,value},more,end))))))
    case 1n+ +n Arms{+parent,+column}:
      match tokens:
        case Con{+keyword,+tail}:
          S.choose(Result<S.Error,Parsed>,Bool.or(S.matches(keyword,"<eof>"),U32.is_le(S.column(keyword),parent)),u =>
            Done{Parsed{S.Sequence{Nil{}},tokens}},u =>
          S.choose(Result<S.Error,Parsed>,Bool.and(S.matches(keyword,"case"),Bool.or(U32.is_eq(column,0),U32.is_eq(column,S.column(keyword)))),u =>
            then(run(n,Term{True{}},header(tail)),+pattern => +rest =>
              S.choose(Result<S.Error,Parsed>,Bool.or(starts(rest,","),Bool.or(scrutinee(rest),promotes(rest))),u =>
                run(n,RowTail{keyword,pattern,parent,S.column(keyword)},rest),u =>
              S.bind(List<&2,S.Token>,Parsed,expect(rest,":"),body =>
                then(run(n,Body{S.column(keyword)},body),value => after =>
                  then(run(n,Arms{parent,S.column(keyword)},S.skip_lines(after)),more => end =>
                    prepend(S.Arm{keyword,pattern,value},more,end)))))),u =>
            unsupported(tokens,"pattern-or-indentation")))
        case _: invalid(tokens,"unexpected-end")

def parse(depth: Nat, tokens: List<&2,S.Token>) -> Result<S.Error,Parsed>:
  run(depth,Book{},tokens)

import Base
import ./syntax.bend as S

type Parsed is Data:
  Parsed{value: S.Node, rest: List<&2,S.Token>}

type Mode is Data:
  Book{}
  Declaration{}
  Constructors{parent: U32, column: U32}
  Parameters{close: String}
  Arguments{close: String, pattern: Bool}
  Term{pattern: Bool}
  Body{parent: U32}
  StartBody{parent: U32}
  BodyAt{column: U32, first: Bool}
  Arms{parent: U32, column: U32}
  Header{keyword: S.Token, name: S.Token}
  TypeKind{name: S.Token}
  FunctionTail{token: S.Token, parameters: S.Node}
  MatchTail{token: S.Token, value: S.Node, column: U32}
  RowTail{token: S.Token, pattern: S.Node, parent: U32, column: U32}
  BindingStart{quantity: U32, column: U32}
  AnnotatedBinding{token: S.Token, quantity: U32, column: U32}
  BindingTail{token: S.Token, quantity: U32, annotation: Maybe<&2,S.Token>, value: S.Node, column: U32}
  ListTail{close: String, head: S.Node, parameters: Bool, pattern: Bool}

def invalid(+ts: List<&2,S.Token>, code: String) -> Result<S.Error,Parsed>:
  Fail{S.Invalid{"parse",code,S.here(ts)}}

def unsupported(+ts: List<&2,S.Token>, code: String) -> Result<S.Error,Parsed>:
  Fail{S.Unsupported{"parse",code,S.here(ts)}}

def starts(ts: List<&2,S.Token>, word: String) -> Bool:
  match ts:
    case Nil{}: False{}
    case Con{head,tail}: S.matches(head,word)

def touching(name: S.Token, ts: List<&2,S.Token>) -> Bool:
  match ts:
    case Nil{}: False{}
    case Con{head,tail}: S.touches(name,head)

def scrutinee(ts: List<&2,S.Token>) -> Bool:
  match ts:
    case Nil{}: False{}
    case Con{head,tail}: S.identifier(head)

def numeral(ts: List<&2,S.Token>) -> Bool:
  match ts:
    case Nil{}: False{}
    case Con{head,tail}: S.numeral(S.text(head))

# After a term, `a +b` opens another column and `a + b` is an operator.
def promotes(ts: List<&2,S.Token>) -> Bool:
  match ts:
    case Con{+plus,Con{next,rest}}: Bool.and(S.matches(plus,"+"),S.marks(plus,next))
    case _: False{}

# A row's next column opens at a name, a numeral, a parenthesis or a marking `+`.
def opens(+ts: List<&2,S.Token>) -> Bool:
  Bool.or(scrutinee(ts),Bool.or(numeral(ts),Bool.or(starts(ts,"("),promotes(ts))))

# After a term the seed reads an infix operator, a call, an index, an offload `!(` or, after a name, a
# lambda. A body the lowering discards holds any of them unchecked and a live one needs a target the
# program defines, so the parser leaves each unread: it is unsupported wherever a term ends.
# A `+` or `-` that touches a name is a marker; `.` opens only `.|.`, `.^.` and `.&.`.
def marker(ts: List<&2,S.Token>) -> Bool:
  match ts:
    case Con{+sign,Con{next,rest}}: Bool.and(Bool.or(S.matches(sign,"+"),S.matches(sign,"-")),S.marks(sign,next))
    case _: False{}

def operator(+ts: List<&2,S.Token>) -> Bool:
  match ts:
    case Nil{}: False{}
    case Con{+h,+t}:
      S.choose(Bool,S.matches(h,"."),u => Bool.or(starts(t,"|"),Bool.or(starts(t,"^"),starts(t,"&"))),u =>
        Bool.or(S.infix(h),Bool.and(Bool.or(S.matches(h,"+"),S.matches(h,"-")),Bool.not(marker(Con{h,t})))))

def bang(+ts: List<&2,S.Token>) -> Bool:
  match ts:
    case Con{+h,+t}: Bool.and(S.matches(h,"!"),starts(t,"("))
    case _: False{}

def suffix(+ts: List<&2,S.Token>) -> Bool:
  match ts:
    case Con{+h,+t}: Bool.or(Bool.or(S.matches(h,"("),S.matches(h,"[")),Bool.or(bang(Con{h,t}),operator(Con{h,t})))
    case _: False{}

def arrow(ts: List<&2,S.Token>) -> Bool:
  match ts:
    case Con{+eq,+t}: Bool.and(S.matches(eq,"="),Bool.and(starts(t,">"),touching(eq,t)))
    case _: False{}

def variable(node: S.Node) -> Bool:
  match node:
    case S.Variable{token}: True{}
    case _: False{}

def lambda(value: S.Node, ts: List<&2,S.Token>) -> Bool:
  Bool.and(arrow(ts),variable(value))

# A line that starts with an operator, `!(` or `=>` continues the term before it; one with `(` or `[` does not.
def continues(+ts: List<&2,S.Token>) -> Bool:
  Bool.or(operator(ts),Bool.or(bang(ts),arrow(ts)))

# A line break, then a name: whitespace to the seed.
def broken(+ts: List<&2,S.Token>) -> Bool:
  Bool.and(starts(ts,"\n"),scrutinee(S.skip_lines(ts)))

# The seed accepts a rebound dotted binder, `++y` and a name after a line break,
# which the parser cannot tell: each is unsupported; other unbindable names are invalid.
def binder_failure(+ts: List<&2,S.Token>, +name: S.Token, code: String, promoted: Bool) -> Result<S.Error,Parsed>:
  S.choose(Result<S.Error,Parsed>,S.identifier(name),u => unsupported(ts,"dotted-binder"),u =>
  S.choose(Result<S.Error,Parsed>,Bool.and(promoted,S.matches(name,"+")),u => unsupported(ts,"repeated-promotion"),u =>
  S.choose(Result<S.Error,Parsed>,broken(ts),u => unsupported(ts,"line-break"),u =>
    invalid(ts,code))))

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

def wrap_function(token: S.Token, params: S.Node, result: S.Token,
  body: S.Node, rest: List<&2,S.Token>) -> Result<S.Error,Parsed>:
  match params:
    case S.Sequence{items}: Done{Parsed{S.Function{token,items,result,body},rest}}
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

# A line break before a let's `=` or `:` is whitespace to the seed.
def split(+ts: List<&2,S.Token>) -> Bool:
  Bool.and(starts(ts,"\n"),Bool.or(starts(S.skip_lines(ts),"="),starts(S.skip_lines(ts),":")))

# The seed reads `+name` that starts no let as a promoted term, which an operator may continue.
def promoted_term(+quantity: U32, +ts: List<&2,S.Token>) -> Bool:
  Bool.and(U32.is_eq(quantity,2),Bool.or(Bool.and(Bool.or(starts(ts,"\n"),starts(ts,"<eof>")),Bool.not(split(ts))),operator(ts)))

# The seed reads any term after a scrutinee, unchecked in a discarded match: a header
# ends only at a closer, a separator or a keyword.
def term_start(ts: List<&2,S.Token>) -> Bool:
  match ts:
    case Nil{}: False{}
    case Con{+h,t}: Bool.not(Bool.or(S.closes(h),S.reserved(S.text(h))))

# So is one before its value.
def assign(+ts: List<&2,S.Token>) -> Result<S.Error,List<&2,S.Token>>:
  S.choose(Result<S.Error,List<&2,S.Token>>,split(ts),u =>
    Fail{S.Unsupported{"parse","line-break",S.here(ts)}},u =>
  S.bind(List<&2,S.Token>,List<&2,S.Token>,expect(ts,"="),+rhs =>
    S.choose(Result<S.Error,List<&2,S.Token>>,broken(rhs),u =>
      Fail{S.Unsupported{"parse","line-break",S.here(rhs)}},u =>
    S.choose(Result<S.Error,List<&2,S.Token>>,Bool.and(starts(rhs,"\n"),Bool.and(Bool.not(scrutinee(S.skip_lines(rhs))),term_start(S.skip_lines(rhs)))),u =>
      Fail{S.Unsupported{"parse","line-break",S.here(rhs)}},u => Done{rhs}))))

# The seed reads the next statement on the line of a let's value.
def line_end(+ts: List<&2,S.Token>) -> Result<S.Error,List<&2,S.Token>>:
  match ts:
    case Con{+h,t}:
      S.choose(Result<S.Error,List<&2,S.Token>>,S.statement(h),u =>
        Fail{S.Unsupported{"parse","same-line-statement",S.at(h)}},u =>
      S.choose(Result<S.Error,List<&2,S.Token>>,suffix(ts),u =>
        Fail{S.Unsupported{"parse","term-form",S.at(h)}},u => expect(ts,"\n")))
    case Nil{}: expect(ts,"\n")

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

# The seed reads a second arm, or the next declaration, on the line of a body's end.
def body_end(value: S.Node, +ts: List<&2,S.Token>) -> Result<S.Error,Parsed>:
  match ts:
    case Con{+h,t}:
      S.choose(Result<S.Error,Parsed>,Bool.or(S.matches(h,"\n"),S.matches(h,"<eof>")),u =>
        Done{Parsed{value,ts}},u =>
      S.choose(Result<S.Error,Parsed>,S.matches(h,"case"),u => unsupported(ts,"same-line-arm"),u =>
      S.choose(Result<S.Error,Parsed>,Bool.or(S.matches(h,"def"),S.matches(h,"type")),u => unsupported(ts,"same-line-declaration"),u =>
        invalid(ts,"end-of-body"))))
    case _: invalid(ts,"unexpected-end")

def terminated(+value: S.Node, +ts: List<&2,S.Token>) -> Result<S.Error,Parsed>:
  match value:
    case S.Constructor{token,items}:
      match ts:
        case Con{+head,+tail}:
          S.choose(Result<S.Error,Parsed>,S.matches(head,"="),u =>
            S.choose(Result<S.Error,Parsed>,Bool.or(starts(tail,"="),starts(tail,">")),u =>
              body_end(value,ts),u => unsupported(ts,"destructuring-binding")),u => body_end(value,ts))
        case Nil{}: body_end(value,ts)
    case _: body_end(value,ts)

def reply(+value: S.Node, +ts: List<&2,S.Token>) -> Result<S.Error,Parsed>:
  S.choose(Result<S.Error,Parsed>,suffix(ts),u => unsupported(ts,"term-form"),u => terminated(value,ts))

def term_failure(+ts: List<&2,S.Token>) -> Result<S.Error,Parsed>:
  match ts:
    case Con{+h,t}: S.choose(Result<S.Error,Parsed>,S.closes(h),u => invalid(ts,"expected-term"),u => unsupported(ts,"term-form"))
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
          # The seed reads a case left of its match's column as a row of that match, and a declaration at any column.
          S.choose(Result<S.Error,Parsed>,S.matches(head,"case"),u =>
            unsupported(tokens,"pattern-or-indentation"),u =>
          S.choose(Result<S.Error,Parsed>,U32.is_eq(S.column(head),0),u =>
            then(run(n,Header{head,name},tail),value => rest =>
              then(run(n,Book{},rest),more => end => prepend(value,more,end))),u =>
          S.choose(Result<S.Error,Parsed>,Bool.or(S.matches(head,"def"),S.matches(head,"type")),u =>
            unsupported(tokens,"top-level-indentation"),u =>
          S.choose(Result<S.Error,Parsed>,continues(tokens),u =>
            unsupported(tokens,"term-form"),u => invalid(tokens,"top-level-indentation"))))))
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
              then(run(n,Parameters{"}"},open),fields => closed =>
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
            then(parameter(tokens),p => rest => run(n,ListTail{close,p,True{},False{}},rest))))
        case _: invalid(tokens,"unexpected-end")
    case 1n+ +n Arguments{+close,+pattern}:
      match tokens:
        case Con{+h,+t}:
          S.choose(Result<S.Error,Parsed>,S.matches(h,close),u =>
            Done{Parsed{S.Sequence{Nil{}},t}},u =>
          # The seed reads a line break inside call or constructor arguments as
          # whitespace, which a term here does not: Arguments and ListTail stop at it.
          S.choose(Result<S.Error,Parsed>,S.matches(h,"\n"),u => unsupported(tokens,"line-break"),u =>
            then(run(n,Term{pattern},tokens),arg => rest => run(n,ListTail{close,arg,False{},pattern},rest))))
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
              then(run(n,Bool.pick(Mode,parameters,Parameters{close},Arguments{close,pattern}),t),more => rest => prepend(head,more,rest))),u =>
            S.choose(Result<S.Error,Parsed>,Bool.and(Bool.not(parameters),Bool.or(scrutinee(tokens),Bool.or(numeral(tokens),Bool.or(starts(tokens,"("),Bool.and(pattern,promotes(tokens)))))),u => unsupported(tokens,"argument-whitespace"),u =>
            S.choose(Result<S.Error,Parsed>,Bool.and(Bool.not(Bool.or(parameters,pattern)),Bool.or(suffix(tokens),lambda(head,tokens))),u => unsupported(tokens,"term-form"),u =>
            S.choose(Result<S.Error,Parsed>,Bool.and(Bool.not(parameters),S.matches(h,"\n")),u => unsupported(tokens,"line-break"),u =>
              invalid(tokens,"argument-separator"))))))
        case _: invalid(tokens,"unexpected-end")
    case 1n+ +n Term{+pattern}:
      match tokens:
        case Con{+name,Con{+open,+tail}}:
          S.choose(Result<S.Error,Parsed>,Bool.and(pattern,S.matches(name,"+")),u =>
            S.choose(Result<S.Error,Parsed>,S.binder(open),u => Done{Parsed{S.Promotion{open},tail}},u => binder_failure(tokens,open,"pattern-binder",True{})),u =>
          S.choose(Result<S.Error,Parsed>,S.identifier(name),u =>
          S.choose(Result<S.Error,Parsed>,Bool.and(S.matches(open,"("),S.same_line(name,open)),u =>
            then(run(n,Arguments{")",pattern},tail),args => rest => wrap_call(name,False{},args,rest)),u =>
          S.choose(Result<S.Error,Parsed>,S.matches(open,"{"),u =>
            # Fields open at a brace touching the name, as in the seed.
            S.choose(Result<S.Error,Parsed>,S.touches(name,open),u =>
              then(run(n,Arguments{"}",pattern},tail),args => rest => wrap_call(name,True{},args,rest)),u =>
              invalid(Con{open,tail},"detached-brace")),u =>
          S.choose(Result<S.Error,Parsed>,Bool.or(Bool.not(pattern),S.binder(name)),u =>
            Done{Parsed{S.Variable{name},Con{open,tail}}},u => binder_failure(tokens,name,"pattern-binder",True{})))),u =>
            term_failure(tokens)))
        case _: invalid(tokens,"term")
    case 1n+ +n Body{+parent}:
      run(n,StartBody{parent},S.skip_lines(tokens))
    case 1n+ +n StartBody{+parent}:
      match tokens:
        case Con{+h,t}:
          S.choose(Result<S.Error,Parsed>,U32.is_gt(S.column(h),parent),u =>
            run(n,BodyAt{S.column(h),True{}},tokens),u =>
          # The seed lays an arm body out anywhere; a def body keeps its indentation.
          S.choose(Result<S.Error,Parsed>,Bool.and(U32.is_gt(parent,0),S.statement(h)),u =>
            unsupported(tokens,"body-indentation"),u => invalid(tokens,"body-indentation")))
        case _: invalid(tokens,"body")
    case 1n+ +n BodyAt{+column,+first}:
      match tokens:
        case Con{+h,Con{+second,+tail}}:
          S.choose(Result<S.Error,Parsed>,U32.is_eq(S.column(h),column),u =>
          S.choose(Result<S.Error,Parsed>,S.matches(h,"match"),u =>
            then(run(n,Term{False{}},header(Con{second,tail})),value => rest => run(n,MatchTail{h,value,S.column(h)},rest)),u =>
          S.choose(Result<S.Error,Parsed>,Bool.or(S.matches(h,"+"),S.matches(h,"-")),u =>
            # After a let, the seed reads a spaced marker as an operator on its value.
            S.choose(Result<S.Error,Parsed>,Bool.or(first,S.marks(h,second)),u =>
              run(n,BindingStart{Bool.pick(U32,S.matches(h,"+"),2,0),S.column(h)},Con{second,tail}),u =>
              invalid(tokens,"detached-marker")),u =>
          S.choose(Result<S.Error,Parsed>,Bool.or(S.matches(second,"="),S.matches(second,":")),u =>
            run(n,BindingStart{1,S.column(h)},tokens),u =>
          S.choose(Result<S.Error,Parsed>,Bool.and(S.identifier(h),split(Con{second,tail})),u =>
            unsupported(Con{second,tail},"line-break"),u =>
            then(run(n,Term{False{}},tokens),value => rest => reply(value,rest)))))),u =>
          # The seed checks no column for a statement, and an operator continues the term before it.
          S.choose(Result<S.Error,Parsed>,S.statement(h),u =>
            unsupported(tokens,"body-indentation"),u =>
          S.choose(Result<S.Error,Parsed>,continues(tokens),u =>
            unsupported(tokens,"term-form"),u => invalid(tokens,"body-indentation"))))
        case _: invalid(tokens,"body")
    case 1n+ +n Header{+keyword,+name}:
      S.choose(Result<S.Error,Parsed>,Bool.and(S.matches(keyword,"import"),Bool.and(starts(tokens,"/"),
        Bool.or(S.matches(name,"."),String.starts_with(S.text(name),"0x")))),u =>
        unsupported(Con{name,tokens},"import"),u =>
      S.choose(Result<S.Error,Parsed>,S.identifier(name),u =>
      S.choose(Result<S.Error,Parsed>,S.matches(keyword,"type"),u =>
      S.choose(Result<S.Error,Parsed>,starts(tokens,"<"),u =>
        unsupported(tokens,"generic-datatype"),u =>
        S.bind(List<&2,S.Token>,Parsed,expect(tokens,"is"),kind =>
          run(n,TypeKind{name},kind))),u =>
      S.choose(Result<S.Error,Parsed>,S.matches(keyword,"def"),u =>
        S.bind(List<&2,S.Token>,Parsed,expect(tokens,"("),args =>
          then(run(n,Parameters{")"},args),params => rest => run(n,FunctionTail{name,params},rest))),u =>
        unsupported(Con{keyword,tokens},"declaration-form"))),u =>
      S.choose(Result<S.Error,Parsed>,continues(Con{keyword,Con{name,tokens}}),u =>
        unsupported(Con{keyword,Con{name,tokens}},"term-form"),u => invalid(tokens,"declaration-name"))))
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
      S.choose(Result<S.Error,Parsed>,term_start(tokens),u =>
        then(run(n,Term{False{}},tokens),more => rest =>
          run(n,MatchTail{token,columns(value,more),column},rest)),u =>
      S.bind(List<&2,S.Token>,Parsed,expect(tokens,":"),arms =>
        then(run(n,Arms{column,0},S.skip_lines(arms)),items => rest => wrap_match(token,value,items,rest)))))
    case 1n+ +n BindingStart{+quantity,+column}:
      match tokens:
        case Con{+name,Con{+separator,+tail}}:
          # The seed reads an erased let's name as a name, any other as a pattern.
          S.choose(Result<S.Error,Parsed>,Bool.and(S.identifier(name),Bool.or(U32.is_eq(quantity,0),S.binder(name))),u =>
          S.choose(Result<S.Error,Parsed>,S.matches(separator,":"),u =>
            run(n,AnnotatedBinding{name,quantity,column},tail),u =>
          S.choose(Result<S.Error,Parsed>,promoted_term(quantity,Con{separator,tail}),u =>
            unsupported(tokens,"term-form"),u =>
            S.bind(List<&2,S.Token>,Parsed,assign(Con{separator,tail}),rhs =>
              then(run(n,Term{False{}},rhs),value => rest => run(n,BindingTail{name,quantity,None{},value,column},rest))))),u =>
          S.choose(Result<S.Error,Parsed>,Bool.or(continues(tokens),Bool.and(U32.is_eq(quantity,2),starts(S.skip_lines(tokens),"("))),u =>
            unsupported(tokens,"term-form"),u =>
          S.choose(Result<S.Error,Parsed>,Bool.and(U32.is_eq(quantity,2),Bool.and(starts(tokens,"\n"),starts(S.skip_lines(tokens),"+"))),u =>
            unsupported(tokens,"repeated-promotion"),u =>
            binder_failure(tokens,name,"binding-name",U32.is_ne(quantity,0)))))
        case _: invalid(tokens,"binding")
    case 1n+ +n AnnotatedBinding{+name,+quantity,+column}:
      match tokens:
        case Con{+typ,+tail}:
          S.choose(Result<S.Error,Parsed>,S.identifier(typ),u =>
            S.choose(Result<S.Error,Parsed>,starts(tail,"<"),u =>
              unsupported(tail,"type-application"),u =>
            S.bind(List<&2,S.Token>,Parsed,assign(tail),rhs =>
              then(run(n,Term{False{}},rhs),value => rest => run(n,BindingTail{name,quantity,Some{typ},value,column},rest)))),u =>
            unsupported(tokens,"binding-type"))
        case _: invalid(tokens,"binding-type")
    case 1n+ +n BindingTail{+token,+quantity,+annotation,+value,+column}:
      S.choose(Result<S.Error,Parsed>,lambda(value,tokens),u => unsupported(tokens,"term-form"),u =>
      S.bind(List<&2,S.Token>,Parsed,line_end(tokens),body =>
        then(run(n,BodyAt{column,False{}},S.skip_lines(body)),next => rest =>
          Done{Parsed{S.Binding{token,quantity,annotation,value,next},rest}})))
    case 1n+ +n RowTail{+keyword,+pattern,+parent,+column}:
      S.choose(Result<S.Error,Parsed>,starts(tokens,","),u =>
        S.bind(List<&2,S.Token>,Parsed,expect(tokens,","),tail =>
          then(run(n,Term{True{}},tail),more => rest =>
            run(n,RowTail{keyword,columns(pattern,more),parent,column},rest))),u =>
      S.choose(Result<S.Error,Parsed>,opens(tokens),u =>
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
              S.choose(Result<S.Error,Parsed>,Bool.or(starts(rest,","),opens(rest)),u =>
                run(n,RowTail{keyword,pattern,parent,S.column(keyword)},rest),u =>
              S.bind(List<&2,S.Token>,Parsed,expect(rest,":"),body =>
                then(run(n,Body{S.column(keyword)},body),value => after =>
                  then(run(n,Arms{parent,S.column(keyword)},S.skip_lines(after)),more => end =>
                    prepend(S.Arm{keyword,pattern,value},more,end)))))),u =>
            unsupported(tokens,"pattern-or-indentation")))
        case _: invalid(tokens,"unexpected-end")

def parse(depth: Nat, tokens: List<&2,S.Token>) -> Result<S.Error,Parsed>:
  run(depth,Book{},tokens)

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
  BodyAt{column: U32}
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

def scrutinee(ts: List<&2,S.Token>) -> Bool:
  match ts:
    case Nil{}: False{}
    case Con{head,tail}: S.identifier(head)

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

def body_end(value: S.Node, +ts: List<&2,S.Token>) -> Result<S.Error,Parsed>:
  match ts:
    case Con{h,t}:
      S.choose(Result<S.Error,Parsed>,Bool.or(S.matches(h,"\n"),S.matches(h,"<eof>")),u =>
        Done{Parsed{value,ts}},u => invalid(ts,"end-of-body"))
    case _: invalid(ts,"unexpected-end")

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

def term_failure(+ts: List<&2,S.Token>) -> Result<S.Error,Parsed>:
  match ts:
    case Con{+h,t}:
      S.choose(Result<S.Error,Parsed>,Bool.or(S.matches(h,")"),Bool.or(S.matches(h,"}"),
        Bool.or(S.matches(h,":"),Bool.or(S.matches(h,","),Bool.or(S.matches(h,"\n"),S.matches(h,"<eof>")))))),u =>
          invalid(ts,"expected-term"),u => unsupported(ts,"term-form"))
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
            then(run(n,Term{pattern},tokens),arg => rest => run(n,ListTail{close,arg,False{},pattern},rest)))
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
            invalid(tokens,"argument-separator")))
        case _: invalid(tokens,"unexpected-end")
    case 1n+ +n Term{+pattern}:
      match tokens:
        case Con{+name,Con{+open,+tail}}:
          S.choose(Result<S.Error,Parsed>,Bool.and(pattern,S.matches(name,"+")),u =>
            S.choose(Result<S.Error,Parsed>,S.binder(open),u => Done{Parsed{S.Promotion{open},tail}},u => invalid(tokens,"pattern-binder")),u =>
          S.choose(Result<S.Error,Parsed>,S.identifier(name),u =>
          S.choose(Result<S.Error,Parsed>,S.matches(open,"("),u =>
            then(run(n,Arguments{")",pattern},tail),args => rest => wrap_call(name,False{},args,rest)),u =>
          S.choose(Result<S.Error,Parsed>,S.matches(open,"{"),u =>
            # Fields open at a brace touching the name, as in the seed.
            S.choose(Result<S.Error,Parsed>,S.touches(name,open),u =>
              then(run(n,Arguments{"}",pattern},tail),args => rest => wrap_call(name,True{},args,rest)),u =>
              invalid(Con{open,tail},"detached-brace")),u =>
          S.choose(Result<S.Error,Parsed>,Bool.or(Bool.not(pattern),S.binder(name)),u =>
            Done{Parsed{S.Variable{name},Con{open,tail}}},u => invalid(tokens,"pattern-binder")))),u =>
            term_failure(tokens)))
        case _: invalid(tokens,"term")
    case 1n+ +n Body{+parent}:
      run(n,StartBody{parent},S.skip_lines(tokens))
    case 1n+ +n StartBody{+parent}:
      match tokens:
        case Con{+h,t}:
          S.choose(Result<S.Error,Parsed>,U32.is_gt(S.column(h),parent),u =>
            run(n,BodyAt{S.column(h)},tokens),u => invalid(tokens,"body-indentation"))
        case _: invalid(tokens,"body")
    case 1n+ +n BodyAt{+column}:
      match tokens:
        case Con{+h,Con{+second,+tail}}:
          S.choose(Result<S.Error,Parsed>,U32.is_eq(S.column(h),column),u =>
          S.choose(Result<S.Error,Parsed>,S.matches(h,"match"),u =>
            then(run(n,Term{False{}},header(Con{second,tail})),value => rest => run(n,MatchTail{h,value,S.column(h)},rest)),u =>
          S.choose(Result<S.Error,Parsed>,Bool.or(S.matches(h,"+"),S.matches(h,"-")),u =>
            run(n,BindingStart{Bool.pick(U32,S.matches(h,"+"),2,0),S.column(h)},Con{second,tail}),u =>
          S.choose(Result<S.Error,Parsed>,Bool.or(S.matches(second,"="),S.matches(second,":")),u =>
            run(n,BindingStart{1,S.column(h)},tokens),u =>
            then(run(n,Term{False{}},tokens),value => rest => reply(value,rest))))),u =>
            invalid(tokens,"body-indentation"))
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
          S.choose(Result<S.Error,Parsed>,Bool.and(S.matches(dash,"-"),Bool.and(S.matches(arrow,">"),S.identifier(typ))),u =>
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
    case 1n+ +n BindingStart{+quantity,+column}:
      match tokens:
        case Con{+name,Con{+separator,+tail}}:
          # The seed reads an erased let's name as a name, any other as a pattern.
          S.choose(Result<S.Error,Parsed>,Bool.and(S.identifier(name),Bool.or(U32.is_eq(quantity,0),S.binder(name))),u =>
          S.choose(Result<S.Error,Parsed>,S.matches(separator,":"),u =>
            run(n,AnnotatedBinding{name,quantity,column},tail),u =>
            S.bind(List<&2,S.Token>,Parsed,expect(Con{separator,tail},"="),rhs =>
              then(run(n,Term{False{}},rhs),value => rest => run(n,BindingTail{name,quantity,None{},value,column},rest)))),u =>
            invalid(tokens,"binding-name"))
        case _: invalid(tokens,"binding")
    case 1n+ +n AnnotatedBinding{+name,+quantity,+column}:
      match tokens:
        case Con{+typ,+tail}:
          S.choose(Result<S.Error,Parsed>,S.identifier(typ),u =>
            S.choose(Result<S.Error,Parsed>,starts(tail,"<"),u =>
              unsupported(tail,"type-application"),u =>
            S.bind(List<&2,S.Token>,Parsed,expect(tail,"="),rhs =>
              then(run(n,Term{False{}},rhs),value => rest => run(n,BindingTail{name,quantity,Some{typ},value,column},rest)))),u =>
            unsupported(tokens,"binding-type"))
        case _: invalid(tokens,"binding-type")
    case 1n+ +n BindingTail{+token,+quantity,+annotation,+value,+column}:
      S.bind(List<&2,S.Token>,Parsed,expect(tokens,"\n"),body =>
        then(run(n,BodyAt{column},S.skip_lines(body)),next => rest =>
          Done{Parsed{S.Binding{token,quantity,annotation,value,next},rest}}))
    case 1n+ +n RowTail{+keyword,+pattern,+parent,+column}:
      S.choose(Result<S.Error,Parsed>,starts(tokens,","),u =>
        S.bind(List<&2,S.Token>,Parsed,expect(tokens,","),tail =>
          then(run(n,Term{True{}},tail),more => rest =>
            run(n,RowTail{keyword,columns(pattern,more),parent,column},rest))),u =>
      S.choose(Result<S.Error,Parsed>,Bool.or(scrutinee(tokens),starts(tokens,"+")),u =>
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
              S.choose(Result<S.Error,Parsed>,Bool.or(starts(rest,","),Bool.or(scrutinee(rest),starts(rest,"+"))),u =>
                run(n,RowTail{keyword,pattern,parent,S.column(keyword)},rest),u =>
              S.bind(List<&2,S.Token>,Parsed,expect(rest,":"),body =>
                then(run(n,Body{S.column(keyword)},body),value => after =>
                  then(run(n,Arms{parent,S.column(keyword)},S.skip_lines(after)),more => end =>
                    prepend(S.Arm{keyword,pattern,value},more,end)))))),u =>
            unsupported(tokens,"pattern-or-indentation")))
        case _: invalid(tokens,"unexpected-end")

def parse(depth: Nat, tokens: List<&2,S.Token>) -> Result<S.Error,Parsed>:
  run(depth,Book{},tokens)

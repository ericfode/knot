import Base
import ./syntax.bend as S

type Parsed is Data:
  Parsed{value: S.Node, rest: List<&2,S.Token>}

type Mode is Data:
  Book{}
  Declaration{}
  Constructors{parent: U32, column: U32}
  Parameters{}
  Arguments{close: String}
  Term{}
  Body{parent: U32}
  StartBody{parent: U32}
  BodyAt{column: U32}
  Arms{parent: U32, column: U32}
  Header{keyword: S.Token, name: S.Token}
  TypeKind{name: S.Token}
  FunctionTail{token: S.Token, parameters: S.Node}
  MatchTail{token: S.Token, value: S.Node, column: U32}
  BindingStart{quantity: U32, column: U32}
  AnnotatedBinding{token: S.Token, quantity: U32, column: U32}
  BindingTail{token: S.Token, quantity: U32, annotation: Maybe<&2,S.Token>, value: S.Node, column: U32}
  ListTail{close: String, head: S.Node, parameters: Bool}

def invalid(+ts: List<&2,S.Token>, code: String) -> Result<S.Error,Parsed>:
  Fail{S.Invalid{"parse",code,S.here(ts)}}

def unsupported(+ts: List<&2,S.Token>, code: String) -> Result<S.Error,Parsed>:
  Fail{S.Unsupported{"parse",code,S.here(ts)}}

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

def parameter_parts(+quantity: U32, +ts: List<&2,S.Token>) -> Result<S.Error,Parsed>:
  match ts:
    case Con{+name,Con{+colon,Con{+typ,+rest}}}:
      S.choose(Result<S.Error,Parsed>,Bool.and(S.identifier(name),Bool.and(S.matches(colon,":"),S.identifier(typ))),u =>
        Done{Parsed{S.Parameter{name,quantity,typ},rest}},u => invalid(ts,"parameter"))
    case _: invalid(ts,"parameter")

def parameter(+ts: List<&2,S.Token>) -> Result<S.Error,Parsed>:
  match ts:
    case Con{+h,+t}:
      S.choose(Result<S.Error,Parsed>,S.matches(h,"-"),u => parameter_parts(0,t),u =>
      S.choose(Result<S.Error,Parsed>,S.matches(h,"+"),u => parameter_parts(2,t),u =>
        parameter_parts(1,ts)))
    case _: invalid(ts,"parameter")

def body_end(value: S.Node, +ts: List<&2,S.Token>) -> Result<S.Error,Parsed>:
  match ts:
    case Con{h,t}:
      S.choose(Result<S.Error,Parsed>,Bool.or(S.matches(h,"\n"),S.matches(h,"<eof>")),u =>
        Done{Parsed{value,ts}},u => invalid(ts,"end-of-body"))
    case _: invalid(ts,"unexpected-end")

def term_failure(+ts: List<&2,S.Token>) -> Result<S.Error,Parsed>:
  match ts:
    case Con{+h,t}:
      S.choose(Result<S.Error,Parsed>,Bool.or(S.matches(h,")"),Bool.or(S.matches(h,"}"),
        Bool.or(S.matches(h,":"),Bool.or(S.matches(h,","),Bool.or(S.matches(h,"\n"),S.matches(h,"<eof>")))))),u =>
          invalid(ts,"expected-term"),u => unsupported(ts,"term-form"))
    case _: invalid(ts,"unexpected-end")

def constructor_close(+ts: List<&2,S.Token>) -> Result<S.Error,List<&2,S.Token>>:
  match ts:
    case Con{+h,+t}:
      S.choose(Result<S.Error,List<&2,S.Token>>,S.matches(h,"}"),u => Done{t},u =>
        Fail{S.Unsupported{"parse","constructor-fields",S.at(h)}})
    case _: Fail{S.Invalid{"parse","constructor",S.here(ts)}}

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
              S.bind(List<&2,S.Token>,Parsed,constructor_close(open),closed =>
                then(body_end(S.Constructor{name,Nil{}},closed),ctor => after =>
                  then(run(n,Constructors{parent,S.column(name)},S.skip_lines(after)),more => end => prepend(ctor,more,end))))),u =>
            unsupported(tokens,"constructor-fields-or-indentation")))
        case _: invalid(tokens,"unexpected-end")
    case 1n+ +n Parameters{}:
      match tokens:
        case Con{+h,+t}:
          S.choose(Result<S.Error,Parsed>,S.matches(h,")"),u =>
            Done{Parsed{S.Sequence{Nil{}},t}},u =>
            then(parameter(tokens),p => rest => run(n,ListTail{")",p,True{}},rest)))
        case _: invalid(tokens,"unexpected-end")
    case 1n+ +n Arguments{+close}:
      match tokens:
        case Con{+h,+t}:
          S.choose(Result<S.Error,Parsed>,S.matches(h,close),u =>
            Done{Parsed{S.Sequence{Nil{}},t}},u =>
            then(run(n,Term{},tokens),arg => rest => run(n,ListTail{close,arg,False{}},rest)))
        case _: invalid(tokens,"unexpected-end")
    case 1n+ +n ListTail{+close,+head,+parameters}:
      match tokens:
        case Con{+h,+t}:
          S.choose(Result<S.Error,Parsed>,S.matches(h,close),u =>
            Done{Parsed{S.Sequence{Con{head,Nil{}}},t}},u =>
          S.choose(Result<S.Error,Parsed>,S.matches(h,","),u =>
            then(run(n,Bool.pick(Mode,parameters,Parameters{},Arguments{close}),t),more => rest => prepend(head,more,rest)),u =>
            invalid(tokens,"argument-separator")))
        case _: invalid(tokens,"unexpected-end")
    case 1n+ +n Term{}:
      match tokens:
        case Con{+name,Con{+open,+tail}}:
          S.choose(Result<S.Error,Parsed>,S.identifier(name),u =>
          S.choose(Result<S.Error,Parsed>,S.matches(open,"("),u =>
            then(run(n,Arguments{")"},tail),args => rest => wrap_call(name,False{},args,rest)),u =>
          S.choose(Result<S.Error,Parsed>,S.matches(open,"{"),u =>
            then(run(n,Arguments{"}"},tail),args => rest => wrap_call(name,True{},args,rest)),u =>
            Done{Parsed{S.Variable{name},Con{open,tail}}})),u =>
            term_failure(tokens))
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
            then(run(n,Term{},Con{second,tail}),value => rest => run(n,MatchTail{h,value,S.column(h)},rest)),u =>
          S.choose(Result<S.Error,Parsed>,Bool.or(S.matches(h,"+"),S.matches(h,"-")),u =>
            run(n,BindingStart{Bool.pick(U32,S.matches(h,"+"),2,0),S.column(h)},Con{second,tail}),u =>
          S.choose(Result<S.Error,Parsed>,Bool.or(S.matches(second,"="),S.matches(second,":")),u =>
            run(n,BindingStart{1,S.column(h)},tokens),u =>
            then(run(n,Term{},tokens),value => rest => body_end(value,rest))))),u =>
            invalid(tokens,"body-indentation"))
        case _: invalid(tokens,"body")
    case 1n+ +n Header{+keyword,+name}:
      S.choose(Result<S.Error,Parsed>,S.identifier(name),u =>
      S.choose(Result<S.Error,Parsed>,S.matches(keyword,"type"),u =>
        S.bind(List<&2,S.Token>,Parsed,expect(tokens,"is"),kind =>
          run(n,TypeKind{name},kind)),u =>
      S.choose(Result<S.Error,Parsed>,S.matches(keyword,"def"),u =>
        S.bind(List<&2,S.Token>,Parsed,expect(tokens,"("),args =>
          then(run(n,Parameters{},args),params => rest => run(n,FunctionTail{name,params},rest))),u =>
        unsupported(Con{keyword,tokens},"declaration-form"))),u => invalid(tokens,"declaration-name"))
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
          S.choose(Result<S.Error,Parsed>,Bool.and(S.matches(dash,"-"),Bool.and(S.matches(arrow,">"),Bool.and(S.identifier(typ),S.matches(colon,":")))),u =>
            then(run(n,Body{0},body),value => rest => wrap_function(name,S.Sequence{params},typ,value,rest)),u =>
            invalid(tokens,"function-result"))
        case _: invalid(tokens,"function-result")
    case 1n+ +n FunctionTail{token,other}:
      Fail{S.Internal{"parse","declaration-mode"}}
    case 1n+ +n MatchTail{+token,+value,+column}:
      S.bind(List<&2,S.Token>,Parsed,expect(tokens,":"),arms =>
        then(run(n,Arms{column,0},S.skip_lines(arms)),items => rest => wrap_match(token,value,items,rest)))
    case 1n+ +n BindingStart{+quantity,+column}:
      match tokens:
        case Con{+name,Con{+separator,+tail}}:
          S.choose(Result<S.Error,Parsed>,S.identifier(name),u =>
          S.choose(Result<S.Error,Parsed>,S.matches(separator,":"),u =>
            run(n,AnnotatedBinding{name,quantity,column},tail),u =>
            S.bind(List<&2,S.Token>,Parsed,expect(Con{separator,tail},"="),rhs =>
              then(run(n,Term{},rhs),value => rest => run(n,BindingTail{name,quantity,None{},value,column},rest)))),u =>
            invalid(tokens,"binding-name"))
        case _: invalid(tokens,"binding")
    case 1n+ +n AnnotatedBinding{+name,+quantity,+column}:
      match tokens:
        case Con{+typ,+tail}:
          S.choose(Result<S.Error,Parsed>,S.identifier(typ),u =>
            S.bind(List<&2,S.Token>,Parsed,expect(tail,"="),rhs =>
              then(run(n,Term{},rhs),value => rest => run(n,BindingTail{name,quantity,Some{typ},value,column},rest))),u =>
            unsupported(tokens,"binding-type"))
        case _: invalid(tokens,"binding-type")
    case 1n+ +n BindingTail{+token,+quantity,+annotation,+value,+column}:
      S.bind(List<&2,S.Token>,Parsed,expect(tokens,"\n"),body =>
        then(run(n,BodyAt{column},S.skip_lines(body)),next => rest =>
          Done{Parsed{S.Binding{token,quantity,annotation,value,next},rest}}))
    case 1n+ +n Arms{+parent,+column}:
      match tokens:
        case Con{+keyword,+tail}:
          S.choose(Result<S.Error,Parsed>,Bool.or(S.matches(keyword,"<eof>"),U32.is_le(S.column(keyword),parent)),u =>
            Done{Parsed{S.Sequence{Nil{}},tokens}},u =>
          S.choose(Result<S.Error,Parsed>,Bool.and(S.matches(keyword,"case"),Bool.or(U32.is_eq(column,0),U32.is_eq(column,S.column(keyword)))),u =>
            then(run(n,Term{},tail),pattern => rest =>
              S.bind(List<&2,S.Token>,Parsed,expect(rest,":"),body =>
                then(run(n,Body{S.column(keyword)},body),value => after =>
                  then(run(n,Arms{parent,S.column(keyword)},S.skip_lines(after)),more => end =>
                    prepend(S.Arm{keyword,pattern,value},more,end))))),u =>
            unsupported(tokens,"pattern-or-indentation")))
        case _: invalid(tokens,"unexpected-end")

def parse(depth: Nat, tokens: List<&2,S.Token>) -> Result<S.Error,Parsed>:
  run(depth,Book{},tokens)

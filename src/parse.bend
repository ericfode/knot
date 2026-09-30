import Base
import ./syntax.bend as S
import ./closure-types.bend as F
import ./parse-visibility.bend as V

type Parsed is Data:
  Parsed{value: S.Node, rest: List<&2,S.Token>}

type Mode is Data:
  Book{}
  Declaration{}
  Constructors{parent: U32, column: U32}
  Parameters{close: String}
  Arguments{close: String, pattern: Bool}
  Term{pattern: Bool}
  Postfix{token: S.Token, value: S.Node, pattern: Bool}
  LambdaStart{quantity: U32}
  LambdaBody{token: S.Token, quantity: U32}
  LambdaStatements{column: U32}
  LambdaBinding{quantity: U32, column: U32}
  LambdaAnnotated{token: S.Token, quantity: U32, column: U32}
  LambdaTail{token: S.Token, quantity: U32, annotation: Maybe<&2,S.Token>, value: S.Node, column: U32}
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

def typed(result: Result<S.Error,F.Read>,
  next: S.Token -> List<&2,S.Token> -> Result<S.Error,Parsed>) -> Result<S.Error,Parsed>:
  match result:
    case Fail{e}: Fail{e}
    case Done{F.Read{token,rest}}: next(token,rest)

def lambda_plain(tokens: List<&2,S.Token>) -> Bool:
  match tokens:
    case Con{name,Con{equal,Con{arrow,tail}}}:
      Bool.and(S.identifier(name),Bool.and(S.matches(equal,"="),S.matches(arrow,">")))
    case _: False{}

def lambda_prefix(+tokens: List<&2,S.Token>) -> Bool:
  match tokens:
    case Con{+head,+tail}:
      S.choose(Bool,S.matches(head,"+"),u => lambda_plain(tail),u => lambda_plain(tokens))
    case _: False{}

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

def wrap_apply(token: S.Token, function: S.Node, value: S.Node,
  rest: List<&2,S.Token>) -> Result<S.Error,Parsed>:
  match value:
    case S.Sequence{items}: Done{Parsed{S.Apply{token,function,items},rest}}
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

def parameter_end(+name: S.Token, +quantity: U32, +typ: S.Token, +rest: List<&2,S.Token>) -> Result<S.Error,Parsed>:
  match rest:
    case Con{h,t}: Done{Parsed{S.Parameter{name,quantity,typ},rest}}
    case Nil{}: invalid(rest,"parameter")

def plain_parameter(tokens: List<&2,S.Token>) -> Bool:
  match tokens:
    case Con{name,Con{colon,tail}}: Bool.and(S.identifier(name),S.matches(colon,":"))
    case _: False{}

def parameter_prefix(+tokens: List<&2,S.Token>) -> Bool:
  match tokens:
    case Con{+head,+tail}:
      S.choose(Bool,Bool.or(S.matches(head,"+"),Bool.or(S.matches(head,"-"),S.matches(head,"~"))),u =>
        plain_parameter(tail),u => plain_parameter(tokens))
    case _: False{}

def parameter_parts(+quantity: U32, +ts: List<&2,S.Token>) -> Result<S.Error,Parsed>:
  match ts:
    case Con{+name,Con{+colon,Con{+typ,+rest}}}:
      S.choose(Result<S.Error,Parsed>,Bool.and(S.identifier(name),Bool.or(S.matches(colon,","),S.matches(colon,"}"))),u =>
        unsupported(ts,"bare-quantity-field"),u =>
      S.choose(Result<S.Error,Parsed>,Bool.and(S.identifier(name),S.matches(colon,":")),u =>
        S.choose(Result<S.Error,Parsed>,Bool.or(S.identifier(typ),S.matches(typ,"(")),u => parameter_end(name,quantity,typ,rest),u =>
          unsupported(Con{typ,rest},"parameter-type")),u => invalid(ts,"parameter")))
    case _: invalid(ts,"parameter")

def parameter(+ts: List<&2,S.Token>) -> Result<S.Error,Parsed>:
  match ts:
    case Con{+h,+t}:
      S.choose(Result<S.Error,Parsed>,S.matches(h,"-"),u => parameter_parts(0,t),u =>
      S.choose(Result<S.Error,Parsed>,S.matches(h,"+"),u => parameter_parts(2,t),u =>
        parameter_parts(1,ts)))
    case _: invalid(ts,"parameter")

def parameter_type(fuel: Nat, value: S.Node, rest: List<&2,S.Token>) -> Result<S.Error,Parsed>:
  match value:
    case S.Parameter{+name,+q,typ}:
      typed(F.read(fuel,F.TypeExpr{},Con{typ,rest},"parameter-type"),token => tail =>
        Done{Parsed{S.Parameter{name,q,token},tail}})
    case _: Fail{S.Internal{"parse","expected-parameter"}}

def result_body(+tokens: List<&2,S.Token>) -> Result<S.Error,List<&2,S.Token>>:
  match tokens:
    case Con{+colon,+body}:
      S.choose(Result<S.Error,List<&2,S.Token>>,S.matches(colon,":"),u => Done{body},u =>
        Fail{S.Invalid{"parse","function-result",S.here(tokens)}})
    case _: Fail{S.Invalid{"parse","function-result",S.here(tokens)}}

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

def compound(node: S.Node) -> Bool:
  match node:
    case S.Match{token,value,arms}: True{}
    case S.Lambda{token,q,body}: compound(body)
    case S.Binding{token,q,annotation,value,body}: compound(body)
    case _: False{}

def reply(+value: S.Node, +ts: List<&2,S.Token>) -> Result<S.Error,Parsed>:
  match value:
    case S.Constructor{token,items}:
      S.choose(Result<S.Error,Parsed>,starts(ts,"="),u =>
        unsupported(ts,"destructuring-binding"),u => body_end(value,ts))
    case S.Lambda{token,q,body}:
      S.choose(Result<S.Error,Parsed>,compound(body),u => Done{Parsed{value,ts}},u => body_end(value,ts))
    case _: body_end(value,ts)

def term_failure(+ts: List<&2,S.Token>) -> Result<S.Error,Parsed>:
  match ts:
    case Con{+h,t}:
      S.choose(Result<S.Error,Parsed>,Bool.or(S.matches(h,")"),Bool.or(S.matches(h,"}"),
        Bool.or(S.matches(h,":"),Bool.or(S.matches(h,","),Bool.or(S.matches(h,"\n"),S.matches(h,"<eof>")))))),u =>
          invalid(ts,"expected-term"),u => unsupported(ts,"term-form"))
    case _: invalid(ts,"unexpected-end")

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
            then(parameter(tokens),p => rest =>
              then(parameter_type(n,p,rest),typed => tail => run(n,ListTail{close,typed,True{},False{}},tail)))))
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
            then(run(n,Bool.pick(Mode,parameters,Parameters{close},Arguments{close,pattern}),t),more => rest => prepend(head,more,rest)),u =>
          S.choose(Result<S.Error,Parsed>,Bool.and(parameters,parameter_prefix(tokens)),u =>
            S.choose(Result<S.Error,Parsed>,S.matches(h,"~"),u => invalid(tokens,"template-order"),u =>
              then(run(n,Parameters{close},tokens),more => rest => prepend(head,more,rest))),u =>
            invalid(tokens,"argument-separator"))))
        case _: invalid(tokens,"unexpected-end")
    case 1n+ +n Term{+pattern}:
      match tokens:
        case Con{+name,Con{+open,+tail}}:
          S.choose(Result<S.Error,Parsed>,Bool.and(Bool.not(pattern),lambda_prefix(tokens)),u =>
            S.choose(Result<S.Error,Parsed>,S.matches(name,"+"),u =>
              run(n,LambdaStart{2},Con{open,tail}),u => run(n,LambdaStart{1},tokens)),u =>
          S.choose(Result<S.Error,Parsed>,Bool.and(pattern,S.matches(name,"+")),u =>
            S.choose(Result<S.Error,Parsed>,S.identifier(open),u => Done{Parsed{S.Promotion{open},tail}},u => invalid(tokens,"pattern-binder")),u =>
          S.choose(Result<S.Error,Parsed>,S.identifier(name),u =>
          S.choose(Result<S.Error,Parsed>,S.matches(open,"("),u =>
            then(run(n,Arguments{")",pattern},tail),args => rest =>
              then(wrap_call(name,False{},args,rest),value => end => run(n,Postfix{name,value,pattern},end))),u =>
          S.choose(Result<S.Error,Parsed>,S.matches(open,"{"),u =>
            then(run(n,Arguments{"}",pattern},tail),args => rest =>
              then(wrap_call(name,True{},args,rest),value => end => run(n,Postfix{name,value,pattern},end))),u =>
            Done{Parsed{S.Variable{name},Con{open,tail}}})),u =>
            term_failure(tokens))))
        case _: invalid(tokens,"term")
    case 1n+ +n Postfix{+token,+value,+pattern}:
      match tokens:
        case Con{+open,+tail}:
          S.choose(Result<S.Error,Parsed>,Bool.and(Bool.not(pattern),S.matches(open,"(")),u =>
            then(run(n,Arguments{")",False{}},tail),args => rest =>
              then(wrap_apply(token,value,args,rest),applied => end => run(n,Postfix{token,applied,False{}},end))),u =>
            Done{Parsed{value,tokens}})
        case _: Done{Parsed{value,tokens}}
    case 1n+ +n LambdaStart{+quantity}:
      match tokens:
        case Con{token,Con{equal,Con{arrow,tail}}}: run(n,LambdaBody{token,quantity},tail)
        case _: invalid(tokens,"lambda-binder")
    case 1n+ +n LambdaBody{+token,+quantity}:
      match tokens:
        case Con{+head,+tail}:
          S.choose(Result<S.Error,Parsed>,S.matches(head,"\n"),u =>
            then(run(n,LambdaStatements{0},S.skip_lines(tail)),body => rest => Done{Parsed{S.Lambda{token,quantity,body},rest}}),u =>
          S.choose(Result<S.Error,Parsed>,S.matches(head,"match"),u =>
            then(run(n,Term{False{}},tail),value => rest =>
              then(run(n,MatchTail{head,value,S.column(token)},rest),body => end => Done{Parsed{S.Lambda{token,quantity,body},end}})),u =>
            then(run(n,LambdaStatements{0},tokens),body => rest => Done{Parsed{S.Lambda{token,quantity,body},rest}})))
        case _: invalid(tokens,"lambda-body")
    case 1n+ +n LambdaStatements{+column}:
      match tokens:
        case Con{+head,Con{+second,+tail}}:
          S.choose(Result<S.Error,Parsed>,Bool.or(U32.is_eq(column,0),U32.is_eq(S.column(head),column)),u =>
          S.choose(Result<S.Error,Parsed>,lambda_prefix(tokens),u => run(n,Term{False{}},tokens),u =>
          S.choose(Result<S.Error,Parsed>,S.matches(head,"match"),u => run(n,BodyAt{S.column(head)},tokens),u =>
          S.choose(Result<S.Error,Parsed>,Bool.or(S.matches(head,"+"),S.matches(head,"-")),u =>
            run(n,LambdaBinding{Bool.pick(U32,S.matches(head,"+"),2,0),S.column(head)},Con{second,tail}),u =>
          S.choose(Result<S.Error,Parsed>,Bool.or(S.matches(second,"="),S.matches(second,":")),u =>
            run(n,LambdaBinding{1,S.column(head)},tokens),u => run(n,Term{False{}},tokens))))),u =>
            invalid(tokens,"body-indentation"))
        case _: invalid(tokens,"lambda-body")
    case 1n+ +n LambdaBinding{+quantity,+column}:
      match tokens:
        case Con{+name,Con{+separator,+tail}}:
          S.choose(Result<S.Error,Parsed>,S.identifier(name),u =>
          S.choose(Result<S.Error,Parsed>,S.matches(separator,":"),u =>
            run(n,LambdaAnnotated{name,quantity,column},tail),u =>
            S.bind(List<&2,S.Token>,Parsed,expect(Con{separator,tail},"="),rhs =>
              then(run(n,Term{False{}},rhs),value => rest => run(n,LambdaTail{name,quantity,None{},value,column},rest)))),u =>
            invalid(tokens,"binding-name"))
        case _: invalid(tokens,"binding")
    case 1n+ +n LambdaAnnotated{+name,+quantity,+column}:
      typed(F.read(n,F.TypeExpr{},tokens,"binding-type"),+typ => rest =>
        S.bind(List<&2,S.Token>,Parsed,expect(rest,"="),rhs =>
          then(run(n,Term{False{}},rhs),value => end => run(n,LambdaTail{name,quantity,Some{typ},value,column},end))))
    case 1n+ +n LambdaTail{+token,+quantity,+annotation,+value,+column}:
      S.bind(List<&2,S.Token>,Parsed,expect(tokens,"\n"),body =>
        then(run(n,LambdaStatements{column},S.skip_lines(body)),next => rest =>
          Done{Parsed{S.Binding{token,quantity,annotation,value,next},rest}}))
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
            then(run(n,Term{False{}},Con{second,tail}),value => rest => run(n,MatchTail{h,value,S.column(h)},rest)),u =>
          S.choose(Result<S.Error,Parsed>,lambda_prefix(tokens),u =>
            then(run(n,Term{False{}},tokens),value => rest => reply(value,rest)),u =>
          S.choose(Result<S.Error,Parsed>,Bool.or(S.matches(h,"+"),S.matches(h,"-")),u =>
            run(n,BindingStart{Bool.pick(U32,S.matches(h,"+"),2,0),S.column(h)},Con{second,tail}),u =>
          S.choose(Result<S.Error,Parsed>,Bool.or(S.matches(second,"="),S.matches(second,":")),u =>
            run(n,BindingStart{1,S.column(h)},tokens),u =>
            then(run(n,Term{False{}},tokens),value => rest => reply(value,rest)))))),u =>
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
        case Con{+dash,Con{+arrow,+tail}}:
          S.choose(Result<S.Error,Parsed>,Bool.and(S.matches(dash,"-"),S.matches(arrow,">")),u =>
            typed(F.read(n,F.TypeExpr{},tail,"function-result"),+typ => rest =>
              S.bind(List<&2,S.Token>,Parsed,result_body(rest),body =>
                then(run(n,Body{0},body),value => end => wrap_function(name,S.Sequence{params},typ,value,end)))),u =>
            invalid(tokens,"function-result"))
        case _: invalid(tokens,"function-result")
    case 1n+ +n FunctionTail{token,other}:
      Fail{S.Internal{"parse","declaration-mode"}}
    case 1n+ +n MatchTail{+token,+value,+column}:
      S.choose(Result<S.Error,Parsed>,scrutinee(tokens),u =>
        unsupported(tokens,"match-scrutinees"),u =>
      S.bind(List<&2,S.Token>,Parsed,expect(tokens,":"),arms =>
        then(run(n,Arms{column,0},S.skip_lines(arms)),items => rest => wrap_match(token,value,items,rest))))
    case 1n+ +n BindingStart{+quantity,+column}:
      match tokens:
        case Con{+name,Con{+separator,+tail}}:
          S.choose(Result<S.Error,Parsed>,S.identifier(name),u =>
          S.choose(Result<S.Error,Parsed>,S.matches(separator,":"),u =>
            run(n,AnnotatedBinding{name,quantity,column},tail),u =>
            S.bind(List<&2,S.Token>,Parsed,expect(Con{separator,tail},"="),rhs =>
              then(run(n,Term{False{}},rhs),value => rest => run(n,BindingTail{name,quantity,None{},value,column},rest)))),u =>
            invalid(tokens,"binding-name"))
        case _: invalid(tokens,"binding")
    case 1n+ +n AnnotatedBinding{+name,+quantity,+column}:
      typed(F.read(n,F.TypeExpr{},tokens,"binding-type"),+typ => rest =>
        S.bind(List<&2,S.Token>,Parsed,expect(rest,"="),rhs =>
          then(run(n,Term{False{}},rhs),value => end => run(n,BindingTail{name,quantity,Some{typ},value,column},end))))
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
            then(run(n,Term{True{}},tail),pattern => rest =>
              S.bind(List<&2,S.Token>,Parsed,expect(rest,":"),body =>
                then(run(n,Body{S.column(keyword)},body),value => after =>
                  then(run(n,Arms{parent,S.column(keyword)},S.skip_lines(after)),more => end =>
                    prepend(S.Arm{keyword,pattern,value},more,end))))),u =>
            unsupported(tokens,"pattern-or-indentation")))
        case _: invalid(tokens,"unexpected-end")

def parse(+depth: Nat, tokens: List<&2,S.Token>) -> Result<S.Error,Parsed>:
  then(run(depth,Book{},tokens),+root => +rest =>
    S.bind(Unit,Parsed,V.book(depth,root),u => Done{Parsed{root,rest}}))

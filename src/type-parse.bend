import Base
import ./syntax.bend as S

type Parsed is Data:
  Parsed{value: S.Node, rest: List<&2,S.Token>}

type Mode is Data:
  Expression{quantity: U32}
  Tail{value: S.Node}
  Items{}
  ItemTail{head: S.Node}

def starts(ts: List<&2,S.Token>, word: String) -> Bool:
  match ts:
    case Nil{}: False{}
    case Con{h,t}: S.matches(h,word)

def meet_prefix(ts: List<&2,S.Token>) -> Bool:
  match ts:
    case Con{a,Con{b,Con{c,t}}}:
      Bool.and(S.matches(a,"<"),Bool.and(S.matches(b,"&"),S.matches(c,">")))
    case _: False{}

def application_prefix(tokens: List<&2,S.Token>) -> Bool:
  match tokens:
    case Con{name,+tail}:
      Bool.and(S.identifier(name),Bool.and(starts(tail,"<"),Bool.not(meet_prefix(tail))))
    case _: False{}

def unsupported_suffix(+tokens: List<&2,S.Token>) -> Bool:
  Bool.or(starts(tokens,"&"),Bool.or(starts(tokens,"|"),Bool.or(starts(tokens,"("),
    Bool.or(starts(tokens,"-"),starts(tokens,"[")))))

def invalid(ts: List<&2,S.Token>, code: String) -> Result<S.Error,Parsed>:
  Fail{S.Invalid{"parse",code,S.here(ts)}}

# The seed lexes `&2`, `<&>` and a list's closing `>` as glued tokens; Knot
# lexes symbols apart and drops spaces. A gap inside one is Unsupported.
def glued(+a: S.Token, +b: S.Token) -> Bool:
  match a b:
    case S.Token{x,S.At{p,q,l,c}} S.Token{y,S.At{r,s,m,d}}: U32.is_eq(q,r)

def spaced(ts: List<&2,S.Token>) -> Result<S.Error,Parsed>:
  Fail{S.Unsupported{"parse","spacing",S.here(ts)}}

# Only the token just before `mark` can end where it begins.
def flush(+ts: List<&2,S.Token>, +mark: S.Token) -> Bool:
  match ts:
    case Nil{}: False{}
    case Con{+h,+t}: S.choose(Bool,glued(h,mark),u => True{},u => flush(t,mark))

# `rest` closes, after a gap, the list whose item began at `from`.
def apart(+from: List<&2,S.Token>, +rest: List<&2,S.Token>) -> Bool:
  match rest:
    case Con{+h,+t}: S.choose(Bool,S.matches(h,">"),u => Bool.not(flush(from,h)),u => False{})
    case Nil{}: False{}

def finish(+value: S.Node, +tokens: List<&2,S.Token>) -> Result<S.Error,Parsed>:
  S.choose(Result<S.Error,Parsed>,unsupported_suffix(tokens),u =>
    Fail{S.Unsupported{"parse","type-expression",S.here(tokens)}},u => Done{Parsed{value,tokens}})

def then(result: Result<S.Error,Parsed>,
  next: S.Node -> List<&2,S.Token> -> Result<S.Error,Parsed>) -> Result<S.Error,Parsed>:
  match result:
    case Fail{e}: Fail{e}
    case Done{Parsed{value,rest}}: next(value,rest)

def expect(+ts: List<&2,S.Token>, +word: String) -> Result<S.Error,List<&2,S.Token>>:
  match ts:
    case Nil{}: Fail{S.Invalid{"parse","unexpected-end",S.here(ts)}}
    case Con{+h,+t}:
      S.choose(Result<S.Error,List<&2,S.Token>>,S.matches(h,word),u => Done{t},u =>
        Fail{S.Invalid{"parse",String.append("expected-",word),S.at(h)}})

def prepend(head: S.Node, tail: S.Node, rest: List<&2,S.Token>) -> Result<S.Error,Parsed>:
  match tail:
    case S.Sequence{items}: Done{Parsed{S.Sequence{Con{head,items}},rest}}
    case _: Fail{S.Internal{"parse","expected-type-arguments"}}

def apply(token: S.Token, quantity: U32, arguments: S.Node, rest: List<&2,S.Token>) -> Result<S.Error,Parsed>:
  match arguments:
    case S.Sequence{Nil{}}: Fail{S.Invalid{"parse","type-arguments",S.at(token)}}
    case S.Sequence{items}: Done{Parsed{S.TypeApply{token,items,quantity},rest}}
    case _: Fail{S.Internal{"parse","expected-type-arguments"}}

def literal(+token: S.Token, +value: S.Token, +rest: List<&2,S.Token>) -> Result<S.Error,Parsed>:
  S.choose(Result<S.Error,Parsed>,S.matches(value,"0"),u => Done{Parsed{S.Quantity{token,0},rest}},u =>
  S.choose(Result<S.Error,Parsed>,S.matches(value,"1"),u => Done{Parsed{S.Quantity{token,1},rest}},u =>
  S.choose(Result<S.Error,Parsed>,S.matches(value,"2"),u => Done{Parsed{S.Quantity{token,2},rest}},u =>
    invalid(Con{value,rest},"quantity-literal"))))

def read_quantity(+token: S.Token, +tokens: List<&2,S.Token>) -> Result<S.Error,Parsed>:
  match tokens:
    case Con{+value,+rest}:
      S.choose(Result<S.Error,Parsed>,glued(token,value),u => literal(token,value,rest),u => spaced(tokens))
    case Nil{}: invalid(tokens,"quantity-literal")

# Type arguments and Kind expressions share the same bounded tree grammar.
# An argument not followed by `,` or `>` is a term, as in `Tag<On{}>`:
# value-indexed families are Unsupported, so no separator error remains.
def run(fuel: Nat, mode: Mode, +tokens: List<&2,S.Token>) -> Result<S.Error,Parsed>:
  match fuel mode:
    case 0n _: Fail{S.Exhausted{"parse",S.here(tokens)}}
    case 1n+ +n Expression{+quantity}:
      match tokens:
        case Con{+h,+t}:
          S.choose(Result<S.Error,Parsed>,Bool.and(U32.is_eq(quantity,2),
            Bool.not(Bool.or(S.matches(h,"+"),application_prefix(tokens)))),u =>
              Fail{S.Unsupported{"parse","type-prefix",S.at(h)}},u =>
          S.choose(Result<S.Error,Parsed>,S.matches(h,"+"),u => run(n,Expression{2},t),u =>
          S.choose(Result<S.Error,Parsed>,S.matches(h,"&"),u =>
            then(read_quantity(h,t),value => rest => run(n,Tail{value},rest)),u =>
          S.choose(Result<S.Error,Parsed>,Bool.or(S.matches(h,"Type"),S.matches(h,"Data")),u =>
            run(n,Tail{S.TypeKind{h,S.Quantity{h,Bool.pick(U32,S.matches(h,"Data"),2,1)}}},t),u =>
          S.choose(Result<S.Error,Parsed>,S.matches(h,"Quant"),u =>
            run(n,Tail{S.QuantType{h}},t),u =>
          S.choose(Result<S.Error,Parsed>,S.matches(h,"Kind"),u =>
            S.bind(List<&2,S.Token>,Parsed,expect(t,"("),body =>
              then(run(n,Expression{1},body),q => rest =>
                S.bind(List<&2,S.Token>,Parsed,expect(rest,")"),end =>
                  run(n,Tail{S.TypeKind{h,q}},end)))),u =>
          S.choose(Result<S.Error,Parsed>,S.identifier(h),u =>
          S.choose(Result<S.Error,Parsed>,Bool.and(starts(t,"<"),Bool.not(meet_prefix(t))),u =>
            S.bind(List<&2,S.Token>,Parsed,expect(t,"<"),body =>
              then(run(n,Items{},body),args => rest =>
                then(apply(h,quantity,args,rest),value => end => run(n,Tail{value},end)))),u =>
            run(n,Tail{S.Variable{h}},t)),u =>
          S.choose(Result<S.Error,Parsed>,S.matches(h,"~"),u =>
            invalid(tokens,"type-expression"),u =>
            Fail{S.Unsupported{"parse","type-expression",S.at(h)}}))))))))
        case _: invalid(tokens,"type-expression")
    case 1n+ +n Tail{+value}:
      match tokens:
        case Con{+a,Con{+b,Con{+c,+t}}}:
          S.choose(Result<S.Error,Parsed>,meet_prefix(tokens),u =>
            S.choose(Result<S.Error,Parsed>,Bool.and(glued(a,b),glued(b,c)),u =>
              then(run(n,Expression{1},t),right => rest => Done{Parsed{S.Meet{a,value,right},rest}}),u =>
              spaced(tokens)),u =>
            finish(value,tokens))
        case _: finish(value,tokens)
    case 1n+ +n Items{}:
      match tokens:
        case Con{+h,+t}:
          S.choose(Result<S.Error,Parsed>,S.matches(h,">"),u => Done{Parsed{S.Sequence{Nil{}},t}},u =>
            then(run(n,Expression{1},tokens),arg => +rest =>
              S.choose(Result<S.Error,Parsed>,apart(tokens,rest),u => spaced(rest),u => run(n,ItemTail{arg},rest))))
        case _: invalid(tokens,"type-arguments")
    case 1n+ +n ItemTail{+head}:
      match tokens:
        case Con{+h,+t}:
          S.choose(Result<S.Error,Parsed>,S.matches(h,">"),u => Done{Parsed{S.Sequence{Con{head,Nil{}}},t}},u =>
          S.choose(Result<S.Error,Parsed>,S.matches(h,","),u =>
            then(run(n,Items{},t),tail => rest => prepend(head,tail,rest)),u =>
            Fail{S.Unsupported{"parse","term-argument",S.at(h)}}))
        case _: invalid(tokens,"type-arguments")

def expression(fuel: Nat, tokens: List<&2,S.Token>) -> Result<S.Error,Parsed>:
  run(fuel,Expression{1},tokens)

def parameter_node(+bare: Bool, +name: S.Token, +quantity: U32, +typ: S.Node,
  +rest: List<&2,S.Token>) -> Result<S.Error,Parsed>:
  match bare typ:
    case False{} S.TypeKind{token,q}: Fail{S.Unsupported{"parse","parameter-type",S.at(token)}}
    case False{} S.QuantType{token}: Fail{S.Unsupported{"parse","parameter-type",S.at(token)}}
    case _ _:
      S.choose(Result<S.Error,Parsed>,unsupported_suffix(rest),u =>
        Fail{S.Unsupported{"parse","parameter-type",S.here(rest)}},u =>
        Done{Parsed{S.TypedParameter{name,quantity,typ},rest}})

# Only an unmarked bare binder is a quantity parameter. A marked one, `+a,`,
# is a parameter missing its type, rejected where the seed expects `:`.
def parameter_parts(+fuel: Nat, +bare: Bool, +quantity: U32,
  +tokens: List<&2,S.Token>) -> Result<S.Error,Parsed>:
  match tokens:
    case Con{+name,Con{+colon,+rest}}:
      S.choose(Result<S.Error,Parsed>,S.identifier(name),u =>
      S.choose(Result<S.Error,Parsed>,S.matches(colon,":"),u =>
        then(expression(fuel,rest),typ => +end =>
          S.choose(Result<S.Error,Parsed>,apart(rest,end),u => spaced(end),u => parameter_node(bare,name,quantity,typ,end))),u =>
      S.choose(Result<S.Error,Parsed>,Bool.and(bare,Bool.or(S.matches(colon,","),Bool.or(S.matches(colon,")"),S.matches(colon,">")))),u =>
        S.choose(Result<S.Error,Parsed>,U32.is_eq(quantity,1),u =>
          Done{Parsed{S.TypedParameter{name,0,S.QuantType{name}},Con{colon,rest}}},u =>
          invalid(Con{colon,rest},"parameter")),u =>
        Fail{S.Unsupported{"parse","bare-quantity-field",S.at(name)}})),u => invalid(tokens,"parameter"))
    case _: invalid(tokens,"parameter")

def parameter(+fuel: Nat, +bare: Bool, +tokens: List<&2,S.Token>) -> Result<S.Error,Parsed>:
  match tokens:
    case Con{+h,+t}:
      S.choose(Result<S.Error,Parsed>,S.matches(h,"-"),u => parameter_parts(fuel,bare,0,t),u =>
      S.choose(Result<S.Error,Parsed>,S.matches(h,"+"),u => parameter_parts(fuel,bare,2,t),u =>
        parameter_parts(fuel,bare,1,tokens)))
    case _: invalid(tokens,"parameter")

def simple_parts(tokens: List<&2,S.Token>) -> Bool:
  match tokens:
    case Con{name,Con{colon,Con{typ,rest}}}:
      Bool.and(S.matches(colon,":"),Bool.and(S.identifier(typ),Bool.not(starts(rest,"<"))))
    case _: False{}

def simple(+tokens: List<&2,S.Token>) -> Bool:
  match tokens:
    case Con{+h,+t}:
      S.choose(Bool,Bool.or(S.matches(h,"-"),S.matches(h,"+")),u => simple_parts(t),u => simple_parts(tokens))
    case _: False{}

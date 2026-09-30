import Base
import ./syntax.bend as S
import ./core.bend as C

type Read is Data:
  Read{token: S.Token, rest: List<&2,S.Token>}
type Mode is Data:
  TypeExpr{}
  TypeGroupedExpr{}
  TypeAtom{}
  TypeTail{domain: S.Token, grouped: Bool}
  TypeGroup{token: S.Token}
  TypeFamily{open: S.Token, depth: U32, parens: U32, grouped: Bool}
type Interned is Data:
  Interned{types: List<&2,C.Datatype>, index: U32}

def then(result: Result<S.Error,Read>, next: S.Token -> List<&2,S.Token> -> Result<S.Error,Read>) -> Result<S.Error,Read>:
  match result:
    case Fail{e}: Fail{e}
    case Done{Read{token,rest}}: next(token,rest)

def unsupported(-A: Type, tokens: List<&2,S.Token>, code: String) -> Result<S.Error,A>:
  Fail{S.Unsupported{"parse",code,S.here(tokens)}}

# Arrows associate right; grouping changes only the type tree.
def read(fuel: Nat, mode: Mode, +tokens: List<&2,S.Token>, +code: String) -> Result<S.Error,Read>:
  match fuel mode:
    case 0n _: Fail{S.Exhausted{"parse",S.here(tokens)}}
    case 1n+ +n TypeExpr{}:
      then(read(n,TypeAtom{},tokens,code),domain => rest => read(n,TypeTail{domain,False{}},rest,code))
    case 1n+ +n TypeGroupedExpr{}:
      then(read(n,TypeAtom{},tokens,code),domain => rest => read(n,TypeTail{domain,True{}},rest,code))
    case 1n+ +n TypeAtom{}:
      match tokens:
        case Con{+head,+tail}:
          S.choose(Result<S.Error,Read>,S.identifier(head),u => Done{Read{head,tail}},u =>
          S.choose(Result<S.Error,Read>,S.matches(head,"("),u =>
            then(read(n,TypeGroupedExpr{},tail,code),token => rest => read(n,TypeGroup{token},rest,code)),u =>
            unsupported(Read,tokens,code)))
        case Nil{}: Fail{S.Invalid{"parse",code,S.here(tokens)}}
    case 1n+ +n TypeGroup{+token}:
      match tokens:
        case Con{+head,+tail}:
          S.choose(Result<S.Error,Read>,S.matches(head,")"),u => Done{Read{token,tail}},u =>
            unsupported(Read,tokens,code))
        case Nil{}: Fail{S.Invalid{"parse",code,S.here(tokens)}}
    case 1n+ +n TypeTail{+domain,+grouped}:
      match tokens:
        case Con{+dash,Con{+arrow,+tail}}:
          S.choose(Result<S.Error,Read>,S.matches(dash,"-"),u =>
            S.choose(Result<S.Error,Read>,S.matches(arrow,">"),u =>
              S.choose(Result<S.Error,Read>,S.adjacent(dash,arrow),u =>
                then(read(n,Bool.pick(Mode,grouped,TypeGroupedExpr{},TypeExpr{}),tail,code),result => rest => Done{Read{S.Arrow{domain,result},rest}}),u =>
                Fail{S.Invalid{"parse","split-arrow",S.at(dash)}}),u =>
              Done{Read{domain,tokens}}),u =>
          S.choose(Result<S.Error,Read>,S.matches(dash,"<"),u =>
            S.choose(Result<S.Error,Read>,S.matches(arrow,"-"),u =>
              Fail{S.Invalid{"parse",code,S.at(dash)}},u =>
              read(n,TypeFamily{dash,1,0,grouped},Con{arrow,tail},code)),u =>
          S.choose(Result<S.Error,Read>,S.matches(dash,"("),u =>
            unsupported(Read,tokens,code),u => Done{Read{domain,tokens}})))
        case _: Done{Read{domain,tokens}}
    # A family application is outside this profile. Locate its closing bracket
    # before refusing it: an unclosed '<' is the seed's untyped comparison.
    case 1n+ +n TypeFamily{+open,+depth,+parens,+grouped}:
      match tokens:
        case Con{+head,Con{+next,+tail}}:
          S.choose(Result<S.Error,Read>,S.matches(head,"<eof>"),u =>
            Fail{S.Invalid{"parse",code,S.at(open)}},u =>
          S.choose(Result<S.Error,Read>,Bool.and(S.matches(head,"-"),S.matches(next,">")),u =>
            read(n,TypeFamily{open,depth,parens,grouped},tail,code),u =>
          S.choose(Result<S.Error,Read>,Bool.and(grouped,Bool.and(U32.is_eq(parens,0),S.matches(head,":"))),u =>
            unsupported(Read,[open],code),u =>
          S.choose(Result<S.Error,Read>,S.matches(head,"("),u =>
            read(n,TypeFamily{open,depth,U32.add(parens,1),grouped},Con{next,tail},code),u =>
          S.choose(Result<S.Error,Read>,S.matches(head,")"),u =>
            S.choose(Result<S.Error,Read>,U32.is_gt(parens,0),u =>
              read(n,TypeFamily{open,depth,U32.sub(parens,1),grouped},Con{next,tail},code),u =>
              Fail{S.Invalid{"parse",code,S.at(open)}}),u =>
          S.choose(Result<S.Error,Read>,S.matches(head,"<"),u =>
            read(n,TypeFamily{open,U32.add(depth,1),parens,grouped},Con{next,tail},code),u =>
          S.choose(Result<S.Error,Read>,S.matches(head,">"),u =>
            S.choose(Result<S.Error,Read>,U32.is_eq(depth,1),u =>
              unsupported(Read,[open],code),u => read(n,TypeFamily{open,U32.sub(depth,1),parens,grouped},Con{next,tail},code)),u =>
            read(n,TypeFamily{open,depth,parens,grouped},Con{next,tail},code))))))))
        case _: Fail{S.Invalid{"parse",code,S.at(open)}}

def token(definition: C.Datatype) -> S.Token:
  match definition:
    case C.Datatype{name,data,ctors}: name
    case C.Arrow{name,domain,result}: name

def reusable(definition: C.Datatype) -> Bool:
  match definition:
    case C.Datatype{name,data,ctors}: data
    case C.Arrow{name,domain,result}: False{}

def find(types: List<&2,C.Datatype>, +name: S.Token, +index: U32) -> Maybe<&2,U32>:
  match types:
    case Nil{}: None{}
    case Con{C.Datatype{token,data,ctors},+tail}:
      S.choose(Maybe<&2,U32>,String.eq(S.text(token),S.text(name)),u => Some{index},u => find(tail,name,U32.add(index,1)))
    case Con{C.Arrow{token,domain,result},tail}: find(tail,name,U32.add(index,1))

# An arrow's key is its resolved pair, never its recursively printed spelling.
def find_arrow(types: List<&2,C.Datatype>, +domain: U32, +result: U32, +index: U32) -> Maybe<&2,U32>:
  match types:
    case Nil{}: None{}
    case Con{C.Arrow{name,input,output},+tail}:
      S.choose(Maybe<&2,U32>,Bool.and(U32.is_eq(input,domain),U32.is_eq(output,result)),u => Some{index},u => find_arrow(tail,domain,result,U32.add(index,1)))
    case Con{head,tail}: find_arrow(tail,domain,result,U32.add(index,1))

def known(value: Maybe<&2,U32>, name: S.Token) -> Result<S.Error,U32>:
  match value:
    case None{}: C.invalid(U32,"unknown-type",name)
    case Some{index}: Done{index}

def lookup(fuel: Nat, +name: S.Token, +types: List<&2,C.Datatype>) -> Result<S.Error,U32>:
  match fuel name:
    case 0n _: C.exhausted(U32,name)
    case 1n+ n S.Token{text,at}: known(find(types,name,0),name)
    case 1n+ +n S.Arrow{domain,+result}:
      S.bind(U32,U32,lookup(n,domain,types),domain_id =>
        S.bind(U32,U32,lookup(n,result,types),result_id => known(find_arrow(types,domain_id,result_id,0),name)))

def found(value: Maybe<&2,U32>, +types: List<&2,C.Datatype>, name: S.Token) -> Result<S.Error,Interned>:
  match value:
    case None{}: C.invalid(Interned,"unknown-type",name)
    case Some{index}: Done{Interned{types,index}}

def append(value: Maybe<&2,U32>, +types: List<&2,C.Datatype>, +name: S.Token, +domain: U32, +result: U32) -> Result<S.Error,Interned>:
  match value:
    case Some{index}: Done{Interned{types,index}}
    case None{}:
      +index = U32.from_nat(List.length(&2,C.Datatype,types))
      S.choose(Result<S.Error,Interned>,U32.is_ge(index,4096),u => C.exhausted(Interned,name),u =>
        Done{Interned{List.append(&2,C.Datatype,types,[C.Arrow{name,domain,result}]),index}})

def then_intern(result: Result<S.Error,Interned>, next: List<&2,C.Datatype> -> U32 -> Result<S.Error,Interned>) -> Result<S.Error,Interned>:
  match result:
    case Fail{e}: Fail{e}
    case Done{Interned{types,index}}: next(types,index)

def with_types(-A: Data, result: Result<S.Error,Interned>, next: List<&2,C.Datatype> -> Result<S.Error,A>) -> Result<S.Error,A>:
  match result:
    case Fail{e}: Fail{e}
    case Done{Interned{types,index}}: next(types)

def intern(fuel: Nat, +name: S.Token, +types: List<&2,C.Datatype>) -> Result<S.Error,Interned>:
  match fuel name:
    case 0n _: C.exhausted(Interned,name)
    case 1n+ n S.Token{text,at}: found(find(types,name,0),types,name)
    case 1n+ +n S.Arrow{domain,+result}:
      then_intern(intern(n,domain,types),with_domain => +domain_id =>
        then_intern(intern(n,result,with_domain),+with_result => +result_id =>
          append(find_arrow(with_result,domain_id,result_id,0),with_result,name,domain_id,result_id)))

def intern_all(names: List<&2,S.Token>, +types: List<&2,C.Datatype>) -> Result<S.Error,List<&2,C.Datatype>>:
  match names:
    case Nil{}: Done{types}
    case Con{head,+tail}:
      with_types(List<&2,C.Datatype>,intern(4096n,head,types),next => intern_all(tail,next))

def signature(parameters: List<&2,S.Node>, +result: S.Token) -> S.Token:
  match parameters:
    case Nil{}: result
    case Con{S.Parameter{name,q,domain},tail}: S.Arrow{domain,signature(tail,result)}
    case _: result

def annotation(value: Maybe<&2,S.Token>) -> List<&2,S.Token>:
  match value:
    case None{}: Nil{}
    case Some{token}: [token]

# Explicit type occurrences precede synthetic signature suffixes, so declared
# datatype IDs and the first explicit arrow ID do not depend on function count.
def occurrences(fuel: Nat, node: S.Node, +signatures: Bool) -> Result<S.Error,List<&2,S.Token>>:
  match fuel node:
    case 0n _: C.exhausted(List<&2,S.Token>,S.Token{"",S.At{0,0,0,0}})
    case 1n+ n S.Variable{token}: Done{Nil{}}
    case 1n+ n S.Promotion{token}: Done{Nil{}}
    case 1n+ n S.Parameter{token,q,type_name}: Done{Bool.pick(List<&2,S.Token>,signatures,Nil{},[type_name])}
    case 1n+ +n S.Constructor{token,args}: occurrences(n,S.Sequence{args},signatures)
    case 1n+ +n S.Call{token,args}: occurrences(n,S.Sequence{args},signatures)
    case 1n+ +n S.Apply{token,function,args}: occurrences(n,S.Sequence{Con{function,args}},signatures)
    case 1n+ +n S.Lambda{token,q,body}: occurrences(n,body,signatures)
    case 1n+ +n S.Binding{token,q,+annot,value,body}:
      S.bind(List<&2,S.Token>,List<&2,S.Token>,occurrences(n,S.Sequence{[value,body]},signatures),tail =>
        Done{List.append(&2,S.Token,Bool.pick(List<&2,S.Token>,signatures,Nil{},annotation(annot)),tail)})
    case 1n+ +n S.Match{token,value,arms}: occurrences(n,S.Sequence{Con{value,arms}},signatures)
    case 1n+ +n S.Arm{token,pattern,body}: occurrences(n,body,signatures)
    case 1n+ +n S.Datatype{token,data,ctors}: occurrences(n,S.Sequence{ctors},signatures)
    case 1n+ +n S.Function{token,+params,+result,+body}:
      S.choose(Result<S.Error,List<&2,S.Token>>,signatures,u => Done{[signature(params,result)]},u =>
        S.bind(List<&2,S.Token>,List<&2,S.Token>,occurrences(n,S.Sequence{List.append(&2,S.Node,params,[body])},False{}),tail => Done{Con{result,tail}}))
    case 1n+ n S.Sequence{Nil{}}: Done{Nil{}}
    case 1n+ +n S.Sequence{Con{head,+tail}}:
      S.bind(List<&2,S.Token>,List<&2,S.Token>,occurrences(n,head,signatures),+names =>
        S.bind(List<&2,S.Token>,List<&2,S.Token>,occurrences(n,S.Sequence{tail},signatures),rest =>
          Done{List.append(&2,S.Token,names,rest)}))

def complete(+root: S.Node, +headers: List<&2,C.Datatype>) -> Result<S.Error,List<&2,C.Datatype>>:
  S.bind(List<&2,S.Token>,List<&2,C.Datatype>,occurrences(4096n,root,False{}),names =>
    S.bind(List<&2,C.Datatype>,List<&2,C.Datatype>,intern_all(names,headers),+types =>
      S.bind(List<&2,S.Token>,List<&2,C.Datatype>,occurrences(4096n,root,True{}),suffixes => intern_all(suffixes,types))))

def arrows(types: List<&2,C.Datatype>) -> List<&2,C.Datatype>:
  match types:
    case Nil{}: Nil{}
    case Con{C.Datatype{name,data,ctors},tail}: arrows(tail)
    case Con{C.Arrow{name,domain,result},tail}: Con{C.Arrow{name,domain,result},arrows(tail)}

def arrow(types: List<&2,C.Datatype>, +domain: U32, +result: U32, +index: U32) -> Result<S.Error,U32>:
  match types:
    case Nil{}: C.internal(U32,"function-type")
    case Con{C.Datatype{name,data,ctors},tail}: arrow(tail,domain,result,U32.add(index,1))
    case Con{C.Arrow{name,+input,+output},+tail}:
      S.choose(Result<S.Error,U32>,Bool.and(U32.is_eq(input,domain),U32.is_eq(output,result)),u => Done{index},u =>
        arrow(tail,domain,result,U32.add(index,1)))

def arrow_id(types: List<&2,C.Datatype>, domain: U32, result: U32) -> Result<S.Error,U32>:
  arrow(types,domain,result,0)

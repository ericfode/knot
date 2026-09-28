import Base
import ./syntax.bend as S
import ./core.bend as C
import ./opt-term.bend as T
import ./opt-fold.bend as F
import ./opt-inline.bend as I
import ./opt-check.bend as K

type Visit is Data:
  Expression{term: C.Term}
  Arguments{terms: List<&2,C.Term>, parameters: List<&2,C.Parameter>}

type Pass is Data:
  Inline{}
  Fold{}
  Dead{}

def is_inline(pass: Pass) -> Bool:
  match pass:
    case Inline{}: True{}
    case _: False{}

def is_fold(pass: Pass) -> Bool:
  match pass:
    case Fold{}: True{}
    case _: False{}

def is_dead(pass: Pass) -> Bool:
  match pass:
    case Dead{}: True{}
    case _: False{}

def or_original(option: Maybe<&2,C.Term>, original: C.Term) -> C.Term:
  match option:
    case None{}: original
    case Some{term}: term

def rewrite(option: Maybe<&2,C.Term>, original: C.Term, next: C.Term -> Result<S.Error,C.Term>) -> Result<S.Error,C.Term>:
  match option:
    case None{}: Done{original}
    case Some{term}: next(term)

def parameters(function: Maybe<&2,C.Function>, next: List<&2,C.Parameter> -> Result<S.Error,C.Term>) -> Result<S.Error,C.Term>:
  match function:
    case Some{C.Function{C.Signature{token,params,typ},body}}: next(params)
    case None{}: T.internal(C.Term,"function-index")

def known_case(known: Maybe<&2,C.Term>, +arms: List<&2,C.Term>, original: C.Term, next: C.Term -> Result<S.Error,C.Term>) -> Result<S.Error,C.Term>:
  match known:
    case None{}: next(original)
    case Some{value}:
      S.bind(Maybe<&2,C.Term>,C.Term,F.constant(value,arms),option => next(or_original(option,original)))

def keep_let(pass: Pass, depth: Nat, token: S.Token, level: U32, q: U32, typ: U32, value: C.Term, body: C.Term) -> Result<S.Error,C.Term>:
  match pass:
    case Dead{}: F.dead(depth,token,level,q,typ,value,body)
    case _: Done{C.Let{token,level,q,typ,value,body}}

# Each traversal changes one mechanism. No pass changes types, signatures,
# function order or export membership. All current functions are exports.
def walk(fuel: Nat, visit: Visit, +pass: Pass, +all: List<&2,C.Function>, +available: List<&2,C.Function>, +base: U32, +env: List<&2,C.Binding>) -> Result<S.Error,C.Term>:
  match fuel visit:
    case 0n _: T.exhausted(C.Term)
    case 1n+ +n Expression{C.Value{token,typ,tag}}: Done{C.Value{token,typ,tag}}
    case 1n+ +n Expression{C.Reference{+token,+level,+typ}}:
      Done{S.choose(C.Term,is_fold(pass),u => or_original(F.known(env,level),C.Reference{token,level,typ}),u => C.Reference{token,level,typ})}
    case 1n+ +n Expression{C.Construct{+token,+typ,+tag,+fields,args}}:
      S.bind(C.Term,C.Term,walk(n,Arguments{args,fields},pass,all,available,base,env),list =>
        T.terms(list,xs => Done{C.Construct{token,typ,tag,fields,xs}}))
    case 1n+ +n Expression{C.Application{+token,+index,+typ,+args}}:
      parameters(I.function_at(all,index),params =>
        S.bind(C.Term,C.Term,walk(n,Arguments{args,params},pass,all,available,base,env),list => T.terms(list,+xs =>
          S.choose(Result<S.Error,C.Term>,is_inline(pass),u =>
            S.bind(Maybe<&2,C.Term>,C.Term,I.candidate(n,I.function_at(available,index),index,U32.from_nat(List.length(&2,C.Function,available)),base,xs),option =>
              Done{or_original(option,C.Application{token,index,typ,xs})}),u => Done{C.Application{token,index,typ,xs}}))))
    case 1n+ +n Expression{C.Let{+token,+level,+q,+typ,+value,+body}}:
      S.bind(C.Term,C.Term,S.choose(Result<S.Error,C.Term>,U32.is_eq(q,0),u => Done{value},u => walk(n,Expression{value},pass,all,available,base,env)),+initial =>
        +known = S.choose(Maybe<&2,C.Term>,Bool.and(is_fold(pass),U32.is_ne(q,0)),u => F.literal(initial),u => None{})
        S.bind(C.Term,C.Term,walk(n,Expression{body},pass,all,available,base,Con{C.Binding{token,level,q,typ,False{},known},env}),+rest =>
          S.choose(Result<S.Error,C.Term>,is_fold(pass),u =>
            S.bind(Maybe<&2,C.Term>,C.Term,F.fuse(n,level,initial,rest),option =>
              rewrite(option,C.Let{token,level,q,typ,initial,rest},term => walk(n,Expression{term},pass,all,available,base,env))),u =>
            keep_let(pass,n,token,level,q,typ,initial,rest))))
    case 1n+ +n Expression{C.Case{+token,+level,+typ,+arms}}:
      S.bind(C.Term,C.Term,walk(n,Expression{C.Sequence{arms}},pass,all,available,base,env),list => T.terms(list,+xs =>
        S.choose(Result<S.Error,C.Term>,is_fold(pass),u =>
          known_case(F.known(env,level),xs,C.Case{token,level,typ,xs},term => Done{term}),u => Done{C.Case{token,level,typ,xs}})))
    case 1n+ +n Expression{C.Branch{+tag,+fields,body}}:
      S.bind(C.Term,C.Term,walk(n,Expression{body},pass,all,available,base,List.append(&2,C.Binding,fields,env)),rest => Done{C.Branch{tag,fields,rest}})
    case 1n+ +n Expression{C.Sequence{Nil{}}}: Done{C.Sequence{Nil{}}}
    case 1n+ +n Expression{C.Sequence{Con{head,+tail}}}:
      S.bind(C.Term,C.Term,walk(n,Expression{head},pass,all,available,base,env),first =>
        S.bind(C.Term,C.Term,walk(n,Expression{C.Sequence{tail}},pass,all,available,base,env),list => T.terms(list,xs => Done{C.Sequence{Con{first,xs}}})))
    case 1n+n Expression{term}: Fail{S.Unsupported{"opt","term",S.At{0,0,0,0}}}
    case 1n+ +n Arguments{Nil{},Nil{}}: Done{C.Sequence{Nil{}}}
    case 1n+ +n Arguments{Con{+head,+tail},Con{C.Parameter{token,q,typ},+rest}}:
      S.bind(C.Term,C.Term,S.choose(Result<S.Error,C.Term>,U32.is_eq(q,0),u => Done{head},u => walk(n,Expression{head},pass,all,available,base,env)),first =>
        S.bind(C.Term,C.Term,walk(n,Arguments{tail,rest},pass,all,available,base,env),list => T.terms(list,xs => Done{C.Sequence{Con{first,xs}}})))
    case 1n+ +n Arguments{args,params}: T.internal(C.Term,"argument-arity")

def prepend(signature: C.Signature, body: C.Term, rest: List<&2,C.Function>) -> List<&2,C.Function>:
  Con{C.Function{signature,body},rest}

def arity(signature: C.Signature) -> U32:
  match signature:
    case C.Signature{token,params,typ}: U32.from_nat(List.length(&2,C.Parameter,params))

def functions(remaining: List<&2,C.Function>, +previous: List<&2,C.Function>, +all: List<&2,C.Function>, +depth: Nat, +pass: Pass) -> Result<S.Error,List<&2,C.Function>>:
  match remaining:
    case Nil{}: Done{Nil{}}
    case Con{C.Function{+signature,+body},+tail}:
      S.bind(U32,List<&2,C.Function>,T.measure(depth,body,T.Ceiling{}),base =>
        S.bind(C.Term,List<&2,C.Function>,walk(depth,Expression{body},pass,all,previous,T.maximum(base,arity(signature)),Nil{}),+term =>
          S.bind(List<&2,C.Function>,List<&2,C.Function>,functions(tail,List.append(&2,C.Function,previous,[C.Function{signature,term}]),all,depth,pass),rest =>
            Done{prepend(signature,term,rest)})))

def apply(+depth: Nat, pass: Pass, book: C.Book) -> Result<S.Error,C.Book>:
  match book:
    case C.Book{+types,+items}:
      S.bind(List<&2,C.Function>,C.Book,functions(items,Nil{},items,depth,pass),result => K.verify(depth,C.Book{types,result}))

def compose(passes: List<&2,Pass>, +depth: Nat, book: C.Book) -> Result<S.Error,C.Book>:
  match passes:
    case Nil{}: Done{book}
    case Con{head,+tail}:
      S.bind(C.Book,C.Book,apply(depth,head,book),next => compose(tail,depth,next))

# A successful pipeline is a fixed point, not an arbitrary number of rewrites.
# A bounded failure publishes no partially optimized book.
def settle(rounds: Nat, +depth: Nat, +book: C.Book) -> Result<S.Error,C.Book>:
  match rounds:
    case 0n: T.exhausted(C.Book)
    case 1n+ +n:
      S.bind(C.Book,C.Book,compose([Inline{},Fold{},Dead{}],depth,book),+next =>
        S.bind(Bool,C.Book,T.stable(book,next,depth),same =>
          S.choose(Result<S.Error,C.Book>,same,u => Done{next},u => settle(n,depth,next))))

def pipeline(+depth: Nat, book: C.Book) -> Result<S.Error,C.Book>:
  S.bind(C.Book,C.Book,K.verify(depth,book),checked => settle(8n,depth,checked))

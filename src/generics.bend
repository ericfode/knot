import Base
import ./syntax.bend as S
import ./core.bend as C
import ./types.bend as T
import ./generic-catalog.bend as G
import ./type-erasure.bend as R
import ./scope.bend as E
import ./patterns.bend as P

type Binding is Data:
  Binding{token: S.Token, level: U32, quantity: U32, domain: T.Expr, parameter: Bool, known: Maybe<&2,C.Term>}
type Environment is Data:
  Environment{bindings: List<&2,Binding>, next: U32, open: List<&2,U32>, live: Bool, smaller: List<&2,U32>, root: Maybe<&2,U32>}
type Checked is Data:
  Checked{term: C.Term, domain: T.Expr, uses: List<&2,U32>}
type Fields is Data:
  Fields{environment: Environment, bindings: List<&2,C.Binding>, arguments: List<&2,C.Term>}
type Mode is Data:
  Expression{node: S.Node, expected: Maybe<&2,T.Expr>}
  Arguments{nodes: List<&2,S.Node>, parameters: List<&2,G.Parameter>, substitutions: List<&2,T.Binding>, index: U32, result: T.Expr, token: S.Token}
  Arms{nodes: List<&2,S.Node>, binding: Binding, family: G.Family, expected: T.Expr, seen: List<&2,U32>, token: S.Token}
  Rebuild{term: C.Term, domain: T.Expr}
  RebuildArguments{terms: List<&2,C.Term>, parameters: List<&2,C.Parameter>, token: S.Token}

def domain(binding: Binding) -> T.Expr:
  match binding:
    case Binding{token,level,q,typ,param,known}: typ

def symbols(bindings: List<&2,Binding>) -> List<&2,G.Symbol>:
  match bindings:
    case Nil{}: Nil{}
    case Con{Binding{token,level,q,typ,param,known},tail}: Con{G.Symbol{token,level,typ},symbols(tail)}

def context(env: Environment) -> List<&2,G.Symbol>:
  match env:
    case Environment{bindings,next,open,live,smaller,root}: symbols(bindings)

def find(bindings: List<&2,Binding>, +token: S.Token) -> Result<S.Error,Binding>:
  match bindings:
    case Nil{}: C.invalid(Binding,"free-name",token)
    case Con{+head,+tail}:
      match head:
        case Binding{name,level,q,typ,param,known}:
          S.choose(Result<S.Error,Binding>,String.eq(S.text(name),S.text(token)),u => Done{head},u => find(tail,token))

def lookup(env: Environment, token: S.Token) -> Result<S.Error,Binding>:
  match env:
    case Environment{bindings,next,open,live,smaller,root}: find(bindings,token)

def find_level(bindings: List<&2,Binding>, +level: U32) -> Result<S.Error,Binding>:
  match bindings:
    case Nil{}: C.internal(Binding,"generic-binding-level")
    case Con{+head,+tail}:
      match head:
        case Binding{token,id,q,typ,param,known}:
          S.choose(Result<S.Error,Binding>,U32.is_eq(id,level),u => Done{head},u => find_level(tail,level))

def expected(+token: S.Token, wanted: Maybe<&2,T.Expr>, +value: Checked) -> Result<S.Error,Checked>:
  match wanted value:
    case None{} _: Done{value}
    case Some{target} Checked{term,actual,uses}:
      S.choose(Result<S.Error,Checked>,T.equal(T.normalize(actual),T.normalize(target)),u => Done{value},u => C.invalid(Checked,"type-mismatch",token))

def live_scope(env: Environment, q: U32) -> Environment:
  match env:
    case Environment{bindings,next,open,live,smaller,root}: Environment{bindings,next,open,Bool.and(live,U32.is_ne(q,0)),smaller,root}

def replace(bindings: List<&2,Binding>, +level: U32, +term: C.Term) -> List<&2,Binding>:
  match bindings:
    case Nil{}: Nil{}
    case Con{Binding{token,+id,q,typ,param,+known},tail}:
      Con{Binding{token,id,q,typ,param,S.choose(Maybe<&2,C.Term>,U32.is_eq(id,level),u => Some{term},u => known)},replace(tail,level,term)}

def first_live(root: Maybe<&2,U32>, q: U32, level: U32) -> Maybe<&2,U32>:
  match root:
    case Some{index}: Some{index}
    case None{}: S.choose(Maybe<&2,U32>,U32.is_eq(q,0),u => None{},u => Some{level})

def parameters(params: List<&2,G.Parameter>, +level: U32, env: List<&2,Binding>, open: List<&2,U32>, root: Maybe<&2,U32>) -> Environment:
  match params:
    case Nil{}: Environment{env,level,List.reverse(&2,U32,open),True{},Nil{},root}
    case Con{G.Parameter{token,+q,typ},tail}:
      parameters(tail,U32.add(level,1),Con{Binding{token,level,q,typ,True{},None{}},env},Con{level,open},first_live(root,q,level))

def at_root(root: Maybe<&2,U32>, level: U32) -> Bool:
  match root:
    case None{}: False{}
    case Some{index}: U32.is_eq(index,level)

def branch(env: Environment, +level: U32, known: C.Term, fields: List<&2,C.Binding>) -> Environment:
  match env:
    case Environment{bindings,next,open,live,+smaller,+root}:
      +levels = E.levels(fields)
      Environment{replace(bindings,level,known),next,List.append(&2,U32,levels,E.after(open,level)),live,
        S.choose(List<&2,U32>,Bool.or(at_root(root,level),E.contains(smaller,level)),u => List.append(&2,U32,levels,smaller),u => smaller),root}

def occurrence(binding: Binding, +token: S.Token, env: Environment, next: C.Term -> T.Expr -> Result<S.Error,Checked>) -> Result<S.Error,Checked>:
  match binding env:
    case Binding{name,level,q,typ,param,Some{term}} _: next(term,typ)
    case Binding{name,+level,+q,+typ,param,None{}} Environment{bindings,index,open,+live,smaller,root}:
      S.choose(Result<S.Error,Checked>,Bool.and(live,U32.is_eq(q,0)),u => C.invalid(Checked,"erased-live",token),u =>
        Done{Checked{C.Reference{token,level,R.type_id(typ)},typ,S.choose(List<&2,U32>,Bool.and(live,U32.is_eq(q,1)),u => [level],u => Nil{})}})

def prepend_argument(head: Checked, tail: Checked, +token: S.Token) -> Result<S.Error,Checked>:
  match head tail:
    case Checked{+term,typ,uses} Checked{C.Sequence{+items},+result,rest}:
      S.bind(List<&2,U32>,Checked,E.sequential(uses,rest,token),merged => Done{Checked{C.Sequence{Con{term,items}},result,merged}})
    case _ _: C.internal(Checked,"generic-arguments")

def static_argument(value: G.Typed, wanted: T.Expr, +token: S.Token, next: T.Expr -> Result<S.Error,Checked>) -> Result<S.Error,Checked>:
  match value:
    case G.Typed{+term,kind}:
      S.choose(Result<S.Error,Checked>,G.fits(kind,wanted),u => next(term),u => C.invalid(Checked,"type-mismatch",token))

def static_result(value: Checked, token: S.Token) -> Result<S.Error,Checked>:
  match value:
    case Checked{C.Sequence{items},result,uses}: Done{Checked{C.Sequence{Con{C.Value{token,0,0},items}},result,uses}}
    case _: C.internal(Checked,"generic-static-arguments")

def substitute_parameters(params: List<&2,G.Parameter>, +substitutions: List<&2,T.Binding>) -> List<&2,G.Parameter>:
  match params:
    case Nil{}: Nil{}
    case Con{G.Parameter{token,q,typ},tail}: Con{G.Parameter{token,q,G.replace(typ,substitutions)},substitute_parameters(tail,substitutions)}

def generic(family: G.Family) -> Bool:
  match family:
    case G.Family{token,params,kind,ctors,value}: value

def constructor_index(actual: Maybe<&2,U32>, index: U32, +token: S.Token, next: Unit -> Result<S.Error,Checked>) -> Result<S.Error,Checked>:
  match actual:
    case None{}: C.invalid(Checked,"type-mismatch",token)
    case Some{found}: S.choose(Result<S.Error,Checked>,U32.is_eq(index,found),next,u => C.invalid(Checked,"type-mismatch",token))

def constructor_type(wanted: Maybe<&2,T.Expr>, reference: G.ConstructorRef, +token: S.Token, next: T.Expr -> U32 -> List<&2,G.Parameter> -> Result<S.Error,Checked>) -> Result<S.Error,Checked>:
  match wanted reference:
    case Some{+typ} G.ConstructorRef{index,+tag,G.Constructor{name,+fields}}:
      constructor_index(G.family_id(typ),index,token,u => next(typ,tag,substitute_parameters(fields,G.instantiated(typ))))
    case None{} _: C.invalid(Checked,"annotation-required",token)

def constructor_result(value: Checked, token: S.Token, +typ: T.Expr, tag: U32, params: List<&2,G.Parameter>, boxed: Bool) -> Result<S.Error,Checked>:
  match value:
    case Checked{C.Sequence{items},ignored,uses}: Done{Checked{R.construct(token,typ,tag,params,items,boxed),typ,uses}}
    case _: C.internal(Checked,"generic-constructor-arguments")

def constructor_family(reference: G.ConstructorRef, +families: List<&2,G.Family>, next: G.Family -> Result<S.Error,Checked>) -> Result<S.Error,Checked>:
  match reference:
    case G.ConstructorRef{index,tag,ctor}: S.bind(G.Family,Checked,G.family_at(families,index),next)

def occupied(found: Maybe<&2,G.Symbol>) -> Bool:
  match found:
    case None{}: False{}
    case Some{value}: True{}

def callable(reference: G.FunctionRef, +token: S.Token, +current: U32, env: Environment) -> Result<S.Error,G.FunctionRef>:
  match reference env:
    case G.FunctionRef{+index,+sig} Environment{bindings,next,open,+live,smaller,root}:
      S.choose(Result<S.Error,G.FunctionRef>,occupied(G.named(symbols(bindings),token)),u => C.invalid(G.FunctionRef,"not-callable",token),u =>
        S.choose(Result<S.Error,G.FunctionRef>,Bool.and(live,U32.is_gt(index,current)),u => C.invalid(G.FunctionRef,"forward-live-call",token),u => Done{G.FunctionRef{index,sig}}))

def descends(args: List<&2,C.Term>, params: List<&2,G.Parameter>, +smaller: List<&2,U32>) -> Bool:
  match args params:
    case Con{+head,+tail} Con{G.Parameter{token,q,typ},+rest}:
      S.choose(Bool,U32.is_eq(q,0),u => descends(tail,rest,smaller),u => E.descends(Con{head,Nil{}},smaller))
    case _ _: False{}

def call_result(value: Checked, +token: S.Token, +index: U32, +current: U32, params: List<&2,G.Parameter>, env: Environment) -> Result<S.Error,Checked>:
  match value env:
    case Checked{C.Sequence{+args},+typ,+uses} Environment{bindings,next,open,live,smaller,root}:
      S.choose(Result<S.Error,Checked>,Bool.and(live,Bool.and(U32.is_eq(index,current),Bool.not(descends(args,params,smaller)))),u =>
        C.unsupported(Checked,"recursive-call",token),u => Done{Checked{C.Application{token,index,R.type_id(typ),args},typ,uses}})
    case _ _: C.internal(Checked,"generic-call-result")

def call_body(reference: G.FunctionRef, +token: S.Token, +wanted: Maybe<&2,T.Expr>, +current: U32, +env: Environment, next: List<&2,G.Parameter> -> T.Expr -> Result<S.Error,Checked>) -> Result<S.Error,Checked>:
  match reference:
    case G.FunctionRef{+index,G.Signature{name,+params,result,body}}:
      S.bind(Checked,Checked,next(params,result),value =>
        S.bind(Checked,Checked,call_result(value,token,index,current,params,env),checked => expected(token,wanted,checked)))

def annotation(node: Maybe<&2,S.Node>, +families: List<&2,G.Family>, +env: Environment, +depth: Nat, +token: S.Token) -> Result<S.Error,Maybe<&2,T.Expr>>:
  match node:
    case None{}: Done{None{}}
    case Some{typ}:
      S.bind(G.Typed,Maybe<&2,T.Expr>,G.expression(depth,typ,families,context(env)),typed =>
        S.bind(T.Expr,Maybe<&2,T.Expr>,G.type_value(typed,token),+value =>
          S.choose(Result<S.Error,Maybe<&2,T.Expr>>,Bool.or(G.is_sort(value),G.is_quant(value)),u =>
            C.unsupported(Maybe<&2,T.Expr>,"type-level-binding",token),u => Done{Some{value}})))

def old_annotation(node: Maybe<&2,S.Token>) -> S.Node:
  match node:
    case None{}: S.Sequence{Nil{}}
    case Some{token}: S.Variable{token}

def binding_annotation(node: S.Node) -> Maybe<&2,S.Node>:
  match node:
    case S.Sequence{Nil{}}: None{}
    case value: Some{value}

def binding_body(value: Checked, +token: S.Token, +q: U32, +families: List<&2,G.Family>, +env: Environment, next: Environment -> Result<S.Error,Checked>) -> Result<S.Error,Checked>:
  match value env:
    case Checked{initial,+typ,uses} Environment{+bindings,+level,open,+live,+smaller,+root}:
      S.choose(Result<S.Error,Checked>,U32.is_ge(level,4096),u => C.exhausted(Checked,token),u =>
        S.choose(Result<S.Error,Checked>,Bool.or(G.is_sort(typ),G.is_quant(typ)),u =>
          C.unsupported(Checked,"type-level-binding",token),u =>
        S.bind(T.Expr,Checked,G.kind(typ,families,context(env)),kind =>
          S.bind(Unit,Checked,G.demand(token,q,kind),u => next(Environment{Con{Binding{token,level,q,typ,False{},None{}},bindings},U32.add(level,1),Nil{},live,smaller,root})))))

def let_result(value: Checked, body: Checked, +token: S.Token, +level: U32, q: U32) -> Result<S.Error,Checked>:
  match value body:
    case Checked{+initial,+typ,uses} Checked{+term,+result,remaining}:
      S.bind(List<&2,U32>,Checked,E.sequential(uses,E.remove(remaining,level),token),merged => Done{Checked{C.Let{token,level,q,R.type_id(typ),initial,term},result,merged}})

def let_body(+value: Checked, +token: S.Token, +q: U32, +families: List<&2,G.Family>, +env: Environment, next: Environment -> Result<S.Error,Checked>) -> Result<S.Error,Checked>:
  match env:
    case Environment{bindings,+level,open,live,smaller,root}:
      S.bind(Checked,Checked,binding_body(value,token,q,families,env,next),body => let_result(value,body,token,level,q))

def matchable(+binding: Binding, +token: S.Token, env: Environment) -> Result<S.Error,Binding>:
  match binding env:
    case Binding{name,+level,q,typ,param,None{}} Environment{bindings,next,open,live,smaller,root}:
      S.choose(Result<S.Error,Binding>,Bool.and(live,U32.is_eq(q,0)),u => C.invalid(Binding,"erased-scrutinee",token),u =>
        S.choose(Result<S.Error,Binding>,Bool.and(param,E.contains(open,level)),u => Done{binding},u => C.invalid(Binding,"unmatchable-binder",token)))
    case _ _: C.invalid(Binding,"already-matched",token)

def scrutinee(node: S.Node, +env: Environment) -> Result<S.Error,Binding>:
  match node:
    case S.Variable{+token}: S.bind(Binding,Binding,lookup(env,token),binding => matchable(binding,token,env))
    case S.Constructor{token,args}: C.invalid(Binding,"constructor-scrutinee",token)
    case S.Call{token,args}: C.invalid(Binding,"computed-scrutinee",token)
    case _: C.internal(Binding,"generic-scrutinee-node")

def constructor_patterns(nodes: List<&2,S.Node>) -> Result<S.Error,Unit>:
  match nodes:
    case Nil{}: Done{Unit{}}
    case Con{S.Arm{token,S.Constructor{name,args},body},tail}: constructor_patterns(tail)
    case Con{S.Arm{token,pat,body},tail}: C.unsupported(Unit,"variable-pattern",token)
    case _: C.internal(Unit,"generic-arm-node")

def matched_family(found: Maybe<&2,U32>, families: List<&2,G.Family>, token: S.Token) -> Result<S.Error,G.Family>:
  match found:
    case None{}: C.unsupported(G.Family,"abstract-match",token)
    case Some{index}: G.family_at(families,index)

def matched_result(value: Checked, binding: Binding, +token: S.Token, +wanted: T.Expr, env: Environment) -> Result<S.Error,Checked>:
  match value binding env:
    case Checked{C.Sequence{+arms},ignored,uses} Binding{name,+level,q,typ,param,known} Environment{bindings,next,open,live,smaller,root}:
      S.bind(List<&2,U32>,Checked,E.sequential(S.choose(List<&2,U32>,Bool.and(live,U32.is_eq(q,1)),u => [level],u => Nil{}),uses,token),merged =>
        Done{Checked{C.Case{token,level,R.type_id(wanted),arms},wanted,merged}})
    case _ _ _: C.internal(Checked,"generic-match-result")

def matched(+binding: Binding, +token: S.Token, +wanted: Maybe<&2,T.Expr>, +families: List<&2,G.Family>, +env: Environment, next: G.Family -> T.Expr -> Result<S.Error,Checked>) -> Result<S.Error,Checked>:
  match wanted:
    case None{}: C.unsupported(Checked,"uninferred-match",token)
    case Some{+typ}:
      S.bind(G.Family,Checked,matched_family(G.family_id(domain(binding)),families,token),family =>
        S.bind(Checked,Checked,next(family,typ),value => matched_result(value,binding,token,typ,env)))

def add_field(env: Environment, +token: S.Token, +q: U32, +typ: T.Expr, next: Environment -> C.Binding -> C.Term -> Result<S.Error,Fields>) -> Result<S.Error,Fields>:
  match env:
    case Environment{+bindings,+level,+open,+live,+smaller,+root}:
      S.choose(Result<S.Error,Fields>,U32.is_ge(level,4096),u => C.exhausted(Fields,token),u =>
        next(Environment{Con{Binding{token,level,q,typ,True{},None{}},bindings},U32.add(level,1),open,live,smaller,root},
          C.Binding{token,level,q,R.type_id(typ),True{},None{}},C.Reference{token,level,R.type_id(typ)}))

def field_node(node: S.Node, next: S.Token -> U32 -> Result<S.Error,Fields>) -> Result<S.Error,Fields>:
  match node:
    case S.Variable{token}: next(token,1)
    case S.Promotion{token}: next(token,2)
    case S.Constructor{token,args}: C.unsupported(Fields,"nested-field-pattern",token)
    case S.Call{token,args}: C.invalid(Fields,"pattern-form",token)
    case _: C.internal(Fields,"generic-field-node")

def prepend_field(binding: C.Binding, term: C.Term, rest: Fields) -> Fields:
  match rest:
    case Fields{env,fields,args}: Fields{env,Con{binding,fields},Con{term,args}}

def fields(nodes: List<&2,S.Node>, params: List<&2,G.Parameter>, +parent: U32, +families: List<&2,G.Family>, +env: Environment, +origin: S.Token) -> Result<S.Error,Fields>:
  match nodes params:
    case Nil{} Nil{}: Done{Fields{env,Nil{},Nil{}}}
    case Con{node,+tail} Con{G.Parameter{name,+q,+typ},+rest}:
      field_node(node,+token => mark =>
        S.choose(Result<S.Error,Fields>,G.has_constructor(families,token),u => C.invalid(Fields,"constructor-pattern-binder",token),u =>
          +actual = P.quantity(q,parent,mark)
          S.bind(T.Expr,Fields,G.kind(typ,families,context(env)),kind =>
            S.bind(Unit,Fields,G.demand(token,actual,kind),u =>
              add_field(env,token,actual,typ,bound => binding => term =>
                S.bind(Fields,Fields,fields(tail,rest,parent,families,bound,origin),remaining => Done{prepend_field(binding,term,remaining)}))))))
    case _ _: C.invalid(Fields,"pattern-arity",origin)

def open_fields(value: Fields, binding: Binding, tag: U32, params: List<&2,G.Parameter>, boxed: Bool) -> Fields:
  match value binding:
    case Fields{env,+bindings,+args} Binding{token,level,q,typ,param,known}:
      Fields{branch(env,level,R.construct(token,typ,tag,params,args,boxed),bindings),bindings,args}

def pattern_type(actual: Maybe<&2,U32>, expected: U32) -> Bool:
  match actual:
    case None{}: False{}
    case Some{index}: U32.is_eq(index,expected)

def pattern(reference: G.ConstructorRef, +binding: Binding, +seen: List<&2,U32>, +token: S.Token, next: U32 -> List<&2,G.Parameter> -> Result<S.Error,Checked>) -> Result<S.Error,Checked>:
  match reference:
    case G.ConstructorRef{index,+tag,G.Constructor{name,+params}}:
      S.choose(Result<S.Error,Checked>,pattern_type(G.family_id(domain(binding)),index),u =>
        S.choose(Result<S.Error,Checked>,E.contains(seen,tag),u => C.unsupported(Checked,"duplicate-arm",token),u => next(tag,substitute_parameters(params,G.instantiated(domain(binding))))),u => C.invalid(Checked,"pattern-type",token))

def field_scope(+binding: Binding, tag: U32, +params: List<&2,G.Parameter>, nodes: List<&2,S.Node>, +boxed: Bool, families: List<&2,G.Family>, env: Environment) -> Result<S.Error,Fields>:
  match binding:
    case Binding{token,level,q,typ,param,known}:
      S.bind(Fields,Fields,fields(nodes,params,q,families,env,token),value => Done{open_fields(value,binding,tag,params,boxed)})

def prepend_arm(head: Checked, tail: Checked, tag: U32, +fields: List<&2,C.Binding>, token: S.Token, boxed: Bool) -> Result<S.Error,Checked>:
  match head tail:
    case Checked{body,typ,uses} Checked{C.Sequence{items},result,rest}:
      Done{Checked{C.Sequence{Con{C.Branch{tag,R.bindings(token,fields,boxed),body},items}},result,E.alternatives(E.remove_fields(fields,uses),rest)}}
    case _ _: C.internal(Checked,"generic-arm-result")

def arm_body(value: Fields, next: Environment -> List<&2,C.Binding> -> Result<S.Error,Checked>) -> Result<S.Error,Checked>:
  match value:
    case Fields{env,fields,args}: next(env,fields)

def complete(family: G.Family, seen: List<&2,U32>, wanted: T.Expr, +token: S.Token) -> Result<S.Error,Checked>:
  match family:
    case G.Family{name,params,kind,ctors,boxed}:
      S.choose(Result<S.Error,Checked>,Nat.is_eq(List.length(&2,G.Constructor,ctors),List.length(&2,U32,seen)),u => Done{Checked{C.Sequence{Nil{}},wanted,Nil{}}},u => C.invalid(Checked,"missing-arm",token))

def rebuilt(value: Checked, token: S.Token, +typ: T.Expr, tag: U32, params: List<&2,C.Parameter>) -> Result<S.Error,Checked>:
  match value:
    case Checked{C.Sequence{args},ignored,uses}: Done{Checked{C.Construct{token,R.type_id(typ),tag,params,args},typ,uses}}
    case _: C.internal(Checked,"generic-rebuild-result")

def unbound(found: Result<S.Error,G.Named>, token: S.Token, error: S.Error) -> Result<S.Error,Binding>:
  match found:
    case Done{reference}: C.unsupported(Binding,"type-level-term",token)
    case Fail{ignored}: Fail{error}

def term_name(found: Result<S.Error,Binding>, families: List<&2,G.Family>, +token: S.Token) -> Result<S.Error,Binding>:
  match found:
    case Done{binding}: Done{binding}
    case Fail{error}: unbound(G.family_named(families,token,0),token,error)

# Types are checked in their own environment; only their erased projection
# crosses into the runtime IR. All recursive checker work spends depth.
def run(fuel: Nat, mode: Mode, +catalog: G.Catalog, +current: U32, +env: Environment) -> Result<S.Error,Checked>:
  match fuel mode catalog env:
    case 0n _ _ _: Fail{S.Exhausted{"check",S.At{0,0,0,0}}}
    case 1n+ +n Expression{S.Variable{+token},+wanted} G.Catalog{families,sigs} _:
      S.bind(Binding,Checked,term_name(lookup(env,token),families,token),binding =>
        S.bind(Checked,Checked,occurrence(binding,token,env,term => typ => run(n,Rebuild{term,typ},catalog,current,env)),value => expected(token,wanted,value)))
    case 1n+ +n Expression{S.Constructor{+token,+args},+wanted} G.Catalog{+families,sigs} _:
      S.bind(G.ConstructorRef,Checked,G.constructor_named(families,token,0),+reference =>
        constructor_type(wanted,reference,token,+typ => +tag => +params =>
          S.choose(Result<S.Error,Checked>,Nat.is_eq(List.length(&2,S.Node,args),List.length(&2,G.Parameter,params)),u =>
            constructor_family(reference,families,+family =>
              S.bind(Checked,Checked,run(n,Arguments{args,params,Nil{},0,typ,token},catalog,current,env),value => constructor_result(value,token,typ,tag,params,generic(family)))),u => C.invalid(Checked,"constructor-arity",token))))
    case 1n+ +n Expression{S.Call{+token,+args},+wanted} G.Catalog{families,sigs} _:
      S.bind(G.FunctionRef,Checked,G.function_named(sigs,token,0),reference =>
        S.bind(G.FunctionRef,Checked,callable(reference,token,current,env),call =>
          call_body(call,token,wanted,current,env,params => result => run(n,Arguments{args,params,Nil{},0,result,token},catalog,current,env))))
    case 1n+ +n Expression{S.Binding{token,q,ann,value,body},wanted} _ _:
      run(n,Expression{S.TypedBinding{token,q,old_annotation(ann),value,body},wanted},catalog,current,env)
    case 1n+ +n Expression{S.TypedBinding{+token,+q,+ann,+value,+body},+wanted} G.Catalog{+families,sigs} _:
      S.bind(Maybe<&2,T.Expr>,Checked,annotation(binding_annotation(ann),families,env,n,token),target =>
        S.bind(Checked,Checked,run(n,Expression{value,target},catalog,current,live_scope(env,q)),initial =>
          let_body(initial,token,q,families,env,bound => run(n,Expression{body,wanted},catalog,current,bound))))
    case 1n+ +n Expression{S.Match{+token,+value,+arms},+wanted} G.Catalog{+families,sigs} _:
      S.bind(Unit,Checked,constructor_patterns(arms),u =>
        S.bind(Binding,Checked,scrutinee(value,env),+binding =>
          matched(binding,token,wanted,families,env,family => typ => run(n,Arms{arms,binding,family,typ,Nil{},token},catalog,current,env))))
    case 1n+n Expression{S.TypeApply{token,args,q},wanted} _ _: C.unsupported(Checked,"type-level-term",token)
    case 1n+n Expression{S.Quantity{token,q},wanted} _ _: C.unsupported(Checked,"type-level-term",token)
    case 1n+n Expression{S.TypeKind{token,q},wanted} _ _: C.unsupported(Checked,"type-level-term",token)
    case 1n+n Expression{S.QuantType{token},wanted} _ _: C.unsupported(Checked,"type-level-term",token)
    case 1n+n Expression{S.Meet{token,left,right},wanted} _ _: C.unsupported(Checked,"type-level-term",token)
    case 1n+n Expression{node,wanted} _ _: C.internal(Checked,"generic-expression-node")
    case 1n+n Arguments{Nil{},Nil{},substitutions,index,result,token} _ _:
      Done{Checked{C.Sequence{Nil{}},G.replace(result,substitutions),Nil{}}}
    case 1n+ +n Arguments{Con{+head,+tail},Con{G.Parameter{name,+q,typ},+rest},+substitutions,+index,+result,+token} G.Catalog{+families,sigs} _:
      +target = G.replace(typ,substitutions)
      S.choose(Result<S.Error,Checked>,Bool.or(G.is_sort(target),G.is_quant(target)),u =>
        S.choose(Result<S.Error,Checked>,U32.is_ne(q,0),u => C.unsupported(Checked,"live-type-argument",token),u =>
        S.bind(G.Typed,Checked,G.expression(n,head,families,context(env)),value =>
          static_argument(value,target,token,actual =>
            S.bind(Checked,Checked,run(n,Arguments{tail,rest,Con{T.Binding{index,actual},substitutions},U32.add(index,1),result,token},catalog,current,env),remaining => static_result(remaining,token))))),u =>
        S.bind(Checked,Checked,run(n,Expression{head,Some{target}},catalog,current,live_scope(env,q)),checked =>
          S.bind(Checked,Checked,run(n,Arguments{tail,rest,substitutions,U32.add(index,1),result,token},catalog,current,env),remaining => prepend_argument(checked,remaining,token))))
    case 1n+n Arguments{nodes,params,substitutions,index,result,token} _ _: C.invalid(Checked,"call-arity",token)
    case 1n+n Arms{Nil{},binding,family,wanted,seen,token} _ _: complete(family,seen,wanted,token)
    case 1n+ +n Arms{Con{S.Arm{+arm,S.Constructor{+name,+nodes},+body},+tail},+binding,+family,+wanted,+seen,+token} G.Catalog{+families,sigs} _:
      S.bind(G.ConstructorRef,Checked,G.constructor_named(families,name,0),reference =>
        pattern(reference,binding,seen,arm,+tag => params =>
          S.bind(Fields,Checked,field_scope(binding,tag,params,nodes,generic(family),families,env),opened =>
            arm_body(opened,bound => +fields =>
              S.bind(Checked,Checked,run(n,Expression{body,Some{wanted}},catalog,current,bound),checked =>
                S.bind(Checked,Checked,run(n,Arms{tail,binding,family,wanted,Con{tag,seen},token},catalog,current,env),remaining => prepend_arm(checked,remaining,tag,fields,name,generic(family))))))))
    case 1n+n Arms{nodes,binding,family,wanted,seen,token} _ _: C.internal(Checked,"generic-arm-node")
    case 1n+n Rebuild{C.Value{token,id,tag},typ} _ _: Done{Checked{C.Value{token,id,tag},typ,Nil{}}}
    case 1n+ +n Rebuild{C.Reference{+token,level,id},typ} _ Environment{bindings,next,open,live,smaller,root}:
      S.bind(Binding,Checked,find_level(bindings,level),binding => occurrence(binding,token,env,term => domain => run(n,Rebuild{term,domain},catalog,current,env)))
    case 1n+ +n Rebuild{C.Construct{+token,id,+tag,+params,args},+typ} _ _:
      S.bind(Checked,Checked,run(n,RebuildArguments{args,params,token},catalog,current,env),value => rebuilt(value,token,typ,tag,params))
    case 1n+n Rebuild{term,typ} _ _: C.internal(Checked,"generic-refinement-node")
    case 1n+n RebuildArguments{Nil{},Nil{},token} _ _: Done{Checked{C.Sequence{Nil{}},T.QuantType{},Nil{}}}
    case 1n+ +n RebuildArguments{Con{head,+tail},Con{C.Parameter{name,q,typ},+rest},+token} _ _:
      S.bind(Checked,Checked,run(n,Rebuild{head,T.Family{typ}},catalog,current,live_scope(env,q)),checked =>
        S.bind(Checked,Checked,run(n,RebuildArguments{tail,rest,token},catalog,current,env),remaining => prepend_argument(checked,remaining,token)))
    case 1n+n RebuildArguments{terms,params,token} _ _: C.internal(Checked,"generic-refinement-arity")

def checked_function(signature: G.Signature, value: Checked) -> C.Function:
  match value:
    case Checked{term,typ,uses}: C.Function{R.signature(signature),term}

def function_body(+signature: G.Signature, +catalog: G.Catalog, index: U32, depth: Nat) -> Result<S.Error,C.Function>:
  match signature:
    case G.Signature{name,params,result,body}:
      S.bind(Checked,C.Function,run(depth,Expression{body,Some{result}},catalog,index,parameters(params,0,Nil{},Nil{},None{})),value => Done{checked_function(signature,value)})

def functions(signatures: List<&2,G.Signature>, +catalog: G.Catalog, +index: U32, +depth: Nat) -> Result<S.Error,List<&2,C.Function>>:
  match signatures:
    case Nil{}: Done{Nil{}}
    case Con{head,+tail}:
      S.bind(C.Function,List<&2,C.Function>,function_body(head,catalog,index,depth),function =>
        S.bind(List<&2,C.Function>,List<&2,C.Function>,functions(tail,catalog,U32.add(index,1),depth),rest => Done{Con{function,rest}}))

def resolved(+catalog: G.Catalog, depth: Nat) -> Result<S.Error,C.Book>:
  match catalog:
    case G.Catalog{+families,signatures}:
      S.bind(List<&2,C.Function>,C.Book,functions(signatures,catalog,0,depth),bodies => Done{C.Book{R.families(families),bodies}})

def check(+depth: Nat, nodes: List<&2,S.Node>) -> Result<S.Error,C.Book>:
  S.bind(G.Catalog,C.Book,G.catalog(depth,nodes),catalog => resolved(catalog,depth))

def typed_parameters(nodes: List<&2,S.Node>) -> Bool:
  match nodes:
    case Nil{}: False{}
    case Con{S.TypedParameter{token,q,typ},tail}: True{}
    case Con{node,tail}: typed_parameters(tail)

def required(nodes: List<&2,S.Node>) -> Bool:
  match nodes:
    case Nil{}: False{}
    case Con{S.Generic{token,params,kind,ctors},tail}: True{}
    case Con{S.TypedFunction{token,params,result,body},tail}: True{}
    case Con{S.Function{token,params,result,body},tail}: Bool.or(typed_parameters(params),required(tail))
    case Con{node,tail}: required(tail)

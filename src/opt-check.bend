import Base
import ./syntax.bend as S
import ./core.bend as C
import ./catalog.bend as G
import ./scope.bend as E
import ./patterns.bend as P
import ./check.bend as K

type Mode is Data:
  Expression{term: C.Term, expected: U32}
  Arguments{terms: List<&2,C.Term>, parameters: List<&2,C.Parameter>, token: S.Token}
  Arms{terms: List<&2,C.Term>, token: S.Token, level: U32, expected: U32, seen: List<&2,U32>}

def internal(-A: Type, code: String) -> Result<S.Error,A>:
  Fail{S.Internal{"opt-core",code}}

def exhausted(-A: Type) -> Result<S.Error,A>:
  Fail{S.Exhausted{"opt-core",S.At{0,0,0,0}}}

def require(condition: Bool, +code: String) -> Result<S.Error,Unit>:
  S.choose(Result<S.Error,Unit>,condition,u => Done{Unit{}},u => internal(Unit,code))

# Source errors become compiler failures when the input is already checked IR.
def classified(error: S.Error) -> S.Error:
  match error:
    case S.Invalid{phase,code,at}: S.Internal{"opt-core",code}
    case S.Unsupported{phase,code,at}: S.Unsupported{"opt-core",code,at}
    case S.Exhausted{phase,at}: S.Exhausted{"opt-core",at}
    case S.Internal{phase,code}: S.Internal{"opt-core",code}
    case S.Host{phase,code}: S.Host{"opt-core",code}

def result(-A: Data, value: Result<S.Error,A>) -> Result<S.Error,A>:
  match value:
    case Fail{error}: Fail{classified(error)}
    case Done{value}: Done{value}

def parameters_equal(left: List<&2,C.Parameter>, right: List<&2,C.Parameter>) -> Bool:
  match left right:
    case Nil{} Nil{}: True{}
    case Con{C.Parameter{name,q,type_id},tail} Con{C.Parameter{other,r,actual},rest}:
      Bool.and(U32.is_eq(q,r),Bool.and(U32.is_eq(type_id,actual),parameters_equal(tail,rest)))
    case _ _: False{}

def signature_at(sigs: List<&2,C.Signature>, +index: U32) -> Result<S.Error,C.Signature>:
  match sigs:
    case Nil{}: internal(C.Signature,"function-index")
    case Con{+head,+tail}:
      S.choose(Result<S.Error,C.Signature>,U32.is_eq(index,0),u => Done{head},u => signature_at(tail,U32.sub(index,1)))

def signatures(functions: List<&2,C.Function>, +count: U32) -> Result<S.Error,List<&2,C.Signature>>:
  match functions:
    case Nil{}: Done{Nil{}}
    case Con{C.Function{+signature,body},+tail}:
      S.choose(Result<S.Error,List<&2,C.Signature>>,U32.is_ge(count,256),u => exhausted(List<&2,C.Signature>),u =>
        S.bind(List<&2,C.Signature>,List<&2,C.Signature>,signatures(tail,U32.add(count,1)),rest => Done{Con{signature,rest}}))

def typed(+types: List<&2,C.Datatype>, +token: S.Token, q: U32, type_id: U32) -> Result<S.Error,Unit>:
  S.bind(C.Datatype,Unit,G.type_at(types,type_id),definition => G.quantity(token,q,definition))

def parameters(params: List<&2,C.Parameter>, +types: List<&2,C.Datatype>, +count: U32) -> Result<S.Error,Unit>:
  match params:
    case Nil{}: Done{Unit{}}
    case Con{C.Parameter{token,q,type_id},+tail}:
      S.choose(Result<S.Error,Unit>,U32.is_ge(count,256),u => exhausted(Unit),u =>
        S.bind(Unit,Unit,typed(types,token,q,type_id),u => parameters(tail,types,U32.add(count,1))))

def field_kind(definition: C.Datatype, +data: Bool, q: U32) -> Result<S.Error,Unit>:
  match definition:
    case C.Datatype{name,child,ctors}: require(G.field_kind(data,q,child),"data-field-kind")

def fields(params: List<&2,C.Parameter>, +types: List<&2,C.Datatype>, +data: Bool, +seen: List<&2,S.Token>, +count: U32) -> Result<S.Error,Unit>:
  match params:
    case Nil{}: Done{Unit{}}
    case Con{C.Parameter{+token,+q,+type_id},+tail}:
      S.choose(Result<S.Error,Unit>,U32.is_ge(count,256),u => exhausted(Unit),u =>
        S.bind(Unit,Unit,require(Bool.not(G.named(seen,token)),"duplicate-field"),u =>
          S.bind(Unit,Unit,typed(types,token,q,type_id),u =>
            S.bind(C.Datatype,Unit,G.type_at(types,type_id),definition =>
              S.bind(Unit,Unit,field_kind(definition,data,q),u => fields(tail,types,data,Con{token,seen},U32.add(count,1)))))))

def constructors(ctors: List<&2,C.Constructor>, +types: List<&2,C.Datatype>, +data: Bool, +count: U32) -> Result<S.Error,Unit>:
  match ctors:
    case Nil{}: require(U32.is_ne(count,0),"empty-datatype")
    case Con{C.Constructor{token,params},+tail}:
      S.choose(Result<S.Error,Unit>,U32.is_ge(count,256),u => exhausted(Unit),u =>
        S.bind(Unit,Unit,fields(params,types,data,Nil{},0),u => constructors(tail,types,data,U32.add(count,1))))

def datatypes(pending: List<&2,C.Datatype>, +types: List<&2,C.Datatype>, +seen: List<&2,S.Token>, +count: U32) -> Result<S.Error,List<&2,S.Token>>:
  match pending:
    case Nil{}: Done{seen}
    case Con{C.Datatype{+token,data,ctors},+tail}:
      S.choose(Result<S.Error,List<&2,S.Token>>,U32.is_ge(count,256),u => exhausted(List<&2,S.Token>),u =>
        S.bind(Unit,List<&2,S.Token>,require(Bool.not(G.named(seen,token)),"duplicate-global"),u =>
          S.bind(Unit,List<&2,S.Token>,constructors(ctors,types,data,0),u => datatypes(tail,types,Con{token,seen},U32.add(count,1)))))

def declarations(sigs: List<&2,C.Signature>, +types: List<&2,C.Datatype>, +seen: List<&2,S.Token>, +count: U32) -> Result<S.Error,Unit>:
  match sigs:
    case Nil{}: Done{Unit{}}
    case Con{C.Signature{+token,params,type_id},+tail}:
      S.choose(Result<S.Error,Unit>,U32.is_ge(count,256),u => exhausted(Unit),u =>
        S.bind(Unit,Unit,require(Bool.not(G.named(seen,token)),"duplicate-global"),u =>
          S.bind(Unit,Unit,parameters(params,types,0),u =>
            S.bind(C.Datatype,Unit,G.type_at(types,type_id),definition => declarations(tail,types,Con{token,seen},U32.add(count,1))))))

def catalog(+types: List<&2,C.Datatype>, +sigs: List<&2,C.Signature>) -> Result<S.Error,C.Catalog>:
  S.bind(List<&2,S.Token>,C.Catalog,datatypes(types,types,Nil{},0),names =>
    S.bind(Unit,C.Catalog,G.unique_constructors(types,Nil{}),u =>
      S.bind(Unit,C.Catalog,declarations(sigs,types,names,0),u => Done{C.Catalog{types,sigs}})))

# Levels are lexical identities, not offsets: binders may be sparse, but a
# nested binder cannot reuse an in-scope identity. Alternatives may reuse it.
def fresh(bindings: List<&2,C.Binding>, +level: U32) -> Result<S.Error,Unit>:
  S.choose(Result<S.Error,Unit>,U32.is_ge(level,4096),u => exhausted(Unit),u =>
    require(Bool.not(E.contains(E.levels(bindings),level)),"binder-level"))

def extend(scope: E.Scope, +binding: C.Binding) -> Result<S.Error,E.Scope>:
  match scope binding:
    case E.Scope{+bindings,next,open,+live,+smaller} C.Binding{token,+level,q,type_id,param,known}:
      S.bind(Unit,E.Scope,fresh(bindings,level),u => Done{E.Scope{Con{binding,bindings},0,Nil{},live,smaller}})

def reference(binding: C.Binding, +token: S.Token, +type_id: U32, live: Bool) -> Result<S.Error,C.Checked>:
  match binding:
    case C.Binding{name,+level,+q,+actual,param,known}:
      S.bind(Unit,C.Checked,require(U32.is_eq(type_id,actual),"reference-type"),u =>
        E.occurrence(None{},token,level,q,actual,live))

def constant(params: List<&2,C.Parameter>, +token: S.Token, +type_id: U32, +tag: U32) -> Result<S.Error,C.Checked>:
  match params:
    case Nil{}: Done{C.Checked{C.Value{token,type_id,tag},type_id,Nil{}}}
    case _: internal(C.Checked,"constant-fields")

def field_binding(binding: C.Binding, parameter: C.Parameter, +parent: U32, +types: List<&2,C.Datatype>) -> Result<S.Error,Unit>:
  match binding parameter:
    case C.Binding{+token,level,+q,+type_id,True{},None{}} C.Parameter{name,+declared,actual}:
      S.bind(Unit,Unit,require(U32.is_eq(type_id,actual),"field-type"),u =>
        S.bind(Unit,Unit,require(Bool.or(U32.is_eq(q,P.quantity(declared,parent,1)),U32.is_eq(q,P.quantity(declared,parent,2))),"field-quantity"),u =>
          typed(types,token,q,type_id)))
    case _ _: internal(Unit,"field-binding")

def branch_fields(bindings: List<&2,C.Binding>, params: List<&2,C.Parameter>, +parent: U32, +types: List<&2,C.Datatype>, scope: E.Scope) -> Result<S.Error,E.Scope>:
  match bindings params:
    case Nil{} Nil{}: Done{scope}
    case Con{+binding,+tail} Con{parameter,+rest}:
      S.bind(Unit,E.Scope,field_binding(binding,parameter,parent,types),u =>
        S.bind(E.Scope,E.Scope,extend(scope,binding),bound => branch_fields(tail,rest,parent,types,bound)))
    case _ _: internal(E.Scope,"field-arity")

def descendants(scope: E.Scope, level: U32, fields: List<&2,C.Binding>) -> E.Scope:
  match scope:
    case E.Scope{bindings,next,open,live,smaller}:
      E.Scope{bindings,next,open,live,E.descendants(level,E.levels(fields),smaller)}

def opened(binding: C.Binding, +fields: List<&2,C.Binding>, params: List<&2,C.Parameter>, types: List<&2,C.Datatype>, scope: E.Scope) -> Result<S.Error,E.Scope>:
  match binding:
    case C.Binding{token,+level,q,type_id,param,known}:
      S.bind(E.Scope,E.Scope,branch_fields(fields,params,q,types,scope),bound => Done{descendants(bound,level,fields)})

def scrutinee(binding: C.Binding, +token: S.Token, live: Bool) -> Result<S.Error,C.Checked>:
  match binding:
    case C.Binding{name,+level,+q,+type_id,param,known}:
      S.bind(Unit,C.Checked,require(U32.is_ne(q,0),"erased-scrutinee"),u => E.occurrence(None{},token,level,q,type_id,live))

def complete(binding: C.Binding, types: List<&2,C.Datatype>, +seen: List<&2,U32>, +token: S.Token) -> Result<S.Error,C.Checked>:
  match binding:
    case C.Binding{name,level,q,type_id,param,known}:
      S.bind(C.Datatype,C.Checked,G.type_at(types,type_id),definition =>
        S.bind(Unit,C.Checked,K.complete_arms(definition,seen,token),u => Done{C.Checked{C.Sequence{Nil{}},0,Nil{}}}))

def arm_parameters(binding: C.Binding, tag: U32, types: List<&2,C.Datatype>) -> Result<S.Error,List<&2,C.Parameter>>:
  match binding:
    case C.Binding{token,level,q,type_id,param,known}: G.field_signature(G.ConstructorRef{type_id,tag},types)

def call_signature(signature: C.Signature, type_id: U32, next: List<&2,C.Parameter> -> Result<S.Error,C.Checked>) -> Result<S.Error,C.Checked>:
  match signature:
    case C.Signature{name,params,result}:
      S.bind(Unit,C.Checked,require(U32.is_eq(type_id,result),"call-type"),u => next(params))

def run(depth: Nat, mode: Mode, +catalog: C.Catalog, +current: U32, +scope: E.Scope) -> Result<S.Error,C.Checked>:
  match depth mode catalog scope:
    case 0n _ _ _: exhausted(C.Checked)
    case 1n+ n Expression{C.Value{+token,+type_id,+tag},+wanted} C.Catalog{types,sigs} _:
      S.bind(List<&2,C.Parameter>,C.Checked,G.field_signature(G.ConstructorRef{type_id,tag},types),params =>
        S.bind(C.Checked,C.Checked,constant(params,token,type_id,tag),value => K.expected(token,Some{wanted},value)))
    case 1n+ +n Expression{C.Construct{+token,+type_id,+tag,+params,+args},+wanted} C.Catalog{types,sigs} _:
      S.bind(List<&2,C.Parameter>,C.Checked,G.field_signature(G.ConstructorRef{type_id,tag},types),declared =>
        S.bind(Unit,C.Checked,require(parameters_equal(params,declared),"constructor-signature"),u =>
          S.bind(C.Checked,C.Checked,run(n,Arguments{args,params,token},catalog,current,scope),value =>
            S.bind(C.Checked,C.Checked,K.rebuilt(value,token,type_id,tag,params),checked => K.expected(token,Some{wanted},checked)))))
    case 1n+ n Expression{C.Reference{+token,level,+type_id},+wanted} _ E.Scope{bindings,next,open,live,smaller}:
      S.bind(C.Binding,C.Checked,E.find_level(bindings,level),binding =>
        S.bind(C.Checked,C.Checked,reference(binding,token,type_id,live),value => K.expected(token,Some{wanted},value)))
    case 1n+ +n Expression{C.Application{+token,+index,+type_id,+args},+wanted} C.Catalog{types,sigs} E.Scope{bindings,next,open,live,smaller}:
      S.bind(Unit,C.Checked,require(Bool.not(Bool.and(live,U32.is_gt(index,current))),"forward-live-call"),u =>
        S.bind(C.Signature,C.Checked,signature_at(sigs,index),signature =>
          call_signature(signature,type_id,params =>
            S.bind(C.Checked,C.Checked,run(n,Arguments{args,params,token},catalog,current,scope),value =>
              S.bind(C.Checked,C.Checked,K.call_result(value,token,index,type_id,current,scope),checked => K.expected(token,Some{wanted},checked))))))
    case 1n+ +n Expression{C.Let{+token,+level,+q,+type_id,+value,+body},+wanted} C.Catalog{types,sigs} _:
      S.bind(Unit,C.Checked,typed(types,token,q,type_id),u =>
        S.bind(E.Scope,C.Checked,extend(scope,C.Binding{token,level,q,type_id,False{},None{}}),+bound =>
          S.bind(C.Checked,C.Checked,run(n,Expression{value,type_id},catalog,current,E.live_scope(scope,q)),+initial =>
            S.bind(C.Checked,C.Checked,run(n,Expression{body,wanted},catalog,current,bound),checked => K.let_result(initial,checked,token,level,q)))))
    case 1n+ +n Expression{C.Case{+token,+level,+type_id,+arms},+wanted} _ E.Scope{bindings,next,open,+live,smaller}:
      S.bind(Unit,C.Checked,require(U32.is_eq(type_id,wanted),"case-type"),u =>
        S.bind(C.Binding,C.Checked,E.find_level(bindings,level),binding =>
          S.bind(C.Checked,C.Checked,scrutinee(binding,token,live),+inspected =>
            S.bind(C.Checked,C.Checked,run(n,Arms{arms,token,level,type_id,Nil{}},catalog,current,scope),branches => K.case_result(branches,inspected,token,level,Some{type_id})))))
    case 1n+ n Expression{C.Sequence{items},wanted} _ _: internal(C.Checked,"expression-sequence")
    case 1n+ n Expression{C.Branch{tag,fields,body},wanted} _ _: internal(C.Checked,"expression-branch")
    case 1n+ n Expression{other,wanted} _ _: Fail{S.Unsupported{"opt-core","term",S.At{0,0,0,0}}}
    case 1n+ n Arguments{Nil{},Nil{},token} _ _: Done{C.Checked{C.Sequence{Nil{}},0,Nil{}}}
    case 1n+ +n Arguments{Con{head,+tail},Con{C.Parameter{name,q,type_id},+rest},+token} _ _:
      S.bind(C.Checked,C.Checked,run(n,Expression{head,type_id},catalog,current,E.live_scope(scope,q)),checked =>
        S.bind(C.Checked,C.Checked,run(n,Arguments{tail,rest,token},catalog,current,scope),remaining => K.prepend_argument(checked,remaining,token)))
    case 1n+ n Arguments{terms,params,token} _ _: internal(C.Checked,"argument-arity")
    case 1n+ n Arms{Nil{},+token,level,wanted,+seen} C.Catalog{types,sigs} E.Scope{bindings,next,open,live,smaller}:
      S.bind(C.Binding,C.Checked,E.find_level(bindings,level),binding => complete(binding,types,seen,token))
    case 1n+ +n Arms{Con{C.Branch{+tag,+fields,+body},+tail},+token,+level,+wanted,+seen} C.Catalog{+types,sigs} E.Scope{bindings,next,open,live,smaller}:
      S.bind(Unit,C.Checked,require(Bool.not(E.contains(seen,tag)),"duplicate-arm"),u =>
        S.bind(C.Binding,C.Checked,E.find_level(bindings,level),+binding =>
          S.bind(List<&2,C.Parameter>,C.Checked,arm_parameters(binding,tag,types),params =>
            S.bind(E.Scope,C.Checked,opened(binding,fields,params,types,scope),bound =>
              S.bind(C.Checked,C.Checked,run(n,Expression{body,wanted},catalog,current,bound),checked =>
                S.bind(C.Checked,C.Checked,run(n,Arms{tail,token,level,wanted,Con{tag,seen}},catalog,current,scope),remaining => K.prepend_arm(tag,fields,checked,remaining)))))))
    case 1n+ n Arms{other,token,level,wanted,seen} _ _: internal(C.Checked,"arm-term")

def function(signature: C.Signature, body: C.Term, catalog: C.Catalog, index: U32, depth: Nat) -> Result<S.Error,Unit>:
  match signature:
    case C.Signature{token,params,result}:
      S.bind(C.Checked,Unit,run(depth,Expression{body,result},catalog,index,E.parameters(params,0,Nil{})),checked => Done{Unit{}})

def functions(pending: List<&2,C.Function>, +catalog: C.Catalog, +index: U32, +depth: Nat) -> Result<S.Error,Unit>:
  match pending:
    case Nil{}: Done{Unit{}}
    case Con{C.Function{signature,body},+tail}:
      S.bind(Unit,Unit,function(signature,body,catalog,index,depth),u => functions(tail,catalog,U32.add(index,1),depth))

def verify(depth: Nat, +book: C.Book) -> Result<S.Error,C.Book>:
  match depth book:
    case 0n _: exhausted(C.Book)
    case 1n+ +n C.Book{+types,+bodies}:
      result(C.Book,S.bind(List<&2,C.Signature>,C.Book,signatures(bodies,0),sigs =>
        S.bind(C.Catalog,C.Book,catalog(types,sigs),catalog =>
          S.bind(Unit,C.Book,functions(bodies,catalog,0,1n+n),u => Done{book}))))

def signature_equal(left: C.Signature, right: C.Signature) -> Bool:
  match left right:
    case C.Signature{name,params,result} C.Signature{other,args,actual}:
      Bool.and(String.eq(S.text(name),S.text(other)),Bool.and(parameters_equal(params,args),U32.is_eq(result,actual)))

def exports_equal(left: List<&2,C.Function>, right: List<&2,C.Function>) -> Bool:
  match left right:
    case Nil{} Nil{}: True{}
    case Con{C.Function{signature,body},tail} Con{C.Function{other,term},rest}:
      Bool.and(signature_equal(signature,other),exports_equal(tail,rest))
    case _ _: False{}

# Types are carried unchanged by the traversal. Check output bodies against
# their own catalog only after ordered input/export signatures agree.
def recheck(depth: Nat, types: List<&2,C.Datatype>, before: List<&2,C.Function>, +after: List<&2,C.Function>) -> Result<S.Error,C.Book>:
  S.bind(Unit,C.Book,require(exports_equal(before,after),"exports-changed"),u => verify(depth,C.Book{types,after}))

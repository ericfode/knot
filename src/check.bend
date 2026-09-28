import Base
import ./syntax.bend as S
import ./core.bend as C
import ./catalog.bend as G
import ./scope.bend as E
import ./patterns.bend as P
import ./literal-check.bend as L
import ./literal-base.bend as LB
import ./primitive-op.bend as R
import ./primitive.bend as O
import ./literal-matrix.bend as M
import ./literal-types.bend as T

type Mode is Data:
  Rebuild{term: C.Term}
  Matrix{plan: M.Plan, expected: U32}
  MatrixArms{plans: List<&2,M.Plan>, expected: U32}
  MatrixLeaves{plans: List<&2,M.Plan>, expected: U32}
  RebuildArguments{terms: List<&2,C.Term>, parameters: List<&2,C.Parameter>, token: S.Token}
  Expression{node: S.Node, expected: Maybe<&2,U32>}
  Arguments{nodes: List<&2,S.Node>, parameters: List<&2,C.Parameter>, token: S.Token}
  Arms{nodes: List<&2,S.Node>, token: S.Token, level: U32, expected: Maybe<&2,U32>}

def expected(+token: S.Token, wanted: Maybe<&2,U32>, +value: C.Checked) -> Result<S.Error,C.Checked>:
  match wanted value:
    case None{} _: Done{value}
    case Some{type_id} C.Checked{term,actual,uses}:
      S.choose(Result<S.Error,C.Checked>,U32.is_eq(type_id,actual),u => Done{value},u => C.invalid(C.Checked,"type-mismatch",token))

def enum_at(types: List<&2,C.Datatype>, +index: U32) -> Result<S.Error,C.Datatype>:
  match types:
    case Nil{}: C.internal(C.Datatype,"type-index")
    case Con{+head,+tail}:
      S.choose(Result<S.Error,C.Datatype>,U32.is_eq(index,0),u => Done{head},u => enum_at(tail,U32.sub(index,1)))

def annotation_id(reference: G.TypeRef) -> Result<S.Error,Maybe<&2,U32>>:
  match reference:
    case G.TypeRef{index,definition}: Done{Some{index}}

def annotation(types: List<&2,C.Datatype>, token: Maybe<&2,S.Token>) -> Result<S.Error,Maybe<&2,U32>>:
  match token:
    case None{}: Done{None{}}
    case Some{name}:
      S.bind(G.TypeRef,Maybe<&2,U32>,G.find_type(types,name,0),reference => annotation_id(reference))

def constant(reference: G.ConstructorRef, +token: S.Token, wanted: Maybe<&2,U32>) -> Result<S.Error,C.Checked>:
  match reference wanted:
    case G.ConstructorRef{+type_id,tag} Some{+target}:
      S.choose(Result<S.Error,C.Checked>,U32.is_eq(type_id,target),u => Done{C.Checked{C.Value{token,type_id,tag},type_id,Nil{}}},u => C.invalid(C.Checked,"type-mismatch",token))
    case _ None{}: C.invalid(C.Checked,"annotation-required",token)

def constructor_result(reference: G.ConstructorRef, +token: S.Token, wanted: Maybe<&2,U32>, params: List<&2,C.Parameter>, value: C.Checked) -> Result<S.Error,C.Checked>:
  match reference wanted value:
    case G.ConstructorRef{+type_id,tag} Some{target} C.Checked{C.Sequence{args},ignored,uses}:
      S.choose(Result<S.Error,C.Checked>,U32.is_eq(type_id,target),u =>
        Done{C.Checked{P.value(token,type_id,tag,params,args),type_id,uses}},u => C.invalid(C.Checked,"type-mismatch",token))
    case _ None{} _: C.invalid(C.Checked,"annotation-required",token)
    case _ _ _: C.internal(C.Checked,"constructor-arguments")

def constructor(+reference: G.ConstructorRef, +args: List<&2,S.Node>, +token: S.Token, +wanted: Maybe<&2,U32>, +params: List<&2,C.Parameter>, next: Unit -> Result<S.Error,C.Checked>) -> Result<S.Error,C.Checked>:
  match args params:
    case Nil{} Nil{}: constant(reference,token,wanted)
    case _ _:
      S.choose(Result<S.Error,C.Checked>,Nat.is_eq(List.length(&2,S.Node,args),List.length(&2,C.Parameter,params)),u =>
        S.bind(C.Checked,C.Checked,next(Unit{}),value => constructor_result(reference,token,wanted,params,value)),u => C.invalid(C.Checked,"constructor-arity",token))

def variable(+binding: C.Binding, +token: S.Token, +scope: E.Scope, next: C.Term -> Result<S.Error,C.Checked>) -> Result<S.Error,C.Checked>:
  match binding:
    case C.Binding{name,level,q,type_id,param,Some{C.Construct{origin,typ,tag,params,args}}}:
      next(C.Construct{origin,typ,tag,params,args})
    case _: E.reference(binding,token,scope)

def bound(bindings: List<&2,C.Binding>, +token: S.Token) -> Bool:
  match bindings:
    case Nil{}: False{}
    case Con{C.Binding{name,level,q,type_id,param,known},tail}:
      Bool.or(String.eq(S.text(name),S.text(token)),bound(tail,token))

def callable(reference: G.FunctionRef, +token: S.Token, +current: U32, scope: E.Scope) -> Result<S.Error,G.FunctionRef>:
  match reference scope:
    case G.FunctionRef{+index,+sig} E.Scope{bindings,next,from,live,smaller}:
      S.choose(Result<S.Error,G.FunctionRef>,bound(bindings,token),u => C.invalid(G.FunctionRef,"not-callable",token),u =>
        S.choose(Result<S.Error,G.FunctionRef>,Bool.and(live,U32.is_gt(index,current)),u => C.invalid(G.FunctionRef,"forward-live-call",token),u => Done{G.FunctionRef{index,sig}}))

def call_result(value: C.Checked, +token: S.Token, +index: U32, +result: U32, current: U32, scope: E.Scope) -> Result<S.Error,C.Checked>:
  match value scope:
    case C.Checked{C.Sequence{+items},ignored,+uses} E.Scope{bindings,next,open,live,smaller}:
      S.choose(Result<S.Error,C.Checked>,Bool.and(U32.is_eq(index,current),Bool.not(E.descends(items,smaller))),u =>
        C.unsupported(C.Checked,"recursive-call",token),u => Done{C.Checked{C.Application{token,index,result,items},result,uses}})
    case _ _: C.internal(C.Checked,"arguments-result")

def prepend_argument(head: C.Checked, tail: C.Checked, token: S.Token) -> Result<S.Error,C.Checked>:
  match head tail:
    case C.Checked{+term,type_id,uses} C.Checked{C.Sequence{+items},ignored,rest}:
      S.bind(List<&2,U32>,C.Checked,E.sequential(uses,rest,token),merged => Done{C.Checked{C.Sequence{Con{term,items}},0,merged}})
    case _ _: C.internal(C.Checked,"argument-list")

def let_result(value: C.Checked, body: C.Checked, +token: S.Token, +level: U32, q: U32) -> Result<S.Error,C.Checked>:
  match value body:
    case C.Checked{+initial,+type_id,uses} C.Checked{+result,+result_type,body_uses}:
      S.bind(List<&2,U32>,C.Checked,E.sequential(uses,E.remove(body_uses,level),token),merged =>
        Done{C.Checked{C.Let{token,level,q,type_id,initial,result},result_type,merged}})

def pattern_arity(+reference: G.ConstructorRef, args: List<&2,S.Node>, +token: S.Token, params: List<&2,C.Parameter>) -> Result<S.Error,G.ConstructorRef>:
  S.choose(Result<S.Error,G.ConstructorRef>,Nat.is_eq(List.length(&2,S.Node,args),List.length(&2,C.Parameter,params)),u => Done{reference},u => C.invalid(G.ConstructorRef,"pattern-arity",token))

def pattern(node: S.Node, +types: List<&2,C.Datatype>) -> Result<S.Error,G.ConstructorRef>:
  match node:
    case S.Constructor{+token,+args}:
      S.bind(G.ConstructorRef,G.ConstructorRef,T.constructor(types,token),+reference =>
        S.bind(List<&2,C.Parameter>,G.ConstructorRef,G.field_signature(reference,types),params => pattern_arity(reference,args,token,params)))
    case S.Variable{token}: C.unsupported(G.ConstructorRef,"variable-pattern",token)
    case S.Promotion{token}: C.unsupported(G.ConstructorRef,"variable-pattern",token)
    case S.Call{token,args}: C.invalid(G.ConstructorRef,"pattern-form",token)
    case _: C.internal(G.ConstructorRef,"pattern-node")

def pattern_id(reference: G.ConstructorRef, +type_id: U32, +seen: List<&2,U32>, +token: S.Token) -> Result<S.Error,U32>:
  match reference:
    case G.ConstructorRef{actual,+tag}:
      S.choose(Result<S.Error,U32>,U32.is_eq(actual,type_id),u =>
        S.choose(Result<S.Error,U32>,E.contains(seen,tag),u => C.unsupported(U32,"duplicate-arm",token),u => Done{tag}),u => C.invalid(U32,"pattern-type",token))

def complete_arms(definition: C.Datatype, seen: List<&2,U32>, +token: S.Token) -> Result<S.Error,Unit>:
  match definition:
    case C.Datatype{name,data,tokens}:
      S.choose(Result<S.Error,Unit>,Nat.is_eq(List.length(&2,C.Constructor,tokens),List.length(&2,U32,seen)),u => Done{Unit{}},u => C.invalid(Unit,"missing-arm",token))

def patterns(nodes: List<&2,S.Node>, +types: List<&2,C.Datatype>, +type_id: U32, +seen: List<&2,U32>, +token: S.Token) -> Result<S.Error,Unit>:
  match nodes:
    case Nil{}:
      S.bind(C.Datatype,Unit,enum_at(types,type_id),definition => complete_arms(definition,seen,token))
    case Con{S.Arm{+arm,pat,body},+tail}:
      S.bind(G.ConstructorRef,Unit,pattern(pat,types),reference =>
        S.bind(U32,Unit,pattern_id(reference,type_id,seen,arm),tag => patterns(tail,types,type_id,Con{tag,seen},token)))
    case _: C.internal(Unit,"arm-node")

def prepend_arm(tag: U32, +fields: List<&2,C.Binding>, head: C.Checked, tail: C.Checked) -> Result<S.Error,C.Checked>:
  match head tail:
    case C.Checked{body,type_id,uses} C.Checked{C.Sequence{items},ignored,rest}:
      Done{C.Checked{C.Sequence{Con{C.Branch{tag,fields,body},items}},0,E.alternatives(E.remove_fields(fields,uses),rest)}}
    case _ _: C.internal(C.Checked,"arm-list")

def case_result(branches: C.Checked, inspected: C.Checked, +token: S.Token, level: U32, wanted: Maybe<&2,U32>) -> Result<S.Error,C.Checked>:
  match branches inspected wanted:
    case C.Checked{C.Sequence{+items},ignored,uses} C.Checked{term,source_type,scrutinee_uses} Some{+type_id}:
      S.bind(List<&2,U32>,C.Checked,E.sequential(scrutinee_uses,uses,token),merged => Done{C.Checked{C.Case{token,level,type_id,items},type_id,merged}})
    case _ _ None{}: C.internal(C.Checked,"uninferred-match")
    case _ _ _: C.internal(C.Checked,"match-result")

def call_body(reference: G.FunctionRef, +token: S.Token, +wanted: Maybe<&2,U32>, current: U32, scope: E.Scope, next: List<&2,C.Parameter> -> Result<S.Error,C.Checked>) -> Result<S.Error,C.Checked>:
  match reference:
    case G.FunctionRef{+index,C.Signature{name,params,+result}}:
      S.bind(C.Checked,C.Checked,next(params),value =>
        S.bind(C.Checked,C.Checked,call_result(value,token,index,result,current,scope),checked => expected(token,wanted,checked)))

def binding_body(initial: C.Checked, +token: S.Token, +q: U32, types: List<&2,C.Datatype>, +scope: E.Scope, next: E.Scope -> Result<S.Error,C.Checked>) -> Result<S.Error,C.Checked>:
  match initial:
    case C.Checked{term,+type_id,uses}:
      S.bind(C.Datatype,C.Checked,enum_at(types,type_id),definition =>
        S.bind(Unit,C.Checked,G.quantity(token,q,definition),u => next(E.extend(scope,token,q,type_id))))

def match_body(binding: C.Binding, +token: S.Token, +arms: List<&2,S.Node>, types: List<&2,C.Datatype>, +scope: E.Scope, +wanted: Maybe<&2,U32>, next: U32 -> Result<S.Error,C.Checked>) -> Result<S.Error,C.Checked>:
  match binding wanted:
    case C.Binding{+name,+level,+q,+type_id,+param,+known} Some{target}:
      S.bind(Unit,C.Checked,patterns(arms,types,type_id,Nil{},token),u =>
        S.bind(C.Checked,C.Checked,E.reference(C.Binding{name,level,q,type_id,param,known},token,scope),inspected =>
          S.bind(C.Checked,C.Checked,next(level),branches => case_result(branches,inspected,token,level,wanted))))
    case _ None{}: C.invalid(C.Checked,"annotation-required",token)

def arm_body(reference: G.ConstructorRef, next: U32 -> Result<S.Error,C.Checked>) -> Result<S.Error,C.Checked>:
  match reference:
    case G.ConstructorRef{type_id,tag}: next(tag)

def arm_scope(fields: P.Fields, next: E.Scope -> List<&2,C.Binding> -> Result<S.Error,C.Checked>) -> Result<S.Error,C.Checked>:
  match fields:
    case P.Fields{scope,bindings,args}: next(scope,bindings)

def rebuilt(value: C.Checked, token: S.Token, +type_id: U32, tag: U32, params: List<&2,C.Parameter>) -> Result<S.Error,C.Checked>:
  match value:
    case C.Checked{C.Sequence{args},ignored,uses}: Done{C.Checked{P.value(token,type_id,tag,params,args),type_id,uses}}
    case _: C.internal(C.Checked,"refined-arguments")

def literal_constructor(value: C.Checked, types: List<&2,C.Datatype>) -> Result<S.Error,C.Checked>:
  match value:
    case C.Checked{term,+type_id,uses}: Done{C.Checked{L.constructor(term,types,type_id),type_id,uses}}

def intrinsic_type(reference: G.TypeRef, next: U32 -> Result<S.Error,C.Checked>) -> Result<S.Error,C.Checked>:
  match reference:
    case G.TypeRef{id,definition}: next(id)

def matrix_wanted(wanted: Maybe<&2,U32>, token: S.Token, next: U32 -> Result<S.Error,C.Checked>) -> Result<S.Error,C.Checked>:
  match wanted:
    case None{}: C.invalid(C.Checked,"annotation-required",token)
    case Some{target}: next(target)

def matrix_consumed(body: C.Checked, +binding: C.Binding, +scope: E.Scope) -> Result<S.Error,C.Checked>:
  match binding:
    case C.Binding{+token,+level,q,typ,param,known}:
      S.bind(C.Checked,C.Checked,E.reference(binding,token,scope),inspected => M.consumed(body,inspected,level,token))

def matrix_case(value: C.Checked, column: C.Binding, +target: U32) -> Result<S.Error,C.Checked>:
  match value column:
    case C.Checked{C.Sequence{arms},ignored,uses} C.Binding{token,level,q,typ,param,known}:
      Done{C.Checked{C.Case{token,level,target,arms},target,uses}}
    case _ _: C.internal(C.Checked,"matrix-case")

def matrix_default(value: C.Checked) -> Result<S.Error,C.Checked>:
  match value:
    case C.Checked{term,typ,uses}: Done{C.Checked{C.Sequence{[C.Default{term}]},0,uses}}

def matrix_retained(first: C.Checked, rest: C.Checked) -> Result<S.Error,C.Checked>:
  Done{first}

def run(fuel: Nat, mode: Mode, +catalog: C.Catalog, +current: U32, +scope: E.Scope) -> Result<S.Error,C.Checked>:
  match fuel mode catalog scope:
    case 0n _ _ _: Fail{S.Exhausted{"check",S.At{0,0,0,0}}}
    case 1n+ +n Matrix{M.MatrixLeaf{bound,body},target} _ _:
      run(n,Expression{body,Some{target}},catalog,current,bound)
    case 1n+ +n Matrix{M.MLeaves{plans},target} _ _:
      run(n,MatrixLeaves{plans,target},catalog,current,scope)
    case 1n+ +n Matrix{M.MCase{+column,arms},+target} _ _:
      S.bind(C.Checked,C.Checked,run(n,MatrixArms{arms,target},catalog,current,scope),value => matrix_case(value,column,target))
    case 1n+ +n Matrix{plan,target} _ _: C.internal(C.Checked,"matrix-plan")
    case 1n+ +n MatrixArms{Nil{},target} _ _: Done{C.Checked{C.Sequence{Nil{}},0,Nil{}}}
    case 1n+ +n MatrixArms{Con{M.MBranch{+tag,+fields,body},+tail},+target} _ _:
      S.bind(C.Checked,C.Checked,run(n,Matrix{body,target},catalog,current,scope),head =>
        S.bind(C.Checked,C.Checked,run(n,MatrixArms{tail,target},catalog,current,scope),rest => prepend_arm(tag,fields,head,rest)))
    case 1n+ +n MatrixArms{Con{M.MDefault{body},Nil{}},target} _ _:
      S.bind(C.Checked,C.Checked,run(n,Matrix{body,target},catalog,current,scope),matrix_default)
    case 1n+ +n MatrixArms{plans,target} _ _: C.internal(C.Checked,"matrix-arm")
    case 1n+ +n MatrixLeaves{Nil{},target} _ _: Done{C.Checked{C.Sequence{Nil{}},target,Nil{}}}
    case 1n+ +n MatrixLeaves{Con{head,+tail},+target} _ _:
      S.bind(C.Checked,C.Checked,run(n,Matrix{head,target},catalog,current,scope),first =>
        S.bind(C.Checked,C.Checked,run(n,MatrixLeaves{tail,target},catalog,current,scope),rest => matrix_retained(first,rest)))
    case 1n+ +n Expression{S.Literal{+token,kind,number,text},+wanted} C.Catalog{types,sigs} _:
      S.bind(C.Checked,C.Checked,L.literal(token,kind,number,text,types),value => expected(token,wanted,value))
    case 1n+ +n Expression{S.Offset{+token,count,tail},wanted} _ _:
      run(n,Expression{S.Intrinsic{token,R.NAdd{},[S.Literal{token,1,count,Nil{}},tail]},wanted},catalog,current,scope)
    case 1n+ +n Expression{S.Intrinsic{+token,+op,+args},+wanted} C.Catalog{+types,sigs} _:
      S.bind(G.TypeRef,C.Checked,G.find_type(types,LB.token(O.output(op)),0),reference =>
        intrinsic_type(reference,+id =>
          S.bind(List<&2,C.Parameter>,C.Checked,L.arguments(op,types),params =>
            S.bind(C.Checked,C.Checked,run(n,Arguments{args,params,token},catalog,current,scope),arguments =>
              S.bind(C.Checked,C.Checked,L.result(arguments,token,id,op),value => expected(token,wanted,value))))))
    case 1n+ +n Expression{S.Variable{+token},+wanted} _ _:
      S.bind(C.Binding,C.Checked,E.lookup(scope,token),binding =>
        S.bind(C.Checked,C.Checked,variable(binding,token,scope,term => run(n,Rebuild{term},catalog,current,scope)),value => expected(token,wanted,value)))
    case 1n+ +n Expression{S.Constructor{+token,+args},+wanted} C.Catalog{+types,sigs} _:
      S.bind(G.ConstructorRef,C.Checked,T.constructor(types,token),+reference =>
        S.bind(List<&2,C.Parameter>,C.Checked,G.field_signature(reference,types),+params =>
          S.bind(C.Checked,C.Checked,constructor(reference,args,token,wanted,params,u => run(n,Arguments{args,params,token},catalog,current,scope)),value => literal_constructor(value,types))))
    case 1n+ +n Expression{S.Call{+token,+args},+wanted} C.Catalog{types,sigs} _:
      S.bind(G.FunctionRef,C.Checked,G.find_function(sigs,token,0),reference =>
        S.bind(G.FunctionRef,C.Checked,callable(reference,token,current,scope),call =>
          call_body(call,token,wanted,current,scope,params => run(n,Arguments{args,params,token},catalog,current,scope))))
    case 1n+ +n Expression{S.Binding{+token,+q,ann,+value,+body},+wanted} C.Catalog{+types,sigs} E.Scope{bindings,+next,from,live,smaller}:
      S.choose(Result<S.Error,C.Checked>,U32.is_eq(next,4096),u => C.exhausted(C.Checked,token),u =>
        S.bind(Maybe<&2,U32>,C.Checked,annotation(types,ann),target =>
          S.bind(C.Checked,C.Checked,run(n,Expression{value,target},catalog,current,E.live_scope(scope,q)),+initial =>
            binding_body(initial,token,q,types,scope,extended =>
              S.bind(C.Checked,C.Checked,run(n,Expression{body,wanted},catalog,current,extended),checked => let_result(initial,checked,token,next,q))))))
    case 1n+ +n Expression{S.Match{+token,value,+arms},+wanted} C.Catalog{+types,sigs} _:
      S.bind(C.Binding,C.Checked,E.scrutinee(value,scope),+binding =>
        S.choose(Result<S.Error,C.Checked>,M.enabled(types,binding),u =>
          matrix_wanted(wanted,token,target =>
            S.bind(M.Plan,C.Checked,M.compile(4096n,binding,arms,types,scope),plan =>
              S.bind(C.Checked,C.Checked,run(n,Matrix{plan,target},catalog,current,scope),body => matrix_consumed(body,binding,scope)))),u =>
          match_body(binding,token,arms,types,scope,wanted,level =>
            run(n,Arms{arms,token,level,wanted},catalog,current,scope))))
    case 1n+ +n Expression{node,wanted} _ _: C.internal(C.Checked,"expression-node")
    case 1n+ +n Arguments{Nil{},Nil{},token} _ _:
      Done{C.Checked{C.Sequence{Nil{}},0,Nil{}}}
    case 1n+ +n Arguments{Con{head,+tail},Con{C.Parameter{name,q,type_id},+rest},+token} _ _:
      S.bind(C.Checked,C.Checked,run(n,Expression{head,Some{type_id}},catalog,current,E.live_scope(scope,q)),checked =>
        S.bind(C.Checked,C.Checked,run(n,Arguments{tail,rest,token},catalog,current,scope),remaining => prepend_argument(checked,remaining,token)))
    case 1n+ +n Arguments{nodes,params,token} _ _: C.invalid(C.Checked,"call-arity",token)
    case 1n+ +n Arms{Nil{},token,level,wanted} _ _:
      Done{C.Checked{C.Sequence{Nil{}},0,Nil{}}}
    case 1n+ +n Arms{Con{S.Arm{arm,+pat,+body},+tail},+token,+level,+wanted} C.Catalog{+types,sigs} _:
      S.bind(G.ConstructorRef,C.Checked,pattern(pat,types),+reference =>
        arm_body(reference,+tag =>
          S.bind(P.Fields,C.Checked,P.branch(scope,level,reference,pat,types),opened =>
            arm_scope(opened,bound => +fields =>
              S.bind(C.Checked,C.Checked,run(n,Expression{body,wanted},catalog,current,bound),checked =>
                S.bind(C.Checked,C.Checked,run(n,Arms{tail,token,level,wanted},catalog,current,scope),remaining => prepend_arm(tag,fields,checked,remaining)))))))
    case 1n+ +n Arms{nodes,token,level,wanted} _ _: C.internal(C.Checked,"arm-node")
    case 1n+ +n Rebuild{C.Value{token,+type_id,tag}} _ _:
      Done{C.Checked{C.Value{token,type_id,tag},type_id,Nil{}}}
    case 1n+ +n Rebuild{C.Reference{+token,level,type_id}} _ E.Scope{bindings,next,open,live,smaller}:
      S.bind(C.Binding,C.Checked,E.find_level(bindings,level),binding =>
        variable(binding,token,scope,term => run(n,Rebuild{term},catalog,current,scope)))
    case 1n+ +n Rebuild{C.Construct{+token,+type_id,+tag,+params,args}} _ _:
      S.bind(C.Checked,C.Checked,run(n,RebuildArguments{args,params,token},catalog,current,scope),value => rebuilt(value,token,type_id,tag,params))
    case 1n+ +n Rebuild{other} _ _: C.internal(C.Checked,"refinement-node")
    case 1n+ +n RebuildArguments{Nil{},Nil{},token} _ _:
      Done{C.Checked{C.Sequence{Nil{}},0,Nil{}}}
    case 1n+ +n RebuildArguments{Con{head,+tail},Con{C.Parameter{name,q,type_id},+rest},+token} _ _:
      S.bind(C.Checked,C.Checked,run(n,Rebuild{head},catalog,current,E.live_scope(scope,q)),checked =>
        S.bind(C.Checked,C.Checked,run(n,RebuildArguments{tail,rest,token},catalog,current,scope),remaining => prepend_argument(checked,remaining,token)))
    case 1n+ +n RebuildArguments{terms,params,token} _ _: C.internal(C.Checked,"refinement-arity")

def checked_function(signature: C.Signature, checked: C.Checked) -> C.Function:
  match checked:
    case C.Checked{term,type_id,uses}: C.Function{signature,term}

def function_body(+signature: C.Signature, body: S.Node, +catalog: C.Catalog, index: U32, depth: Nat) -> Result<S.Error,C.Function>:
  match signature:
    case C.Signature{name,params,result}:
      S.bind(C.Checked,C.Function,run(depth,Expression{body,Some{result}},catalog,index,E.parameters(params,0,Nil{})),checked => Done{checked_function(signature,checked)})

def functions(nodes: List<&2,S.Node>, +sigs: List<&2,C.Signature>, +catalog: C.Catalog, +index: U32, +depth: Nat) -> Result<S.Error,List<&2,C.Function>>:
  match nodes:
    case Nil{}: Done{Nil{}}
    case Con{S.Datatype{name,data,ctors},tail}: functions(tail,sigs,catalog,index,depth)
    case Con{S.Function{name,params,result,+body},+tail}:
      match sigs:
        case Nil{}: C.internal(List<&2,C.Function>,"signature-alignment")
        case Con{signature,+rest}:
          S.bind(C.Function,List<&2,C.Function>,function_body(signature,body,catalog,index,depth),head =>
            S.bind(List<&2,C.Function>,List<&2,C.Function>,functions(tail,rest,catalog,U32.add(index,1),depth),remaining => Done{Con{head,remaining}}))
    case _: C.internal(List<&2,C.Function>,"function-node")

# The enum emitter gates its whole book here until owned field storage lands.
# Structural checking and independent evaluation precede that capability gate.
def enum_constructors(ctors: List<&2,C.Constructor>) -> Result<S.Error,Unit>:
  match ctors:
    case Nil{}: Done{Unit{}}
    case Con{C.Constructor{token,Nil{}},tail}: enum_constructors(tail)
    case Con{C.Constructor{token,Con{head,tail}},rest}:
      C.unsupported(Unit,"constructor-fields",token)

def enum_profile(types: List<&2,C.Datatype>) -> Result<S.Error,Unit>:
  match types:
    case Nil{}: Done{Unit{}}
    case Con{C.Datatype{token,data,ctors},tail}:
      S.bind(Unit,Unit,enum_constructors(ctors),u => enum_profile(tail))

def resolved(+catalog: C.Catalog, nodes: List<&2,S.Node>, depth: Nat) -> Result<S.Error,C.Book>:
  match catalog:
    case C.Catalog{+types,sigs}:
      S.bind(List<&2,C.Function>,C.Book,functions(nodes,sigs,catalog,0,depth),bodies => Done{C.Book{types,bodies}})

def check(depth: Nat, root: S.Node) -> Result<S.Error,C.Book>:
  match depth root:
    case 0n _: Fail{S.Exhausted{"check",S.At{0,0,0,0}}}
    case 1n+ +n S.Sequence{+nodes}:
      S.bind(C.Catalog,C.Book,G.catalog(S.Sequence{nodes}),catalog => resolved(catalog,nodes,1n+n))
    case _ _: C.internal(C.Book,"root-node")

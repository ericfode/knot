import Base
import ./syntax.bend as S
import ./core.bend as C
import ./catalog.bend as G
import ./scope.bend as E
import ./patterns.bend as P

# Rows stay in source order. Each constructor splits a positive matrix from
# its remainder; a default retains the live scrutinee, even at the empty type.
def items(node: S.Node) -> List<&2,S.Node>:
  match node:
    case S.Sequence{nodes}: nodes
    case _: [node]

def flat_fields(nodes: List<&2,S.Node>) -> Bool:
  match nodes:
    case Nil{}: True{}
    case Con{S.Variable{token},tail}: flat_fields(tail)
    case Con{S.Promotion{token},tail}: flat_fields(tail)
    case _: False{}

def named(tokens: List<&2,S.Token>, +token: S.Token) -> Bool:
  match tokens:
    case Nil{}: False{}
    case Con{head,tail}: Bool.or(String.eq(S.text(head),S.text(token)),named(tail,token))

def flat_rows(rows: List<&2,S.Node>, +seen: List<&2,S.Token>) -> Bool:
  match rows:
    case Nil{}: True{}
    case Con{S.Arm{arm,S.Constructor{+token,fields},body},tail}:
      Bool.and(flat_fields(fields),Bool.and(Bool.not(named(seen,token)),flat_rows(tail,Con{token,seen})))
    case _: False{}

def flat(value: S.Node, rows: List<&2,S.Node>) -> Bool:
  match value:
    case S.Sequence{nodes}: False{}
    case _: flat_rows(rows,Nil{})

def binder(+token: S.Token, +types: List<&2,C.Datatype>) -> Result<S.Error,Unit>:
  S.choose(Result<S.Error,Unit>,G.constructor_before(types,token),u =>
    C.invalid(Unit,"constructor-pattern-binder",token),u => Done{Unit{}})

# Validate source patterns, including unreachable rows, before selecting bodies.
def validate(fuel: Nat, node: S.Node, +types: List<&2,C.Datatype>) -> Result<S.Error,Unit>:
  match fuel node:
    case 0n _: Fail{S.Exhausted{"check",S.At{0,0,0,0}}}
    case 1n+n S.Variable{token}: binder(token,types)
    case 1n+n S.Promotion{token}: binder(token,types)
    case 1n+ +n S.Constructor{+token,+args}:
      S.bind(G.ConstructorRef,Unit,G.pattern_constructor(types,token),reference =>
        S.bind(List<&2,C.Parameter>,Unit,G.field_signature(reference,types),params =>
          S.choose(Result<S.Error,Unit>,Nat.is_eq(List.length(&2,S.Node,args),List.length(&2,C.Parameter,params)),u =>
            validate(n,S.Sequence{args},types),u => C.invalid(Unit,"pattern-arity",token))))
    case 1n+n S.Call{token,args}: C.invalid(Unit,"pattern-form",token)
    case 1n+n S.Sequence{Nil{}}: Done{Unit{}}
    case 1n+ +n S.Sequence{Con{head,+tail}}:
      S.bind(Unit,Unit,validate(n,head,types),u => validate(n,S.Sequence{tail},types))
    case _ _: C.internal(Unit,"matrix-pattern")

def prepare(fuel: Nat, rows: List<&2,S.Node>, +width: Nat, +types: List<&2,C.Datatype>) -> Result<S.Error,List<&2,S.Node>>:
  match fuel rows:
    case 0n _: Fail{S.Exhausted{"check",S.At{0,0,0,0}}}
    case 1n+n Nil{}: Done{Nil{}}
    case 1n+ +n Con{S.Arm{+token,+pattern,+body},+tail}:
      S.choose(Result<S.Error,List<&2,S.Node>>,Nat.is_eq(List.length(&2,S.Node,items(pattern)),width),u =>
        S.bind(Unit,List<&2,S.Node>,validate(n,pattern,types),u =>
          S.bind(List<&2,S.Node>,List<&2,S.Node>,prepare(n,tail,width,types),rest =>
            Done{Con{S.Arm{token,S.Sequence{items(pattern)},body},rest}})),u =>
        C.invalid(List<&2,S.Node>,"pattern-arity",token))
    case _ _: C.internal(List<&2,S.Node>,"matrix-row")

def start(fuel: Nat, token: S.Token, +value: S.Node, rows: List<&2,S.Node>, types: List<&2,C.Datatype>) -> Result<S.Error,S.Node>:
  S.bind(List<&2,S.Node>,S.Node,prepare(fuel,rows,List.length(&2,S.Node,items(value)),types),ready =>
    Done{S.Matrix{token,items(value),ready,4096}})

# Pending aliases are installed in binder order at a leaf. Numeric targets keep
# simultaneous columns distinct even when their names shadow one another.
def bind_body(body: S.Node, +token: S.Token, +level: U32, +mark: U32) -> S.Node:
  match body:
    case S.Alias{name,id,q,rest}: S.Alias{name,id,q,bind_body(rest,token,level,mark)}
    case _: S.Alias{token,level,mark,body}

def mark(rows: List<&2,S.Node>) -> U32:
  match rows:
    case Nil{}: 1
    case Con{S.Arm{token,S.Sequence{Con{S.Promotion{name},rest}},body},tail}: 2
    case Con{head,tail}: mark(tail)

def constructors(rows: List<&2,S.Node>, +seen: List<&2,S.Token>) -> List<&2,S.Token>:
  match rows:
    case Nil{}: Nil{}
    case Con{S.Arm{arm,S.Sequence{Con{S.Constructor{+token,args},rest}},body},+tail}:
      S.choose(List<&2,S.Token>,named(seen,token),u => constructors(tail,seen),u =>
        Con{token,constructors(tail,Con{token,seen})})
    case Con{head,tail}: constructors(tail,seen)

def declared(ctors: List<&2,C.Constructor>) -> List<&2,S.Token>:
  match ctors:
    case Nil{}: Nil{}
    case Con{C.Constructor{token,fields},tail}: Con{token,declared(tail)}

def fresh(params: List<&2,C.Parameter>, +level: U32, +at: S.At) -> List<&2,S.Node>:
  match params:
    case Nil{}: Nil{}
    case Con{head,tail}:
      Con{S.Variable{S.Token{String.append("$matrix",U32.show(level)),at}},fresh(tail,U32.add(level,1),at)}

def specialize(rows: List<&2,S.Node>, +ctor: S.Token, +fields: List<&2,S.Node>, +level: U32) -> List<&2,S.Node>:
  match rows:
    case Nil{}: Nil{}
    case Con{S.Arm{+arm,S.Sequence{Con{S.Constructor{token,+args},+rest}},+body},+tail}:
      S.choose(List<&2,S.Node>,String.eq(S.text(token),S.text(ctor)),u =>
        Con{S.Arm{arm,S.Sequence{List.append(&2,S.Node,args,rest)},body},specialize(tail,ctor,fields,level)},u =>
        specialize(tail,ctor,fields,level))
    case Con{S.Arm{arm,S.Sequence{Con{S.Variable{token},rest}},body},tail}:
      Con{S.Arm{arm,S.Sequence{List.append(&2,S.Node,fields,rest)},bind_body(body,token,level,1)},specialize(tail,ctor,fields,level)}
    case Con{S.Arm{arm,S.Sequence{Con{S.Promotion{token},rest}},body},tail}:
      Con{S.Arm{arm,S.Sequence{List.append(&2,S.Node,fields,rest)},bind_body(body,token,level,2)},specialize(tail,ctor,fields,level)}
    case Con{head,tail}: specialize(tail,ctor,fields,level)

def default_rows(rows: List<&2,S.Node>, +level: U32) -> List<&2,S.Node>:
  match rows:
    case Nil{}: Nil{}
    case Con{S.Arm{arm,S.Sequence{Con{S.Variable{token},rest}},body},tail}:
      Con{S.Arm{arm,S.Sequence{rest},bind_body(body,token,level,1)},default_rows(tail,level)}
    case Con{S.Arm{arm,S.Sequence{Con{S.Promotion{token},rest}},body},tail}:
      Con{S.Arm{arm,S.Sequence{rest},bind_body(body,token,level,2)},default_rows(tail,level)}
    case Con{head,tail}: default_rows(tail,level)

# A variable column binds without inspecting or closing the ordered frontier.
def variable_column(+binding: C.Binding, +scope: E.Scope, +token: S.Token) -> Result<S.Error,C.Binding>:
  match binding scope:
    case C.Binding{name,level,q,type_id,param,None{}} E.Scope{bindings,next,open,live,smaller}:
      S.choose(Result<S.Error,C.Binding>,S.choose(Bool,param,u => E.contains(open,level),u => U32.is_eq(U32.add(level,1),next)),u => Done{binding},u =>
        C.invalid(C.Binding,"unmatchable-binder",token))
    case C.Binding{name,level,q,type_id,param,Some{C.Reference{a,b,c}}} _:
      C.unsupported(C.Binding,"default-scrutinee",token)
    case C.Binding{name,level,q,type_id,param,Some{C.Case{a,b,c,Nil{}}}} _:
      C.unsupported(C.Binding,"default-scrutinee",token)
    case _ _: C.invalid(C.Binding,"already-matched",token)

def promote(token: S.Token, level: U32, q: U32, +body: S.Node) -> S.Node:
  S.choose(S.Node,U32.is_eq(q,2),u => S.Alias{token,level,2,body},u => body)

def remaining(tokens: List<&2,S.Token>, +ctor: S.Token) -> List<&2,S.Token>:
  match tokens:
    case Nil{}: Nil{}
    case Con{+head,+tail}:
      S.choose(List<&2,S.Token>,S.matches(head,S.text(ctor)),u => remaining(tail,ctor),u => Con{head,remaining(tail,ctor)})

def without(rows: List<&2,S.Node>, +ctor: S.Token) -> List<&2,S.Node>:
  match rows:
    case Nil{}: Nil{}
    case Con{S.Arm{+arm,S.Sequence{Con{S.Constructor{+token,+args},+rest}},+body},+tail}:
      S.choose(List<&2,S.Node>,S.matches(token,S.text(ctor)),u => without(tail,ctor),u =>
        Con{S.Arm{arm,S.Sequence{Con{S.Constructor{token,args},rest}},body},without(tail,ctor)})
    case Con{head,tail}: Con{head,without(tail,ctor)}

def available(column: S.Node, definition: C.Datatype) -> List<&2,S.Token>:
  match column definition:
    case S.Remainder{token,level,tags} _: tags
    case _ C.Datatype{token,data,ctors}: declared(ctors)

def column_binding(+column: S.Node, +scope: E.Scope) -> Result<S.Error,C.Binding>:
  match column scope:
    case S.Remainder{token,level,tags} E.Scope{bindings,next,open,live,smaller}: E.find_level(bindings,level)
    case _ _: E.scrutinee(column,scope)

def split(tags: List<&2,S.Token>, binding: C.Binding, +token: S.Token, +column: S.Node,
  +columns: List<&2,S.Node>, +rows: List<&2,S.Node>, scope: E.Scope, +types: List<&2,C.Datatype>, +work: U32) -> Result<S.Error,S.Node>:
  match tags binding scope:
    case Nil{} _ _: C.internal(S.Node,"matrix-split")
    case Con{+ctor,tail} C.Binding{+name,+level,q,+type_id,param,known} E.Scope{bindings,+next,open,live,smaller}:
      S.bind(C.Datatype,S.Node,G.type_at(types,type_id),definition =>
        +rest = remaining(available(column,definition),ctor)
        S.bind(G.ConstructorRef,S.Node,G.find_constructor(types,ctor,0),reference =>
          S.bind(List<&2,C.Parameter>,S.Node,G.field_signature(reference,types),params =>
            +fields = fresh(params,next,S.at(token))
            Done{promote(name,level,mark(rows),S.Decision{token,column,S.Constructor{ctor,fields},
              S.Matrix{token,List.append(&2,S.Node,fields,columns),specialize(rows,ctor,fields,level),work},
              S.Matrix{token,Con{S.Remainder{name,level,rest},columns},without(rows,ctor),work}})})))

def alias_column(+binding: C.Binding, +token: S.Token, columns: List<&2,S.Node>, +rows: List<&2,S.Node>, work: U32) -> S.Node:
  match binding:
    case C.Binding{name,level,q,type_id,param,known}:
      promote(name,level,mark(rows),S.Matrix{token,columns,default_rows(rows,level),work})

def variable_step(+column: S.Node, +token: S.Token, +columns: List<&2,S.Node>, +rows: List<&2,S.Node>, +scope: E.Scope, +work: U32) -> Result<S.Error,S.Node>:
  match column:
    case S.Remainder{name,level,tags}:
      S.bind(C.Binding,S.Node,column_binding(column,scope),binding => Done{alias_column(binding,token,columns,rows,work)})
    case S.Variable{+name}:
      S.bind(C.Binding,S.Node,E.lookup(scope,name),binding =>
        S.bind(C.Binding,S.Node,variable_column(binding,scope,name),bound =>
          Done{alias_column(bound,token,columns,rows,work)}))
    case _: S.bind(C.Binding,S.Node,E.scrutinee(column,scope),binding => C.internal(S.Node,"matrix-variable"))

def column_step(+token: S.Token, columns: List<&2,S.Node>, +rows: List<&2,S.Node>, +work: U32, +types: List<&2,C.Datatype>, +scope: E.Scope) -> Result<S.Error,S.Node>:
  match columns rows:
    case Nil{} Con{S.Arm{arm,patterns,body},tail}: Done{body}
    case Nil{} Nil{}: C.invalid(S.Node,"missing-arm",token)
    case Con{+column,+tail} _:
      S.choose(Result<S.Error,S.Node>,Bool.not(List.is_empty(&2,S.Node,rows)),u =>
        S.choose(Result<S.Error,S.Node>,List.is_empty(&2,S.Token,constructors(rows,Nil{})),u =>
          variable_step(column,token,tail,rows,scope,work),u =>
          S.bind(C.Binding,S.Node,column_binding(column,scope),binding => split(constructors(rows,Nil{}),binding,token,column,tail,rows,scope,types,work))),u =>
        Done{S.Match{token,column,Nil{}}})
    case _ _: C.internal(S.Node,"matrix-leaf")

# One unit per residual matrix. Expansion threads the unused work through
# both sides of every decision; the quota bounds the entire generated tree.
def step(+token: S.Token, columns: List<&2,S.Node>, rows: List<&2,S.Node>, +work: U32,
  types: List<&2,C.Datatype>, scope: E.Scope) -> Result<S.Error,S.Node>:
  S.choose(Result<S.Error,S.Node>,U32.is_eq(work,0),u => C.exhausted(S.Node,token),u =>
    column_step(token,columns,rows,U32.sub(work,1),types,scope))

# Promotion changes quantity, never identity. Every alias of the same level is
# refined together by the existing pattern checker; erased fields stay erased.
def remarked(bindings: List<&2,C.Binding>, +level: U32, +mark: U32) -> List<&2,C.Binding>:
  match bindings:
    case Nil{}: Nil{}
    case Con{C.Binding{token,+id,+q,type_id,param,known},tail}:
      Con{C.Binding{token,id,S.choose(U32,U32.is_eq(id,level),u => P.quantity(q,1,mark),u => q),type_id,param,known},remarked(tail,level,mark)}

# A `+` row's mark reaches only a lambda-case binder (a parameter or field), as
# in the seed. A let binder and its aliases keep the let's declared quantity.
# Its kind is judged later, where the frontier binds it (P.bound).
def alias_bound(binding: C.Binding, +token: S.Token, +row: U32, scope: E.Scope) -> Result<S.Error,E.Scope>:
  match binding scope:
    case C.Binding{name,+level,q,type_id,+param,known} E.Scope{bindings,next,open,live,smaller}:
      +mark = S.choose(U32,param,u => row,u => 1)
      +actual = P.quantity(q,1,mark)
      Done{E.Scope{Con{C.Binding{token,level,actual,type_id,param,known},remarked(bindings,level,mark)},next,open,live,smaller}}

def alias(+scope: E.Scope, token: S.Token, level: U32, mark: U32) -> Result<S.Error,E.Scope>:
  match scope:
    case E.Scope{bindings,next,open,live,smaller}:
      S.bind(C.Binding,E.Scope,E.find_level(bindings,level),binding => alias_bound(binding,token,mark,scope))


type Expansion is Data:
  Expansion{node: S.Node, remaining: U32}

def thread(result: Result<S.Error,Expansion>, next: S.Node -> U32 -> Result<S.Error,Expansion>) -> Result<S.Error,Expansion>:
  match result:
    case Fail{error}: Fail{error}
    case Done{Expansion{node,work}}: next(node,work)

def expanded(value: Expansion) -> S.Node:
  match value:
    case Expansion{node,work}: node

def opened(value: P.Fields) -> E.Scope:
  match value:
    case P.Fields{scope,bindings,args}: scope

def at_level(binding: C.Binding, next: U32 -> Result<S.Error,Expansion>) -> Result<S.Error,Expansion>:
  match binding:
    case C.Binding{name,level,q,type_id,param,known}: next(level)

def reference(pattern: S.Node, types: List<&2,C.Datatype>) -> Result<S.Error,G.ConstructorRef>:
  match pattern:
    case S.Constructor{token,args}: G.find_constructor(types,token,0)
    case _: C.internal(G.ConstructorRef,"matrix-constructor")

def residual(+binding: C.Binding, column: S.Node, pattern: S.Node, +scope: E.Scope, types: List<&2,C.Datatype>) -> Result<S.Error,E.Scope>:
  match binding pattern:
    case C.Binding{name,level,q,type_id,param,known} S.Constructor{+ctor,args}:
      S.bind(C.Datatype,E.Scope,G.type_at(types,type_id),definition =>
        Done{E.residual(scope,binding,List.is_empty(&2,S.Token,remaining(available(column,definition),ctor)))})
    case _ _: C.internal(E.Scope,"matrix-residual")

# Only internal lowering states are traversed. A source body starts its own
# matrix budget when the checker reaches it; discarded source bodies stay dead.
def expand(fuel: Nat, +node: S.Node, +types: List<&2,C.Datatype>, +scope: E.Scope, +work: U32) -> Result<S.Error,Expansion>:
  match fuel node:
    case 0n _: Fail{S.Exhausted{"check",S.At{0,0,0,0}}}
    case 1n+ +n S.Matrix{token,columns,rows,quota}:
      S.bind(S.Node,Expansion,step(token,columns,rows,work,types,scope),tree =>
        expand(n,tree,types,scope,U32.sub(work,1)))
    case 1n+ +n S.Alias{+token,+level,+mark,body}:
      S.bind(E.Scope,Expansion,alias(scope,token,level,mark),bound =>
        thread(expand(n,body,types,bound,work),tree => left => Done{Expansion{S.Alias{token,level,mark,tree},left}}))
    case 1n+ +n S.Decision{+token,+column,+pattern,+yes,+no}:
      S.bind(C.Binding,Expansion,column_binding(column,scope),+binding =>
        at_level(binding,+level =>
          S.bind(G.ConstructorRef,Expansion,reference(pattern,types),reference =>
            S.bind(P.Fields,Expansion,P.branch(scope,level,reference,pattern,types),fields =>
              thread(expand(n,yes,types,opened(fields),work),positive => left =>
                S.bind(E.Scope,Expansion,residual(binding,column,pattern,scope,types),remaining =>
                  thread(expand(n,no,types,remaining,left),negative => rest =>
                    Done{Expansion{S.Decision{token,column,pattern,positive,negative},rest}})))))))
    case 1n+n _: Done{Expansion{node,work}}

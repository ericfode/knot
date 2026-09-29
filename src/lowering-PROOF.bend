import Base
import ./syntax.bend as S
import ./core.bend as C
import ./catalog.bend as G
import ./patterns.bend as P
import ./scope.bend as E
import ./matrix.bend as M
import ./lowering-LAWS.bend as L

# The irrefutable first row. Lowers is the invariant that every lowering state
# preserves: a matrix leads with an irrefutable row whose body lowers to the
# selected body; aliases are transparent and a decision lowers on both sides.
type Led<-columns: List<&2,S.Node>, -rows: List<&2,S.Node>, -body: S.Node> is Data:
  Led{arm: S.Token, patterns: List<&2,S.Node>, lead: S.Node, tail: List<&2,S.Node>,
    shape: {rows == Con{S.Arm{arm,S.Sequence{patterns},lead},tail} : List<&2,S.Node>},
    irrefutable: L.Irrefutable(columns,patterns), lowers: Lowers(lead,body)}

def Lowers(node: S.Node, body: S.Node) -> Data:
  match node:
    case S.Matrix{token,columns,rows,work}: Led<columns,rows,body>
    case S.Alias{token,level,mark,rest}: Lowers(rest,body)
    case S.Decision{token,column,pattern,yes,no}: Sigma<&2,&2,Lowers(yes,body),x => Lowers(no,body)>
    case _: {node == body : S.Node}

def Stepped(result: Result<S.Error,S.Node>, body: S.Node) -> Data:
  match result:
    case Fail{error}: Unit
    case Done{node}: Lowers(node,body)

def Selected(result: Result<S.Error,M.Expansion>, body: S.Node) -> Type:
  match result:
    case Fail{error}: Unit
    case Done{M.Expansion{tree,left}}: L.Leaves(tree,body)

def stepped_bind(-A: Data, result: Result<S.Error,A>, next: A -> Result<S.Error,S.Node>, +body: S.Node,
  each: @x:A -> Stepped(next(x),body)) -> Stepped(S.bind(A,S.Node,result,next),body):
  match result:
    case Fail{error}: Unit{}
    case Done{x}: each(x)

def stepped_choice(condition: Bool, yes: Unit -> Result<S.Error,S.Node>, no: Unit -> Result<S.Error,S.Node>, +body: S.Node,
  a: Stepped(yes(Unit{}),body), b: Stepped(no(Unit{}),body)) -> Stepped(S.choose(Result<S.Error,S.Node>,condition,yes,no),body):
  match condition:
    case True{}: a
    case False{}: b

def selected_bind(-A: Data, result: Result<S.Error,A>, next: A -> Result<S.Error,M.Expansion>, +body: S.Node,
  each: @x:A -> Selected(next(x),body)) -> Selected(S.bind(A,M.Expansion,result,next),body):
  match result:
    case Fail{error}: Unit{}
    case Done{x}: each(x)

def selected_step(result: Result<S.Error,S.Node>, next: S.Node -> Result<S.Error,M.Expansion>, +body: S.Node,
  each: @node:S.Node -> Lowers(node,body) -> Selected(next(node),body), p: Stepped(result,body)) -> Selected(S.bind(S.Node,M.Expansion,result,next),body):
  match result:
    case Fail{error}: Unit{}
    case Done{node}: each(node,p)

def threaded(result: Result<S.Error,M.Expansion>, next: S.Node -> U32 -> Result<S.Error,M.Expansion>, +body: S.Node,
  each: @tree:S.Node -> @left:U32 -> L.Leaves(tree,body) -> Selected(next(tree,left),body), p: Selected(result,body)) ->
  Selected(M.thread(result,next),body):
  match result:
    case Fail{error}: Unit{}
    case Done{M.Expansion{tree,left}}: each(tree,left,p)

def promoted_at(condition: Bool, +token: S.Token, +level: U32, +node: S.Node, +body: S.Node, +p: Lowers(node,body)) ->
  Lowers(S.choose(S.Node,condition,u => S.Alias{token,level,2,node},u => node),body):
  match condition:
    case True{}: p
    case False{}: p

def promoted(+token: S.Token, +level: U32, +mark: U32, +node: S.Node, +body: S.Node, +p: Lowers(node,body)) -> Lowers(M.promote(token,level,mark,node),body):
  promoted_at(U32.is_eq(mark,2),token,level,node,body,p)

def rebound(lead: S.Node, +token: S.Token, +level: U32, +mark: U32, +body: S.Node, p: Lowers(lead,body)) -> Lowers(M.bind_body(lead,token,level,mark),body):
  match lead:
    case S.Alias{name,id,q,rest}: rebound(rest,token,level,mark,body,p)
    case S.Variable{a0}: p
    case S.Promotion{a0}: p
    case S.Constructor{a0,a1}: p
    case S.Call{a0,a1}: p
    case S.Binding{a0,a1,a2,a3,a4}: p
    case S.Match{a0,a1,a2}: p
    case S.Arm{a0,a1,a2}: p
    case S.Matrix{a0,a1,a2,a3}: p
    case S.Decision{a0,a1,a2,a3,a4}: p
    case S.Remainder{a0,a1,a2}: p
    case S.Parameter{a0,a1,a2}: p
    case S.Datatype{a0,a1,a2}: p
    case S.Function{a0,a1,a2,a3}: p
    case S.Literal{a0,a1,a2,a3}: p
    case S.Offset{a0,a1,a2}: p
    case S.Intrinsic{a0,a1,a2}: p
    case S.Sequence{a0}: p

def fresh_irrefutable(params: List<&2,C.Parameter>, +level: U32, +at: S.At, +columns: List<&2,S.Node>, +patterns: List<&2,S.Node>,
  p: L.Irrefutable(columns,patterns)) ->
  L.Irrefutable(List.append(&2,S.Node,M.fresh(params,level,at),columns),List.append(&2,S.Node,M.fresh(params,level,at),patterns)):
  match params:
    case Nil{}: p
    case Con{head,tail}: fresh_irrefutable(tail,U32.add(level,1),at,columns,patterns,p)

# A split mirrors M.split: the promoted binary decision on one constructor.
def split_node(+token: S.Token, +column: S.Node, +ctor: S.Token, +name: S.Token, +level: U32, +next: U32, +columns: List<&2,S.Node>,
  +rows: List<&2,S.Node>, +work: U32, +tags: List<&2,S.Token>, +params: List<&2,C.Parameter>) -> S.Node:
  S.Decision{token,column,S.Constructor{ctor,M.fresh(params,next,S.at(token))},
    S.Matrix{token,List.append(&2,S.Node,M.fresh(params,next,S.at(token)),columns),M.specialize(rows,ctor,M.fresh(params,next,S.at(token)),level),work},
    S.Matrix{token,Con{S.Remainder{name,level,tags},columns},M.without(rows,ctor),work}}

def decision(+token: S.Token, +column: S.Node, +ctor: S.Token, +name: S.Token, +level: U32, +next: U32, +columns: List<&2,S.Node>,
  +rows: List<&2,S.Node>, +work: U32, +tags: List<&2,S.Token>, +params: List<&2,C.Parameter>) -> S.Node:
  M.promote(name,level,M.mark(rows),split_node(token,column,ctor,name,level,next,columns,rows,work,tags,params))

def unmatched(column: S.Node, scope: E.Scope, +body: S.Node) ->
  Stepped(S.bind(C.Binding,S.Node,E.scrutinee(column,scope),binding => C.internal(S.Node,"matrix-variable")),body):
  stepped_bind(C.Binding,E.scrutinee(column,scope),binding => C.internal(S.Node,"matrix-variable"),body,binding => Unit{})

def defaulted(column: S.Node, +token: S.Token, +columns: List<&2,S.Node>, +rows: List<&2,S.Node>, +scope: E.Scope, +work: U32, +body: S.Node,
  each: @binding:C.Binding -> Lowers(M.alias_column(binding,token,columns,rows,work),body)) ->
  Stepped(M.variable_step(column,token,columns,rows,scope,work),body):
  match column:
    case S.Remainder{+name,+level,+tags}:
      stepped_bind(C.Binding,M.column_binding(S.Remainder{name,level,tags},scope),binding => Done{M.alias_column(binding,token,columns,rows,work)},body,each)
    case S.Variable{+name}:
      stepped_bind(C.Binding,E.lookup(scope,name),
        binding => S.bind(C.Binding,S.Node,M.variable_column(binding,scope,name),bound => Done{M.alias_column(bound,token,columns,rows,work)}),body,
        binding => stepped_bind(C.Binding,M.variable_column(binding,scope,name),bound => Done{M.alias_column(bound,token,columns,rows,work)},body,each))
    case S.Promotion{a0}: unmatched(S.Promotion{a0},scope,body)
    case S.Constructor{a0,a1}: unmatched(S.Constructor{a0,a1},scope,body)
    case S.Call{a0,a1}: unmatched(S.Call{a0,a1},scope,body)
    case S.Binding{a0,a1,a2,a3,a4}: unmatched(S.Binding{a0,a1,a2,a3,a4},scope,body)
    case S.Match{a0,a1,a2}: unmatched(S.Match{a0,a1,a2},scope,body)
    case S.Arm{a0,a1,a2}: unmatched(S.Arm{a0,a1,a2},scope,body)
    case S.Matrix{a0,a1,a2,a3}: unmatched(S.Matrix{a0,a1,a2,a3},scope,body)
    case S.Decision{a0,a1,a2,a3,a4}: unmatched(S.Decision{a0,a1,a2,a3,a4},scope,body)
    case S.Alias{a0,a1,a2,a3}: unmatched(S.Alias{a0,a1,a2,a3},scope,body)
    case S.Parameter{a0,a1,a2}: unmatched(S.Parameter{a0,a1,a2},scope,body)
    case S.Datatype{a0,a1,a2}: unmatched(S.Datatype{a0,a1,a2},scope,body)
    case S.Function{a0,a1,a2,a3}: unmatched(S.Function{a0,a1,a2,a3},scope,body)
    case S.Literal{a0,a1,a2,a3}: unmatched(S.Literal{a0,a1,a2,a3},scope,body)
    case S.Offset{a0,a1,a2}: unmatched(S.Offset{a0,a1,a2},scope,body)
    case S.Intrinsic{a0,a1,a2}: unmatched(S.Intrinsic{a0,a1,a2},scope,body)
    case S.Sequence{a0}: unmatched(S.Sequence{a0},scope,body)

def splits(tags: List<&2,S.Token>, binding: C.Binding, +token: S.Token, +column: S.Node, +columns: List<&2,S.Node>, +rows: List<&2,S.Node>,
  scope: E.Scope, +types: List<&2,C.Datatype>, +work: U32, +body: S.Node,
  each: @ctor:S.Token -> @name:S.Token -> @level:U32 -> @next:U32 -> @tags:List<&2,S.Token> -> @params:List<&2,C.Parameter> ->
    Lowers(decision(token,column,ctor,name,level,next,columns,rows,work,tags,params),body)) ->
  Stepped(M.split(tags,binding,token,column,columns,rows,scope,types,work),body):
  match tags:
    case Nil{}: Unit{}
    case Con{+ctor,others}:
      match binding:
        case C.Binding{+name,+level,+quantity,+type_id,+param,+known}:
          match scope:
            case E.Scope{bindings,+next,open,live,smaller}:
              stepped_bind(C.Datatype,G.type_at(types,type_id),
                definition => S.bind(G.ConstructorRef,S.Node,G.find_constructor(types,ctor,0),reference =>
                  S.bind(List<&2,C.Parameter>,S.Node,G.field_signature(reference,types),params =>
                    Done{decision(token,column,ctor,name,level,next,columns,rows,work,M.remaining(M.available(column,definition),ctor),params)})),body,
                +definition => stepped_bind(G.ConstructorRef,G.find_constructor(types,ctor,0),
                  reference => S.bind(List<&2,C.Parameter>,S.Node,G.field_signature(reference,types),params =>
                    Done{decision(token,column,ctor,name,level,next,columns,rows,work,M.remaining(M.available(column,definition),ctor),params)}),body,
                  +reference => stepped_bind(List<&2,C.Parameter>,G.field_signature(reference,types),
                    params => Done{decision(token,column,ctor,name,level,next,columns,rows,work,M.remaining(M.available(column,definition),ctor),params)},body,
                    +params => each(ctor,name,level,next,M.remaining(M.available(column,definition),ctor),params))))

# A nonempty matrix with a column either defaults or splits on its first constructor.
def headed_step(+token: S.Token, +column: S.Node, +columns: List<&2,S.Node>, +first: S.Node, +others: List<&2,S.Node>, +work: U32,
  +types: List<&2,C.Datatype>, +scope: E.Scope, +body: S.Node,
  aliases: @binding:C.Binding -> Lowers(M.alias_column(binding,token,columns,Con{first,others},work),body),
  decisions: @ctor:S.Token -> @name:S.Token -> @level:U32 -> @next:U32 -> @tags:List<&2,S.Token> -> @params:List<&2,C.Parameter> ->
    Lowers(decision(token,column,ctor,name,level,next,columns,Con{first,others},work,tags,params),body)) ->
  Stepped(M.column_step(token,Con{column,columns},Con{first,others},work,types,scope),body):
  stepped_choice(List.is_empty(&2,S.Token,M.constructors(Con{first,others},Nil{})),
    u => M.variable_step(column,token,columns,Con{first,others},scope,work),
    u => S.bind(C.Binding,S.Node,M.column_binding(column,scope),binding =>
      M.split(M.constructors(Con{first,others},Nil{}),binding,token,column,columns,Con{first,others},scope,types,work)),body,
    defaulted(column,token,columns,Con{first,others},scope,work,body,aliases),
    stepped_bind(C.Binding,M.column_binding(column,scope),binding =>
      M.split(M.constructors(Con{first,others},Nil{}),binding,token,column,columns,Con{first,others},scope,types,work),body,
      binding => splits(M.constructors(Con{first,others},Nil{}),binding,token,column,columns,Con{first,others},scope,types,work,body,decisions)))

def aliased_variable(binding: C.Binding, +token: S.Token, +columns: List<&2,S.Node>, +arm: S.Token, +binder: S.Token, +more: List<&2,S.Node>,
  +lead: S.Node, +tail: List<&2,S.Node>, +work: U32, +body: S.Node, +irr: L.Irrefutable(columns,more), +q: Lowers(lead,body)) ->
  Lowers(M.alias_column(binding,token,columns,Con{S.Arm{arm,S.Sequence{Con{S.Variable{binder},more}},lead},tail},work),body):
  match binding:
    case C.Binding{+name,+level,+quantity,+type_id,+param,+known}:
      promoted(name,level,M.mark(Con{S.Arm{arm,S.Sequence{Con{S.Variable{binder},more}},lead},tail}),S.Matrix{token,columns,M.default_rows(Con{S.Arm{arm,S.Sequence{Con{S.Variable{binder},more}},lead},tail},level),work},body,
        Led{arm,more,M.bind_body(lead,binder,level,1),M.default_rows(tail,level),{==},irr,rebound(lead,binder,level,1,body,q)})

def aliased_promotion(binding: C.Binding, +token: S.Token, +columns: List<&2,S.Node>, +arm: S.Token, +binder: S.Token, +more: List<&2,S.Node>,
  +lead: S.Node, +tail: List<&2,S.Node>, +work: U32, +body: S.Node, +irr: L.Irrefutable(columns,more), +q: Lowers(lead,body)) ->
  Lowers(M.alias_column(binding,token,columns,Con{S.Arm{arm,S.Sequence{Con{S.Promotion{binder},more}},lead},tail},work),body):
  match binding:
    case C.Binding{+name,+level,+quantity,+type_id,+param,+known}:
      promoted(name,level,M.mark(Con{S.Arm{arm,S.Sequence{Con{S.Promotion{binder},more}},lead},tail}),S.Matrix{token,columns,M.default_rows(Con{S.Arm{arm,S.Sequence{Con{S.Promotion{binder},more}},lead},tail},level),work},body,
        Led{arm,more,M.bind_body(lead,binder,level,2),M.default_rows(tail,level),{==},irr,rebound(lead,binder,level,2,body,q)})

def decided_variable(+token: S.Token, +column: S.Node, +ctor: S.Token, +name: S.Token, +level: U32, +next: U32, +columns: List<&2,S.Node>,
  +arm: S.Token, +binder: S.Token, +more: List<&2,S.Node>, +lead: S.Node, +tail: List<&2,S.Node>, +work: U32, +tags: List<&2,S.Token>,
  +params: List<&2,C.Parameter>, +body: S.Node, +irr: L.Irrefutable(columns,more), +q: Lowers(lead,body)) ->
  Lowers(decision(token,column,ctor,name,level,next,columns,Con{S.Arm{arm,S.Sequence{Con{S.Variable{binder},more}},lead},tail},work,tags,params),body):
  promoted(name,level,M.mark(Con{S.Arm{arm,S.Sequence{Con{S.Variable{binder},more}},lead},tail}),split_node(token,column,ctor,name,level,next,columns,Con{S.Arm{arm,S.Sequence{Con{S.Variable{binder},more}},lead},tail},work,tags,params),body,
    (Led{arm,List.append(&2,S.Node,M.fresh(params,next,S.at(token)),more),M.bind_body(lead,binder,level,1),M.specialize(tail,ctor,M.fresh(params,next,S.at(token)),level),{==},
       fresh_irrefutable(params,next,S.at(token),columns,more,irr),rebound(lead,binder,level,1,body,q)},
     Led{arm,Con{S.Variable{binder},more},lead,M.without(tail,ctor),{==},irr,q}))

def decided_promotion(+token: S.Token, +column: S.Node, +ctor: S.Token, +name: S.Token, +level: U32, +next: U32, +columns: List<&2,S.Node>,
  +arm: S.Token, +binder: S.Token, +more: List<&2,S.Node>, +lead: S.Node, +tail: List<&2,S.Node>, +work: U32, +tags: List<&2,S.Token>,
  +params: List<&2,C.Parameter>, +body: S.Node, +irr: L.Irrefutable(columns,more), +q: Lowers(lead,body)) ->
  Lowers(decision(token,column,ctor,name,level,next,columns,Con{S.Arm{arm,S.Sequence{Con{S.Promotion{binder},more}},lead},tail},work,tags,params),body):
  promoted(name,level,M.mark(Con{S.Arm{arm,S.Sequence{Con{S.Promotion{binder},more}},lead},tail}),split_node(token,column,ctor,name,level,next,columns,Con{S.Arm{arm,S.Sequence{Con{S.Promotion{binder},more}},lead},tail},work,tags,params),body,
    (Led{arm,List.append(&2,S.Node,M.fresh(params,next,S.at(token)),more),M.bind_body(lead,binder,level,2),M.specialize(tail,ctor,M.fresh(params,next,S.at(token)),level),{==},
       fresh_irrefutable(params,next,S.at(token),columns,more,irr),rebound(lead,binder,level,2,body,q)},
     Led{arm,Con{S.Promotion{binder},more},lead,M.without(tail,ctor),{==},irr,q}))

def led(+token: S.Token, columns: List<&2,S.Node>, +arm: S.Token, patterns: List<&2,S.Node>, +lead: S.Node, +tail: List<&2,S.Node>,
  +work: U32, +types: List<&2,C.Datatype>, +scope: E.Scope, +body: S.Node, +irr: L.Irrefutable(columns,patterns), +q: Lowers(lead,body)) ->
  Stepped(M.column_step(token,columns,Con{S.Arm{arm,S.Sequence{patterns},lead},tail},work,types,scope),body):
  match columns:
    case Nil{}: q
    case Con{+column,+rest}:
      match patterns:
        case Nil{}: match irr:
        case Con{head,+more}:
          match head:
            case S.Variable{+binder}:
              headed_step(token,column,rest,S.Arm{arm,S.Sequence{Con{S.Variable{binder},more}},lead},tail,work,types,scope,body,
                binding => aliased_variable(binding,token,rest,arm,binder,more,lead,tail,work,body,irr,q),
                ctor => name => level => next => tags => params =>
                  decided_variable(token,column,ctor,name,level,next,rest,arm,binder,more,lead,tail,work,tags,params,body,irr,q))
            case S.Promotion{+binder}:
              headed_step(token,column,rest,S.Arm{arm,S.Sequence{Con{S.Promotion{binder},more}},lead},tail,work,types,scope,body,
                binding => aliased_promotion(binding,token,rest,arm,binder,more,lead,tail,work,body,irr,q),
                ctor => name => level => next => tags => params =>
                  decided_promotion(token,column,ctor,name,level,next,rest,arm,binder,more,lead,tail,work,tags,params,body,irr,q))
            case S.Constructor{a0,a1}: match irr:
            case S.Call{a0,a1}: match irr:
            case S.Binding{a0,a1,a2,a3,a4}: match irr:
            case S.Match{a0,a1,a2}: match irr:
            case S.Arm{a0,a1,a2}: match irr:
            case S.Matrix{a0,a1,a2,a3}: match irr:
            case S.Decision{a0,a1,a2,a3,a4}: match irr:
            case S.Remainder{a0,a1,a2}: match irr:
            case S.Alias{a0,a1,a2,a3}: match irr:
            case S.Parameter{a0,a1,a2}: match irr:
            case S.Datatype{a0,a1,a2}: match irr:
            case S.Function{a0,a1,a2,a3}: match irr:
            case S.Literal{a0,a1,a2,a3}: match irr:
            case S.Offset{a0,a1,a2}: match irr:
            case S.Intrinsic{a0,a1,a2}: match irr:
            case S.Sequence{a0}: match irr:

def columned(+token: S.Token, +columns: List<&2,S.Node>, +rows: List<&2,S.Node>, +work: U32, +types: List<&2,C.Datatype>, +scope: E.Scope,
  +body: S.Node, p: Led<columns,rows,body>) -> Stepped(M.column_step(token,columns,rows,work,types,scope),body):
  match p:
    case Led{+arm,+patterns,+lead,+tail,shape,irr,q}:
      %Equal.sym(List<&2,S.Node>,rows,Con{S.Arm{arm,S.Sequence{patterns},lead},tail},shape) :
        Stepped(M.column_step(token,columns,_,work,types,scope),body)
      led(token,columns,arm,patterns,lead,tail,work,types,scope,body,irr,q)

def stepped(+token: S.Token, +columns: List<&2,S.Node>, +rows: List<&2,S.Node>, +work: U32, +types: List<&2,C.Datatype>, +scope: E.Scope,
  +body: S.Node, p: Led<columns,rows,body>) -> Stepped(M.step(token,columns,rows,work,types,scope),body):
  stepped_choice(U32.is_eq(work,0),u => C.exhausted(S.Node,token),u => M.column_step(token,columns,rows,U32.sub(work,1),types,scope),body,
    Unit{},columned(token,columns,rows,U32.sub(work,1),types,scope,body,p))

def after_no(+token: S.Token, +column: S.Node, +pattern: S.Node, +positive: S.Node) -> S.Node -> U32 -> Result<S.Error,M.Expansion>:
  negative => rest => Done{M.Expansion{S.Decision{token,column,pattern,positive,negative},rest}}

def after_yes(+n: Nat, +token: S.Token, +column: S.Node, +pattern: S.Node, +no: S.Node, +binding: C.Binding, +types: List<&2,C.Datatype>,
  +scope: E.Scope) -> S.Node -> U32 -> Result<S.Error,M.Expansion>:
  positive => left =>
    S.bind(E.Scope,M.Expansion,M.residual(binding,column,pattern,scope,types),remaining =>
      M.thread(M.expand(n,no,types,remaining,left),after_no(token,column,pattern,positive)))

def opened_tree(+n: Nat, binding: C.Binding, +token: S.Token, +column: S.Node, +pattern: S.Node, +yes: S.Node, +no: S.Node,
  +types: List<&2,C.Datatype>, +scope: E.Scope, +work: U32, +body: S.Node, +py: Lowers(yes,body), +pn: Lowers(no,body),
  yes_ih: @scope:E.Scope -> @work:U32 -> Lowers(yes,body) -> Selected(M.expand(n,yes,types,scope,work),body),
  no_ih: @scope:E.Scope -> @work:U32 -> Lowers(no,body) -> Selected(M.expand(n,no,types,scope,work),body)) ->
  Selected(M.at_level(binding,+level =>
      S.bind(G.ConstructorRef,M.Expansion,M.reference(pattern,types),reference =>
        S.bind(P.Fields,M.Expansion,P.branch(scope,level,reference,pattern,types),fields =>
          M.thread(M.expand(n,yes,types,M.opened(fields),work),after_yes(n,token,column,pattern,no,binding,types,scope))))),body):
  match binding:
    case C.Binding{+name,+level,+quantity,+type_id,+param,+known}:
      selected_bind(G.ConstructorRef,M.reference(pattern,types),reference =>
          S.bind(P.Fields,M.Expansion,P.branch(scope,level,reference,pattern,types),fields =>
            M.thread(M.expand(n,yes,types,M.opened(fields),work),after_yes(n,token,column,pattern,no,C.Binding{name,level,quantity,type_id,param,known},types,scope))),body,
        +reference => selected_bind(P.Fields,P.branch(scope,level,reference,pattern,types),fields =>
            M.thread(M.expand(n,yes,types,M.opened(fields),work),after_yes(n,token,column,pattern,no,C.Binding{name,level,quantity,type_id,param,known},types,scope)),body,
          +fields => threaded(M.expand(n,yes,types,M.opened(fields),work),after_yes(n,token,column,pattern,no,C.Binding{name,level,quantity,type_id,param,known},types,scope),body,
            +positive => +left => ly => selected_bind(E.Scope,M.residual(C.Binding{name,level,quantity,type_id,param,known},column,pattern,scope,types),
                remaining => M.thread(M.expand(n,no,types,remaining,left),after_no(token,column,pattern,positive)),body,
              +remaining => threaded(M.expand(n,no,types,remaining,left),after_no(token,column,pattern,positive),body,
                negative => rest => ln => (ly,ln),no_ih(remaining,left,pn))),
            yes_ih(M.opened(fields),work,py))))

def decided_tree(+n: Nat, +token: S.Token, +column: S.Node, +pattern: S.Node, +yes: S.Node, +no: S.Node, +types: List<&2,C.Datatype>,
  +scope: E.Scope, +work: U32, +body: S.Node, +py: Lowers(yes,body), +pn: Lowers(no,body),
  yes_ih: @scope:E.Scope -> @work:U32 -> Lowers(yes,body) -> Selected(M.expand(n,yes,types,scope,work),body),
  no_ih: @scope:E.Scope -> @work:U32 -> Lowers(no,body) -> Selected(M.expand(n,no,types,scope,work),body)) ->
  Selected(M.expand(1n+n,S.Decision{token,column,pattern,yes,no},types,scope,work),body):
  selected_bind(C.Binding,M.column_binding(column,scope),+binding => M.at_level(binding,+level =>
      S.bind(G.ConstructorRef,M.Expansion,M.reference(pattern,types),reference =>
        S.bind(P.Fields,M.Expansion,P.branch(scope,level,reference,pattern,types),fields =>
          M.thread(M.expand(n,yes,types,M.opened(fields),work),after_yes(n,token,column,pattern,no,binding,types,scope))))),body,
    +binding => opened_tree(n,binding,token,column,pattern,yes,no,types,scope,work,body,py,pn,yes_ih,no_ih))

# Expansion keeps every leaf on the selected body; fuel exhaustion is a failure.
def expanded(fuel: Nat, node: S.Node, +types: List<&2,C.Datatype>, +scope: E.Scope, +work: U32, +body: S.Node, p: Lowers(node,body)) ->
  Selected(M.expand(fuel,node,types,scope,work),body):
  match fuel:
    case 0n: Unit{}
    case 1n+ +n:
      match node:
        case S.Matrix{+token,+columns,+rows,quota}:
          selected_step(M.step(token,columns,rows,work,types,scope),tree => M.expand(n,tree,types,scope,U32.sub(work,1)),body,
            +tree => q => expanded(n,tree,types,scope,U32.sub(work,1),body,q),stepped(token,columns,rows,work,types,scope,body,p))
        case S.Alias{+token,+level,+mark,+rest}:
          selected_bind(E.Scope,M.alias(scope,token,level,mark),
            bound => M.thread(M.expand(n,rest,types,bound,work),tree => left => Done{M.Expansion{S.Alias{token,level,mark,tree},left}}),body,
            +bound => threaded(M.expand(n,rest,types,bound,work),tree => left => Done{M.Expansion{S.Alias{token,level,mark,tree},left}},body,
              tree => left => q => q,expanded(n,rest,types,bound,work,body,p)))
        case S.Decision{+token,+column,+pattern,+yes,+no}:
          match p:
            case (py,pn):
              decided_tree(n,token,column,pattern,yes,no,types,scope,work,body,py,pn,
                +scope => +work => q => expanded(n,yes,types,scope,work,body,q),
                +scope => +work => q => expanded(n,no,types,scope,work,body,q))
        case S.Variable{a0}: p
        case S.Promotion{a0}: p
        case S.Constructor{a0,a1}: p
        case S.Call{a0,a1}: p
        case S.Binding{a0,a1,a2,a3,a4}: p
        case S.Match{a0,a1,a2}: p
        case S.Arm{a0,a1,a2}: p
        case S.Remainder{a0,a1,a2}: p
        case S.Parameter{a0,a1,a2}: p
        case S.Datatype{a0,a1,a2}: p
        case S.Function{a0,a1,a2,a3}: p
        case S.Literal{a0,a1,a2,a3}: p
        case S.Offset{a0,a1,a2}: p
        case S.Intrinsic{a0,a1,a2}: p
        case S.Sequence{a0}: p

def settled(body: S.Node, leaf: L.Leaf(body)) -> Lowers(body,body):
  match body:
    case S.Variable{a0}: {==}
    case S.Promotion{a0}: {==}
    case S.Constructor{a0,a1}: {==}
    case S.Call{a0,a1}: {==}
    case S.Binding{a0,a1,a2,a3,a4}: {==}
    case S.Match{a0,a1,a2}: {==}
    case S.Arm{a0,a1,a2}: {==}
    case S.Matrix{a0,a1,a2,a3}: match leaf:
    case S.Decision{a0,a1,a2,a3,a4}: match leaf:
    case S.Remainder{a0,a1,a2}: {==}
    case S.Alias{a0,a1,a2,a3}: match leaf:
    case S.Parameter{a0,a1,a2}: {==}
    case S.Datatype{a0,a1,a2}: {==}
    case S.Function{a0,a1,a2,a3}: {==}
    case S.Literal{a0,a1,a2,a3}: {==}
    case S.Offset{a0,a1,a2}: {==}
    case S.Intrinsic{a0,a1,a2}: {==}
    case S.Sequence{a0}: {==}

def L.irrefutable_first_row_selected(fuel,token,columns,arm,patterns,body,rows,quota,types,scope,work,tree,left,irrefutable,leaf,lowered):
  %lowered : Selected(_,body)
  expanded(fuel,S.Matrix{token,columns,Con{S.Arm{arm,S.Sequence{patterns},body},rows},quota},types,scope,work,body,
    Led{arm,patterns,body,rows,{==},irrefutable,settled(body,leaf)})

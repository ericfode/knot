import Base
import ./syntax.bend as S
import ./core.bend as C
import ./catalog.bend as G
import ./scope.bend as E
import ./patterns.bend as P
import ./literal-types.bend as L

type Alias is Data:
  Alias{token: S.Token, level: U32, quantity: U32}
type Row is Data:
  Row{patterns: List<&2,S.Node>, body: S.Node, aliases: List<&2,Alias>}
type Plan is Data:
  MCase{column: C.Binding, arms: List<&2,Plan>}
  MBranch{tag: U32, fields: List<&2,C.Binding>, body: Plan}
  MDefault{body: Plan}
  MatrixLeaf{scope: E.Scope, body: S.Node}
  MLeaves{values: List<&2,Plan>}
  MArms{values: List<&2,Plan>}
type Mode is Data:
  Rows{rows: List<&2,Row>, columns: List<&2,C.Binding>}
  Constructors{rows: List<&2,Row>, column: C.Binding, columns: List<&2,C.Binding>, constructors: List<&2,C.Constructor>, tag: U32}
  Words{rows: List<&2,Row>, column: C.Binding, columns: List<&2,C.Binding>, values: List<&2,U32>}
  Leaves{rows: List<&2,Row>}

def retoken(name: String, token: S.Token) -> S.Token:
  S.Token{name,S.at(token)}

def literal(node: S.Node) -> S.Node:
  match node:
    case S.Literal{+token,1,+n,codes}:
      S.choose(S.Node,U32.is_eq(n,0),u => S.Constructor{retoken("Zero",token),Nil{}},u =>
        S.Constructor{retoken("Succ",token),[S.Literal{token,1,U32.sub(n,1),Nil{}}]})
    case S.Literal{token,3,number,Nil{}}: S.Constructor{retoken("SNil",token),Nil{}}
    case S.Literal{+token,3,number,Con{head,tail}}:
      S.Constructor{retoken("SCon",token),[S.Literal{token,2,head,Nil{}},S.Literal{token,3,0,tail}]}
    case S.Offset{token,0,tail}: literal(tail)
    case S.Offset{+token,+count,tail}:
      S.Constructor{retoken("Succ",token),[S.Offset{token,U32.sub(count,1),tail}]}
    case _: node

def constructor(reference: G.ConstructorRef, +type_id: U32, +token: S.Token, +args: List<&2,S.Node>, types: List<&2,C.Datatype>) -> Result<S.Error,S.Node>:
  match reference:
    case G.ConstructorRef{+actual,+tag}:
      S.choose(Result<S.Error,S.Node>,U32.is_eq(actual,type_id),u =>
        S.bind(List<&2,C.Parameter>,S.Node,G.field_signature(G.ConstructorRef{actual,tag},types),params =>
          S.choose(Result<S.Error,S.Node>,Nat.is_eq(List.length(&2,S.Node,args),List.length(&2,C.Parameter,params)),u =>
            Done{S.Constructor{token,args}},u => C.invalid(S.Node,"pattern-arity",token))),u => C.invalid(S.Node,"pattern-type",token))

def normalize(fuel: Nat, node: S.Node, +types: List<&2,C.Datatype>, +type_id: U32) -> Result<S.Error,S.Node>:
  match fuel node:
    case 0n _: Fail{S.Exhausted{"check",S.At{0,0,0,0}}}
    case 1n+n S.Literal{+token,+kind,number,codes}:
      S.choose(Result<S.Error,S.Node>,L.is_kind(types,type_id,kind),u => Done{literal(S.Literal{token,kind,number,codes})},u => C.invalid(S.Node,"pattern-type",token))
    case 1n+n S.Offset{+token,+count,+tail}:
      S.choose(Result<S.Error,S.Node>,L.is_kind(types,type_id,1),u =>
        S.choose(Result<S.Error,S.Node>,U32.is_eq(count,0),u => normalize(n,tail,types,type_id),u => Done{literal(S.Offset{token,count,tail})}),u => C.invalid(S.Node,"pattern-type",token))
    case 1n+n S.Constructor{+token,+args}:
      S.choose(Result<S.Error,S.Node>,L.is_kind(types,type_id,2),u => C.unsupported(S.Node,"char-constructor-pattern",token),u =>
        S.bind(G.ConstructorRef,S.Node,G.find_constructor(types,token,0),reference => constructor(reference,type_id,token,args,types)))
    case 1n+n S.Variable{+token}:
      S.choose(Result<S.Error,S.Node>,G.constructor_named(types,token),u => C.invalid(S.Node,"constructor-pattern-binder",token),u => Done{S.Variable{token}})
    case 1n+n S.Promotion{+token}:
      S.choose(Result<S.Error,S.Node>,G.constructor_named(types,token),u => C.invalid(S.Node,"constructor-pattern-binder",token),u => Done{S.Promotion{token}})
    case 1n+n S.Call{token,args}: C.invalid(S.Node,"pattern-form",token)
    case 1n+n _: C.internal(S.Node,"pattern-node")

def normalized(rows: List<&2,Row>, +types: List<&2,C.Datatype>, +type_id: U32, +fuel: Nat) -> Result<S.Error,List<&2,Row>>:
  match rows:
    case Nil{}: Done{Nil{}}
    case Con{Row{Con{head,+patterns},+body,+aliases},+tail}:
      S.bind(S.Node,List<&2,Row>,normalize(fuel,head,types,type_id),+node =>
        S.bind(List<&2,Row>,List<&2,Row>,normalized(tail,types,type_id,fuel),rest => Done{Con{Row{Con{node,patterns},body,aliases},rest}}))
    case _: C.internal(List<&2,Row>,"matrix-width")

def variable(node: S.Node) -> Bool:
  match node:
    case S.Variable{token}: True{}
    case S.Promotion{token}: True{}
    case _: False{}

def all_variables(rows: List<&2,Row>) -> Bool:
  match rows:
    case Nil{}: True{}
    case Con{Row{Con{head,patterns},body,aliases},tail}: Bool.and(variable(head),all_variables(tail))
    case _: False{}

def capture(node: S.Node, column: C.Binding, +aliases: List<&2,Alias>) -> List<&2,Alias>:
  match node column:
    case S.Variable{+token} C.Binding{name,level,q,typ,param,known}:
      S.choose(List<&2,Alias>,S.matches(token,"_"),u => aliases,u => Con{Alias{token,level,q},aliases})
    case S.Promotion{token} C.Binding{name,level,q,typ,param,known}:
      Con{Alias{token,level,Bool.pick(U32,U32.is_eq(q,0),0,2)},aliases}
    case _ _: aliases

def drop_column(rows: List<&2,Row>, +column: C.Binding) -> List<&2,Row>:
  match rows:
    case Nil{}: Nil{}
    case Con{Row{Con{head,patterns},body,aliases},tail}:
      Con{Row{patterns,body,capture(head,column,aliases)},drop_column(tail,column)}
    case _: Nil{}

def wildcards(params: List<&2,C.Parameter>, +token: S.Token) -> List<&2,S.Node>:
  match params:
    case Nil{}: Nil{}
    case Con{head,tail}: Con{S.Variable{retoken("_",token)},wildcards(tail,token)}

def specialize(rows: List<&2,Row>, +column: C.Binding, +name: S.Token, +params: List<&2,C.Parameter>) -> List<&2,Row>:
  match rows:
    case Nil{}: Nil{}
    case Con{Row{Con{S.Constructor{token,+args},+patterns},+body,+aliases},+tail}:
      S.choose(List<&2,Row>,String.eq(S.text(token),S.text(name)),u =>
        Con{Row{List.append(&2,S.Node,args,patterns),body,aliases},specialize(tail,column,name,params)},u => specialize(tail,column,name,params))
    case Con{Row{Con{+head,+patterns},+body,+aliases},+tail}:
      S.choose(List<&2,Row>,variable(head),u =>
        Con{Row{List.append(&2,S.Node,wildcards(params,name),patterns),body,capture(head,column,aliases)},specialize(tail,column,name,params)},u => specialize(tail,column,name,params))
    case _: Nil{}

def specialize_word(rows: List<&2,Row>, +column: C.Binding, +word: Maybe<&2,U32>) -> List<&2,Row>:
  match rows word:
    case Nil{} _: Nil{}
    case Con{Row{Con{S.Literal{token,kind,number,codes},+patterns},+body,+aliases},+tail} Some{+value}:
      S.choose(List<&2,Row>,U32.is_eq(number,value),u => Con{Row{patterns,body,aliases},specialize_word(tail,column,word)},u => specialize_word(tail,column,word))
    case Con{Row{Con{+head,+patterns},+body,+aliases},+tail} _:
      S.choose(List<&2,Row>,variable(head),u => Con{Row{patterns,body,capture(head,column,aliases)},specialize_word(tail,column,word)},u => specialize_word(tail,column,word))
    case _ _: Nil{}

def words(rows: List<&2,Row>, +seen: List<&2,U32>) -> List<&2,U32>:
  match rows:
    case Nil{}: Nil{}
    case Con{Row{Con{S.Literal{token,kind,+number,codes},patterns},body,aliases},+tail}:
      S.choose(List<&2,U32>,E.contains(seen,number),u => words(tail,seen),u => Con{number,words(tail,Con{number,seen})})
    case Con{head,tail}: words(tail,seen)

def renamed(value: C.Binding, token: S.Token, q: U32) -> C.Binding:
  match value:
    case C.Binding{name,level,old,typ,param,known}: C.Binding{token,level,q,typ,param,known}

def alias_scope(binding: C.Binding, scope: E.Scope) -> Result<S.Error,E.Scope>:
  match scope:
    case E.Scope{bindings,next,open,live,smaller}: Done{E.Scope{Con{binding,bindings},next,open,live,smaller}}

def aliases(names: List<&2,Alias>, +scope: E.Scope) -> Result<S.Error,E.Scope>:
  match names scope:
    case Nil{} _: Done{scope}
    case Con{Alias{+token,level,+q},tail} E.Scope{+bindings,+next,+open,+live,+smaller}:
      S.bind(C.Binding,E.Scope,E.find_level(bindings,level),+value =>
        S.bind(E.Scope,E.Scope,aliases(tail,scope),after =>
          alias_scope(renamed(value,token,q),after)))


def fields(params: List<&2,C.Parameter>, +index: U32, +token: S.Token) -> List<&2,S.Node>:
  match params:
    case Nil{}: Nil{}
    case Con{head,tail}:
      Con{S.Variable{retoken(String.append("#",U32.show(index)),token)},fields(tail,U32.add(index,1),token)}

def opened(value: P.Fields, next: E.Scope -> List<&2,C.Binding> -> Result<S.Error,Plan>) -> Result<S.Error,Plan>:
  match value:
    case P.Fields{scope,bindings,args}: next(scope,bindings)

def branch(head: Plan, tail: Plan, tag: U32, bindings: List<&2,C.Binding>) -> Result<S.Error,Plan>:
  match tail:
    case MArms{rest}: Done{MArms{Con{MBranch{tag,bindings,head},rest}}}
    case _: C.internal(Plan,"matrix-branches")

def default_branch(value: Plan) -> Result<S.Error,Plan>:
  Done{MArms{[MDefault{value}]}}

def case_term(value: Plan, column: C.Binding) -> Result<S.Error,Plan>:
  match value:
    case MArms{arms}: Done{MCase{column,arms}}
    case _: C.internal(Plan,"matrix-case")

def leaves(scope: E.Scope, body: S.Node, tail: Plan) -> Result<S.Error,Plan>:
  match tail:
    case MLeaves{rest}: Done{MLeaves{Con{MatrixLeaf{scope,body},rest}}}
    case _: C.internal(Plan,"matrix-leaves")

def datatype(definition: C.Datatype, next: List<&2,C.Constructor> -> Result<S.Error,Plan>) -> Result<S.Error,Plan>:
  match definition:
    case C.Datatype{token,data,ctors}: next(ctors)

def level(binding: C.Binding) -> U32:
  match binding:
    case C.Binding{token,id,q,typ,param,known}: id

def type_id(binding: C.Binding) -> U32:
  match binding:
    case C.Binding{token,id,q,typ,param,known}: typ

def run(fuel: Nat, mode: Mode, +types: List<&2,C.Datatype>, +scope: E.Scope) -> Result<S.Error,Plan>:
  match fuel mode scope:
    case 0n _ _: Fail{S.Exhausted{"check",S.At{0,0,0,0}}}
    case 1n+n Rows{Nil{},columns} _: Fail{S.Invalid{"check","missing-arm",S.At{0,0,0,0}}}
    case 1n+n Rows{rows,Nil{}} _: run(n,Leaves{rows},types,scope)
    case 1n+ +n Rows{rows,Con{+column,+columns}} _:
      S.bind(List<&2,Row>,Plan,normalized(rows,types,type_id(column),n),+values =>
        S.choose(Result<S.Error,Plan>,all_variables(values),u =>
          run(n,Rows{drop_column(values,column),columns},types,scope),u =>
        S.choose(Result<S.Error,Plan>,Bool.or(L.is_kind(types,type_id(column),0),L.is_kind(types,type_id(column),2)),u =>
          S.bind(Plan,Plan,run(n,Words{values,column,columns,words(values,Nil{})},types,scope),v => case_term(v,column)),u =>
          S.bind(C.Datatype,Plan,G.type_at(types,type_id(column)),definition =>
            datatype(definition,ctors => S.bind(Plan,Plan,
              run(n,Constructors{values,column,columns,ctors,0},types,scope),v => case_term(v,column)))))))
    case 1n+ +n Constructors{rows,column,columns,Nil{},tag} _:
      Done{MArms{Nil{}}}
    case 1n+ +n Constructors{+rows,+column,+columns,Con{C.Constructor{+name,+params},+ctors},+tag} E.Scope{bindings,+next,open,live,smaller}:
      S.bind(P.Fields,Plan,P.open_fields(column,scope,tag,fields(params,next,name),params,types),value =>
        opened(value,bound => +introduced =>
          S.bind(Plan,Plan,run(n,Rows{specialize(rows,column,name,params),List.append(&2,C.Binding,introduced,columns)},types,bound),head =>
            S.bind(Plan,Plan,run(n,Constructors{rows,column,columns,ctors,U32.add(tag,1)},types,scope),tail => branch(head,tail,tag,introduced)))))
    case 1n+ +n Words{rows,column,columns,Nil{}} _:
      S.bind(Plan,Plan,run(n,Rows{specialize_word(rows,column,None{}),columns},types,scope),default_branch)
    case 1n+ +n Words{+rows,+column,+columns,Con{+word,+words}} _:
      S.bind(Plan,Plan,run(n,Rows{specialize_word(rows,column,Some{word}),columns},types,E.branch(scope,level(column),word)),head =>
        S.bind(Plan,Plan,run(n,Words{rows,column,columns,words},types,scope),tail => branch(head,tail,word,Nil{})))
    case 1n+n Leaves{Nil{}} _: Done{MLeaves{Nil{}}}
    case 1n+ +n Leaves{Con{Row{Nil{},body,names},+tail}} _:
      S.bind(E.Scope,Plan,aliases(names,scope),bound =>
        S.bind(Plan,Plan,run(n,Leaves{tail},types,scope),rest => leaves(bound,body,rest)))
    case 1n+n Leaves{rows} _: C.internal(Plan,"matrix-leaf")

def rows(arms: List<&2,S.Node>) -> List<&2,Row>:
  match arms:
    case Nil{}: Nil{}
    case Con{S.Arm{token,pattern,body},tail}: Con{Row{[pattern],body,Nil{}},rows(tail)}
    case _: Nil{}

def consumed(body: C.Checked, inspected: C.Checked, +level: U32, token: S.Token) -> Result<S.Error,C.Checked>:
  match body inspected:
    case C.Checked{term,typ,uses} C.Checked{value,source,inputs}:
      S.bind(List<&2,U32>,C.Checked,E.sequential(inputs,E.remove(uses,level),token),merged => Done{C.Checked{term,typ,merged}})

def compile(depth: Nat, binding: C.Binding, arms: List<&2,S.Node>, types: List<&2,C.Datatype>, scope: E.Scope) -> Result<S.Error,Plan>:
  run(depth,Rows{rows(arms),[binding]},types,scope)

def enabled(+types: List<&2,C.Datatype>, binding: C.Binding) -> Bool:
  +id = type_id(binding)
  Bool.or(L.is_kind(types,id,0),Bool.or(L.is_kind(types,id,1),Bool.or(L.is_kind(types,id,2),L.is_kind(types,id,3))))

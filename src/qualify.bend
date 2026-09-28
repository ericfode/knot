import Base
import ./syntax.bend as S

type Alias is Data:
  Alias{name: String, target: String}
type Symbols is Data:
  Symbols{terms: List<&2,String>, constructors: List<&2,String>}
type Parts is Data:
  Parts{head: String, tail: String}
type Names is Data:
  Names{namespace: String, aliases: List<&2,Alias>, globals: List<&2,String>, own: List<&2,String>}
type Qualified is Data:
  Qualified{value: S.Node, binders: List<&2,String>}
type Position is Data:
  Expression{}
  Pattern{}
  ConstructorHeaders{}

def contains(names: List<&2,String>, +name: String) -> Bool:
  match names:
    case Nil{}: False{}
    case Con{head,tail}: Bool.or(String.eq(head,name),contains(tail,name))

def part(c: Char, parts: Parts) -> Parts:
  match parts:
    case Parts{head,tail}: Parts{SCon{c,head},tail}

def split(+name: String) -> Parts:
  match name:
    case SNil{}: Parts{"",""}
    case SCon{+c,+tail}:
      S.choose(Parts,U32.is_eq(Char.to_u32(c),46),u => Parts{"",name},u => part(c,split(tail)))

def alias(aliases: List<&2,Alias>, +name: String) -> Maybe<&2,String>:
  match aliases:
    case Nil{}: None{}
    case Con{Alias{head,+target},+tail}:
      S.choose(Maybe<&2,String>,String.eq(head,name),u => Some{target},u => alias(tail,name))

def member(parts: Parts, aliases: List<&2,Alias>) -> Maybe<&2,String>:
  match parts:
    case Parts{head,SNil{}}: None{}
    case Parts{head,SCon{c,tail}}: alias(aliases,head)

def prefix(+namespace: String, +name: String) -> String:
  S.choose(String,String.is_empty(namespace),u => name,u => String.concat([namespace,".",name]))

def expand(namespace: String, name: String, parts: Parts, target: Maybe<&2,String>) -> String:
  match parts target:
    case _ None{}: prefix(namespace,name)
    case Parts{head,tail} Some{path}: String.append(path,tail)

def retoken(name: String, token: S.Token) -> S.Token:
  match token:
    case S.Token{old,at}: S.Token{name,at}

def invalid(-A: Data, code: String, token: S.Token) -> Result<S.Error,A>:
  Fail{S.Invalid{"load",code,S.at(token)}}

def known(+name: String, names: Names) -> Bool:
  match names:
    case Names{ns,aliases,globals,own}: Bool.or(contains(own,name),contains(globals,name))

def fallback(+qualified: String, +bare: String, +names: Names) -> String:
  Bool.pick(String,Bool.or(known(qualified,names),Bool.not(known(bare,names))),qualified,bare)

def resolved(+token: S.Token, +qualified: String, +aliased: Bool, +names: Names) -> Result<S.Error,S.Token>:
  S.choose(Result<S.Error,S.Token>,Bool.and(aliased,Bool.and(known(qualified,names),known(S.text(token),names))),u =>
    invalid(S.Token,"ambiguous-alias",token),u =>
    Done{retoken(fallback(qualified,S.text(token),names),token)})

def reference(+token: S.Token, +names: Names) -> Result<S.Error,S.Token>:
  match names:
    case Names{+ns,+aliases,globals,own}:
      resolved(token,expand(ns,S.text(token),split(S.text(token)),member(split(S.text(token)),aliases)),
        Maybe.is_some(&2,String,member(split(S.text(token)),aliases)),names)

def local(+token: S.Token, +names: Names, +bound: List<&2,String>) -> Result<S.Error,S.Token>:
  S.choose(Result<S.Error,S.Token>,contains(bound,S.text(token)),u => Done{token},u => reference(token,names))

def fresh(+token: S.Token, +ns: String, +aliases: List<&2,Alias>, +globals: List<&2,String>) -> Result<S.Error,String>:
  S.choose(Result<S.Error,String>,Maybe.is_some(&2,String,member(split(S.text(token)),aliases)),u =>
    invalid(String,"alias-member",token),u =>
    S.choose(Result<S.Error,String>,Bool.or(contains(globals,S.text(token)),contains(globals,prefix(ns,S.text(token)))),u => invalid(String,"duplicate-global",token),u =>
      Done{prefix(ns,S.text(token))}))

def constructors(nodes: List<&2,S.Node>, +ns: String, +aliases: List<&2,Alias>, +globals: List<&2,String>) -> Result<S.Error,List<&2,String>>:
  match nodes:
    case Nil{}: Done{Nil{}}
    case Con{S.Constructor{token,fields},+tail}:
      S.bind(String,List<&2,String>,fresh(token,ns,aliases,globals),head =>
        S.bind(List<&2,String>,List<&2,String>,constructors(tail,ns,aliases,globals),rest => Done{Con{head,rest}}))
    case _: Fail{S.Internal{"load","constructor-node"}}

def declarations(nodes: List<&2,S.Node>, +ns: String, +aliases: List<&2,Alias>, +terms: List<&2,String>, +ctors: List<&2,String>) -> Result<S.Error,List<&2,String>>:
  match nodes:
    case Nil{}: Done{Nil{}}
    case Con{S.Datatype{token,data,+children},+tail}:
      S.bind(String,List<&2,String>,fresh(token,ns,aliases,terms),name =>
        S.bind(List<&2,String>,List<&2,String>,constructors(children,ns,aliases,ctors),cs =>
          S.bind(List<&2,String>,List<&2,String>,declarations(tail,ns,aliases,terms,ctors),rest =>
            Done{Con{name,List.append(&2,String,cs,rest)}})))
    case Con{S.Function{token,params,result,body},+tail}:
      S.bind(String,List<&2,String>,fresh(token,ns,aliases,terms),name =>
        S.bind(List<&2,String>,List<&2,String>,declarations(tail,ns,aliases,terms,ctors),rest => Done{Con{name,rest}}))
    case _: Fail{S.Internal{"load","declaration-node"}}

def constructors_in(nodes: List<&2,S.Node>) -> List<&2,String>:
  match nodes:
    case Nil{}: Nil{}
    case Con{S.Constructor{token,fields},tail}: Con{S.text(token),constructors_in(tail)}
    case Con{other,tail}: constructors_in(tail)

def names_in(nodes: List<&2,S.Node>) -> List<&2,String>:
  match nodes:
    case Nil{}: Nil{}
    case Con{S.Datatype{token,data,ctors},tail}:
      Con{S.text(token),List.append(&2,String,constructors_in(ctors),names_in(tail))}
    case Con{S.Function{token,params,result,body},tail}: Con{S.text(token),names_in(tail)}
    case Con{other,tail}: names_in(tail)

def declaration_names(root: S.Node) -> List<&2,String>:
  match root:
    case S.Sequence{nodes}: names_in(nodes)
    case _: Nil{}

def terms_in(nodes: List<&2,S.Node>) -> List<&2,String>:
  match nodes:
    case Nil{}: Nil{}
    case Con{S.Datatype{token,data,ctors},tail}: Con{S.text(token),terms_in(tail)}
    case Con{S.Function{token,params,result,body},tail}: Con{S.text(token),terms_in(tail)}
    case Con{other,tail}: terms_in(tail)

def ctors_in(nodes: List<&2,S.Node>) -> List<&2,String>:
  match nodes:
    case Nil{}: Nil{}
    case Con{S.Datatype{token,data,ctors},tail}: List.append(&2,String,constructors_in(ctors),ctors_in(tail))
    case Con{other,tail}: ctors_in(tail)

def term_names(root: S.Node) -> List<&2,String>:
  match root:
    case S.Sequence{nodes}: terms_in(nodes)
    case _: Nil{}

def ctor_names(root: S.Node) -> List<&2,String>:
  match root:
    case S.Sequence{nodes}: ctors_in(nodes)
    case _: Nil{}

def introduced(raw: List<&2,String>, names: Names) -> Names:
  match raw names:
    case Nil{} _: names
    case Con{head,tail} Names{+ns,aliases,globals,own}:
      introduced(tail,Names{ns,aliases,globals,Con{prefix(ns,head),own}})

def following(position: Position, node: S.Node, names: Names) -> Names:
  match position node:
    case ConstructorHeaders{} S.Constructor{token,fields}: introduced([S.text(token)],names)
    case _ S.Datatype{token,data,ctors}: introduced(Con{S.text(token),constructors_in(ctors)},names)
    case _ S.Function{token,params,result,body}: introduced([S.text(token)],names)
    case _ _: names

def is_pattern(position: Position) -> Bool:
  match position:
    case Pattern{}: True{}
    case _: False{}

def declared(+token: S.Token, names: Names) -> S.Token:
  match names:
    case Names{ns,aliases,globals,own}: retoken(prefix(ns,S.text(token)),token)

def constructor_token(token: S.Token, names: Names, position: Position) -> Result<S.Error,S.Token>:
  match position:
    case ConstructorHeaders{}: Done{declared(token,names)}
    case _: reference(token,names)

def annotation(value: Maybe<&2,S.Token>, names: Names) -> Result<S.Error,Maybe<&2,S.Token>>:
  match value:
    case None{}: Done{None{}}
    case Some{token}: S.bind(S.Token,Maybe<&2,S.Token>,reference(token,names),t => Done{Some{t}})

def done(value: S.Node) -> Result<S.Error,Qualified>:
  Done{Qualified{value,Nil{}}}

def then(result: Result<S.Error,Qualified>, next: S.Node -> List<&2,String> -> Result<S.Error,Qualified>) -> Result<S.Error,Qualified>:
  match result:
    case Fail{error}: Fail{error}
    case Done{Qualified{value,binders}}: next(value,binders)

def sequence(node: S.Node, next: List<&2,S.Node> -> Result<S.Error,Qualified>) -> Result<S.Error,Qualified>:
  match node:
    case S.Sequence{items}: next(items)
    case _: Fail{S.Internal{"load","sequence-node"}}

def prepend(head: S.Node, binders: List<&2,String>, tail: S.Node, more: List<&2,String>) -> Result<S.Error,Qualified>:
  sequence(tail,items => Done{Qualified{S.Sequence{Con{head,items}},List.append(&2,String,binders,more)}})

def pattern(+token: S.Token, +node: S.Node, +names: Names, +ctors: List<&2,String>) -> Result<S.Error,Qualified>:
  S.bind(S.Token,Qualified,reference(token,names),+resolved =>
    S.choose(Result<S.Error,Qualified>,Bool.and(known(S.text(resolved),names),contains(ctors,S.text(resolved))),u =>
      Fail{S.Invalid{"check","constructor-pattern-binder",S.at(token)}},u =>
      Done{Qualified{node,[S.text(token)]}}))

# A pattern contributes binders; an expression only reads its current scope.
# The same traversal therefore handles parameters, fields and match arms.
def walk_in(fuel: Nat, node: S.Node, +position: Position, +names: Names, +bound: List<&2,String>, +ctors: List<&2,String>) -> Result<S.Error,Qualified>:
  match fuel node:
    case 0n _: Fail{S.Exhausted{"load",S.At{0,0,0,0}}}
    case 1n+ n S.Variable{+token}:
      S.choose(Result<S.Error,Qualified>,is_pattern(position),u => pattern(token,S.Variable{token},names,ctors),u =>
        S.bind(S.Token,Qualified,local(token,names,bound),t => done(S.Variable{t})))
    case 1n+ n S.Promotion{+token}:
      S.choose(Result<S.Error,Qualified>,is_pattern(position),u => pattern(token,S.Promotion{token},names,ctors),u =>
        Done{Qualified{S.Promotion{token},[S.text(token)]}})
    case 1n+ +n S.Constructor{token,args}:
      S.bind(S.Token,Qualified,constructor_token(token,names,position),t =>
        then(walk_in(n,S.Sequence{args},position,names,bound,ctors),items => binders =>
          sequence(items,xs => Done{Qualified{S.Constructor{t,xs},binders}})))
    case 1n+ +n S.Call{token,args}:
      S.bind(S.Token,Qualified,reference(token,names),t =>
        then(walk_in(n,S.Sequence{args},position,names,bound,ctors),items => binders =>
          sequence(items,xs => Done{Qualified{S.Call{t,xs},binders}})))
    case 1n+ +n S.Binding{+token,q,ann,value,+body}:
      S.bind(Maybe<&2,S.Token>,Qualified,annotation(ann,names),a =>
        then(walk_in(n,value,Expression{},names,bound,ctors),v => ignored =>
          then(walk_in(n,body,Expression{},names,Con{S.text(token),bound},ctors),b => unused =>
            done(S.Binding{token,q,a,v,b}))))
    case 1n+ +n S.Match{token,value,+arms}:
      then(walk_in(n,value,Expression{},names,bound,ctors),v => ignored =>
        then(walk_in(n,S.Sequence{arms},Expression{},names,bound,ctors),items => unused =>
          sequence(items,xs => done(S.Match{token,v,xs}))))
    case 1n+ +n S.Arm{token,pat,+body}:
      then(walk_in(n,pat,Pattern{},names,bound,ctors),p => binders =>
        then(walk_in(n,body,Expression{},names,List.append(&2,String,binders,bound),ctors),b => ignored =>
          done(S.Arm{token,p,b})))
    case 1n+ n S.Parameter{+token,q,typ}:
      S.bind(S.Token,Qualified,reference(typ,names),t => Done{Qualified{S.Parameter{token,q,t},[S.text(token)]}})
    case 1n+ +n S.Datatype{+token,data,children}:
      then(walk_in(n,S.Sequence{children},ConstructorHeaders{},introduced([S.text(token)],names),Nil{},ctors),items => ignored =>
        sequence(items,xs => done(S.Datatype{declared(token,names),data,xs})))
    case 1n+ +n S.Function{+token,params,+result,+body}:
      then(walk_in(n,S.Sequence{params},Expression{},names,Nil{},ctors),items => binders =>
        sequence(items,xs =>
          S.bind(S.Token,Qualified,reference(result,names),t =>
            then(walk_in(n,body,Expression{},introduced([S.text(token)],names),binders,ctors),b => ignored =>
              done(S.Function{declared(token,names),xs,t,b})))))
    case 1n+ n S.Sequence{Nil{}}: done(S.Sequence{Nil{}})
    case 1n+ +n S.Sequence{Con{+head,+tail}}:
      then(walk_in(n,head,position,names,bound,ctors),h => binders =>
        then(walk_in(n,S.Sequence{tail},position,following(position,head,names),bound,ctors),t => more => prepend(h,binders,t,more)))

def walk(fuel: Nat, node: S.Node, position: Position, names: Names, bound: List<&2,String>) -> Result<S.Error,Qualified>:
  walk_in(fuel,node,position,names,bound,Nil{})

def prefixed(+namespace: String, names: List<&2,String>) -> List<&2,String>:
  match names:
    case Nil{}: Nil{}
    case Con{head,tail}: Con{prefix(namespace,head),prefixed(namespace,tail)}

def result(value: Qualified) -> Result<S.Error,S.Node>:
  match value:
    case Qualified{node,binders}: Done{node}

# Globals contains declarations already loaded, including unchecked Base names.
# Qualification does not remove declarations or decide whether their bodies typecheck.
def qualify(+namespace: String, +aliases: List<&2,Alias>, globals: Symbols, root: S.Node) -> Result<S.Error,S.Node>:
  match globals root:
    case Symbols{+terms,+ctors} S.Sequence{+items}:
      S.bind(List<&2,String>,S.Node,declarations(items,namespace,aliases,terms,ctors),checked =>
        S.bind(Qualified,S.Node,walk_in(65536n,S.Sequence{items},Expression{},Names{namespace,aliases,List.append(&2,String,terms,ctors),Nil{}},Nil{},
          List.append(&2,String,ctors,prefixed(namespace,ctors_in(items)))),result))
    case _ _: Fail{S.Internal{"load","book-node"}}

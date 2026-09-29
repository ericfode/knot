import Base
import ./syntax.bend as S
import ./lex.bend as L
import ./parse.bend as P
import ./literal-base.bend as R

type Decl is Data:
  Decl{name: String, names: List<&2,String>, source: String, unsafe: Bool}

type Piece is Data:
  Piece{name: String, names: List<&2,String>, lines: List<&2,String>, datatype: Bool, unsafe: Bool}

type Selected is Data:
  Selected{name: String, node: S.Node}

type Use is Data:
  Use{name: String, constructor: Bool}

type Slice is Data:
  Slice{tree: S.Node, checked: List<&2,String>, unchecked: List<&2,String>}

def review_prefix(value: Maybe<&2,S.Node>) -> String:
  match value:
    case None{}: "BaseChecked\t"
    case Some{node}: "BaseIntrinsic\t"

def review(names: List<&2,String>) -> String:
  match names:
    case Nil{}: ""
    case Con{+name,tail}: String.concat([review_prefix(R.declaration(name)),name,"\n",review(tail)])

def member(names: List<&2,String>, +name: String) -> Bool:
  match names:
    case Nil{}: False{}
    case Con{h,t}: Bool.or(String.eq(h,name),member(t,name))

def word(text: String) -> String:
  match text:
    case SNil{}: SNil{}
    case SCon{+h,+t}:
      S.choose(String,S.word(Char.to_u32(h)),u => SCon{h,word(t)},u => SNil{})

def header(+line: String) -> Maybe<&2,String>:
  S.choose(Maybe<&2,String>,Bool.or(String.starts_with(line,"def "),String.starts_with(line,"law ")),u =>
    Some{word(String.drop(line,4n))},u =>
  S.choose(Maybe<&2,String>,String.starts_with(line,"type "),u =>
    Some{word(String.drop(line,5n))},u => None{}))

def ctor(+line: String) -> Maybe<&2,String>:
  +body = String.drop(line,2n)
  +name = word(body)
  S.choose(Maybe<&2,String>,Bool.and(String.starts_with(line,"  "),
    Bool.and(S.identifier_text(name),String.starts_with(String.drop(body,String.length(name)),"{"))),u =>
      Some{name},u => None{})

def added(name: Maybe<&2,String>, names: List<&2,String>) -> List<&2,String>:
  match name:
    case None{}: names
    case Some{value}: Con{value,names}

def line_in(+line: String, piece: Piece) -> Piece:
  match piece:
    case Piece{name,+names,lines,+datatype,unsafe}:
      Piece{name,S.choose(List<&2,String>,datatype,u => added(ctor(line),names),u => names),
        Con{line,lines},datatype,unsafe}

def finish_piece(piece: Piece) -> Decl:
  match piece:
    case Piece{name,names,lines,datatype,unsafe}:
      Decl{name,List.reverse(&2,String,names),String.append(String.join(List.reverse(&2,String,lines),"\n"),"\n"),unsafe}

def finish(piece: Maybe<&2,Piece>, done: List<&2,Decl>) -> List<&2,Decl>:
  match piece:
    case None{}: done
    case Some{value}: Con{finish_piece(value),done}

def extend(line: String, piece: Maybe<&2,Piece>) -> Maybe<&2,Piece>:
  match piece:
    case None{}: None{}
    case Some{value}: Some{line_in(line,value)}

def index_line(name: Maybe<&2,String>, +line: String,
  +piece: Maybe<&2,Piece>, +unsafe: Bool, +done: List<&2,Decl>,
  next: Maybe<&2,Piece> -> Bool -> List<&2,Decl> -> List<&2,Decl>) -> List<&2,Decl>:
  match name:
    case None{}: next(extend(line,piece),unsafe,done)
    case Some{+value}:
      next(Some{Piece{value,[value],[line],String.starts_with(line,"type "),unsafe}},False{},finish(piece,done))

# The pinned source has column-zero headers and two-space constructor rows.
# Inventory is lexical: unreachable declarations are retained without checking.
def index(lines: List<&2,String>, +piece: Maybe<&2,Piece>, +unsafe: Bool,
  +done: List<&2,Decl>) -> List<&2,Decl>:
  match lines:
    case Nil{}: List.reverse(&2,Decl,finish(piece,done))
    case Con{+line,+tail}:
      S.choose(List<&2,Decl>,String.eq(line,"@unsafe"),u => index(tail,piece,True{},done),u =>
        index_line(header(line),line,piece,unsafe,done,
          value => flag => values => index(tail,value,flag,values)))

def merge(book: List<&2,Decl>, +declaration: Decl) -> List<&2,Decl>:
  match book:
    case Nil{}: [declaration]
    case Con{Decl{+name,+values,+source,+unsafe},+tail}:
      match declaration:
        case Decl{next,other,text,flag}:
          S.choose(List<&2,Decl>,String.eq(name,next),u =>
            Con{Decl{name,values,String.append(source,text),Bool.or(unsafe,flag)},tail},u =>
            Con{Decl{name,values,source,unsafe},merge(tail,declaration)})

def coalesce(events: List<&2,Decl>, book: List<&2,Decl>) -> List<&2,Decl>:
  match events:
    case Nil{}: book
    case Con{head,tail}: coalesce(tail,merge(book,head))

def lines(text: String, +line: String, +done: List<&2,String>) -> List<&2,String>:
  match text:
    case SNil{}: List.reverse(&2,String,Con{String.reverse(line),done})
    case SCon{+c,+tail}:
      S.choose(List<&2,String>,Char.is_eq(c,'\n'),u =>
        lines(tail,"",Con{String.reverse(line),done}),u => lines(tail,SCon{c,line},done))

# A law and its later filling definition are one loaded book entry.
def inventory(text: String) -> List<&2,Decl>:
  coalesce(index(lines(text,"",Nil{}),None{},False{},Nil{}),Nil{})

def names(book: List<&2,Decl>) -> List<&2,String>:
  match book:
    case Nil{}: Nil{}
    case Con{Decl{name,values,source,unsafe},tail}: List.append(&2,String,values,names(tail))

def term_names(book: List<&2,Decl>) -> List<&2,String>:
  match book:
    case Nil{}: Nil{}
    case Con{Decl{name,values,source,unsafe},tail}: Con{name,term_names(tail)}

def ctor_names(book: List<&2,Decl>) -> List<&2,String>:
  match book:
    case Nil{}: Nil{}
    case Con{Decl{name,values,source,unsafe},tail}:
      List.append(&2,String,List.tail(&2,String,values),ctor_names(tail))

def lookup(book: List<&2,Decl>, +name: String) -> Maybe<&2,Decl>:
  match book:
    case Nil{}: None{}
    case Con{+head,+tail}:
      match head:
        case Decl{primary,values,source,unsafe}:
          S.choose(Maybe<&2,Decl>,String.eq(primary,name),u => Some{head},u => lookup(tail,name))

def lookup_use(book: List<&2,Decl>, +reference: Use) -> Maybe<&2,Decl>:
  match book:
    case Nil{}: None{}
    case Con{+head,+tail}:
      match head reference:
        case Decl{+primary,+values,source,unsafe} Use{+name,constructor}:
          S.choose(Maybe<&2,Decl>,S.choose(Bool,constructor,u => member(List.tail(&2,String,values),name),u =>
            String.eq(primary,name)),u => Some{head},u => lookup_use(tail,reference))

def has(uses: List<&2,Use>, +name: String, +constructor: Bool) -> Bool:
  match uses:
    case Nil{}: False{}
    case Con{Use{key,kind},tail}:
      Bool.or(Bool.and(String.eq(key,name),Bool.not(Bool.xor(kind,constructor))),has(tail,name,constructor))

def identity(declaration: Maybe<&2,Decl>) -> List<&2,String>:
  match declaration:
    case None{}: Nil{}
    case Some{Decl{name,values,source,unsafe}}: [name]

def dependencies(uses: List<&2,Use>, +book: List<&2,Decl>, +shadow: List<&2,Use>) -> List<&2,String>:
  match uses:
    case Nil{}: Nil{}
    case Con{+reference,+tail}:
      match reference:
        case Use{+name,+constructor}:
          S.choose(List<&2,String>,has(shadow,name,constructor),u => dependencies(tail,book,shadow),u =>
            List.append(&2,String,identity(lookup_use(book,reference)),dependencies(tail,book,shadow)))

def parameters(nodes: List<&2,S.Node>) -> List<&2,String>:
  match nodes:
    case Nil{}: Nil{}
    case Con{S.Parameter{token,q,typ},tail}: Con{S.text(token),parameters(tail)}
    case Con{head,tail}: parameters(tail)

def fields(nodes: List<&2,S.Node>) -> List<&2,S.Node>:
  match nodes:
    case Nil{}: Nil{}
    case Con{S.Constructor{token,args},tail}: List.append(&2,S.Node,args,fields(tail))
    case Con{head,tail}: fields(tail)

def pattern_names(nodes: List<&2,S.Node>) -> List<&2,String>:
  match nodes:
    case Nil{}: Nil{}
    case Con{S.Variable{token},tail}: Con{S.text(token),pattern_names(tail)}
    case Con{S.Promotion{token},tail}: Con{S.text(token),pattern_names(tail)}
    case Con{head,tail}: pattern_names(tail)

def pattern_scope(node: S.Node, scope: List<&2,String>) -> List<&2,String>:
  match node:
    case S.Variable{token}: Con{S.text(token),scope}
    case S.Constructor{token,args}: List.append(&2,String,pattern_names(args),scope)
    case S.Offset{token,count,tail}: pattern_scope(tail,scope)
    case S.Promotion{token}: Con{S.text(token),scope}
    case _: scope

def free(+token: S.Token, scope: List<&2,String>) -> List<&2,Use>:
  S.choose(List<&2,Use>,member(scope,S.text(token)),u => Nil{},u => [Use{S.text(token),False{}}])

def annotation(token: Maybe<&2,S.Token>) -> List<&2,Use>:
  match token:
    case None{}: Nil{}
    case Some{value}: [Use{S.text(value),False{}}]

# Declaration names and lexical binders are not dependency edges.
def references(depth: Nat, node: S.Node, +scope: List<&2,String>) -> Result<S.Error,List<&2,Use>>:
  match depth node:
    case 0n _: Fail{S.Exhausted{"base-references",S.At{0,0,0,0}}}
    case 1n+n S.Literal{token,kind,number,text}: Done{[Use{R.kind_name(kind),False{}}]}
    case 1n+n S.Offset{token,count,tail}:
      S.bind(List<&2,Use>,List<&2,Use>,references(n,tail,scope),refs => Done{Con{Use{"Nat",False{}},refs}})
    case 1n+n S.Intrinsic{token,op,args}: references(n,S.Sequence{args},scope)
    case 1n+n S.Variable{token}: Done{free(token,scope)}
    case 1n+n S.Promotion{token}: Done{free(token,scope)}
    case 1n+ +n S.Constructor{+token,args}:
      S.bind(List<&2,Use>,List<&2,Use>,references(n,S.Sequence{args},scope),refs => Done{Con{Use{S.text(token),True{}},refs}})
    case 1n+ +n S.Call{+token,args}:
      S.bind(List<&2,Use>,List<&2,Use>,references(n,S.Sequence{args},scope),refs => Done{List.append(&2,Use,free(token,scope),refs)})
    case 1n+ +n S.Binding{+token,q,+typ,value,+body}:
      S.bind(List<&2,Use>,List<&2,Use>,references(n,value,scope),before =>
        S.bind(List<&2,Use>,List<&2,Use>,references(n,body,Con{S.text(token),scope}),after =>
          Done{List.concat(&2,Use,[annotation(typ),before,after])}))
    case 1n+ +n S.Match{token,value,+arms}:
      S.bind(List<&2,Use>,List<&2,Use>,references(n,value,scope),before =>
        S.bind(List<&2,Use>,List<&2,Use>,references(n,S.Sequence{arms},scope),after =>
          Done{List.append(&2,Use,before,after)}))
    case 1n+ +n S.Arm{token,+pattern,+body}:
      +bound = pattern_scope(pattern,scope)
      S.bind(List<&2,Use>,List<&2,Use>,references(n,pattern,bound),before =>
        S.bind(List<&2,Use>,List<&2,Use>,references(n,body,bound),after =>
          Done{List.append(&2,Use,before,after)}))
    case 1n+n S.Parameter{token,q,typ}: Done{[Use{S.text(typ),False{}}]}
    case 1n+n S.Datatype{token,data,ctors}: references(n,S.Sequence{fields(ctors)},scope)
    case 1n+ +n S.Function{token,+params,+result,+body}:
      S.bind(List<&2,Use>,List<&2,Use>,references(n,S.Sequence{params},scope),types =>
        S.bind(List<&2,Use>,List<&2,Use>,references(n,body,List.append(&2,String,parameters(params),scope)),calls =>
          Done{Con{Use{S.text(result),False{}},List.append(&2,Use,types,calls)}}))
    case 1n+n S.Sequence{Nil{}}: Done{Nil{}}
    case 1n+ +n S.Sequence{Con{head,+tail}}:
      S.bind(List<&2,Use>,List<&2,Use>,references(n,head,scope),first =>
        S.bind(List<&2,Use>,List<&2,Use>,references(n,S.Sequence{tail},scope),rest =>
          Done{List.append(&2,Use,first,rest)}))

def base_error(error: S.Error) -> S.Error:
  match error:
    case S.Invalid{phase,code,at}: S.Unsupported{"load",String.append("base-",code),at}
    case _: error

def empty_type(nodes: List<&2,S.Node>) -> Maybe<&2,S.Token>:
  match nodes:
    case Nil{}: None{}
    case Con{S.Datatype{token,data,Nil{}},tail}: Some{token}
    case Con{head,tail}: empty_type(tail)

def nonempty(empty: Maybe<&2,S.Token>, tree: S.Node) -> Result<S.Error,S.Node>:
  match empty:
    case None{}: Done{tree}
    case Some{token}: Fail{S.Unsupported{"check","base-empty-datatype",S.at(token)}}

def parsed(result: Result<S.Error,P.Parsed>) -> Result<S.Error,S.Node>:
  match result:
    case Fail{error}: Fail{base_error(error)}
    case Done{P.Parsed{S.Sequence{+items},rest}}: nonempty(empty_type(items),S.Sequence{items})
    case Done{P.Parsed{value,rest}}: Fail{S.Internal{"load","base-book"}}

def tokens(+depth: Nat, result: Result<S.Error,List<&2,S.Token>>) -> Result<S.Error,S.Node>:
  match result:
    case Fail{error}: Fail{base_error(error)}
    case Done{values}: parsed(P.parse(depth,values))

def lowered(value: Maybe<&2,S.Node>, next: Unit -> Result<S.Error,S.Node>) -> Result<S.Error,S.Node>:
  match value:
    case None{}: next(Unit{})
    case Some{node}: Done{S.Sequence{[node]}}

def parse(+depth: Nat, declaration: Decl) -> Result<S.Error,S.Node>:
  match declaration:
    case Decl{name,values,+source,+unsafe}:
      S.choose(Result<S.Error,S.Node>,unsafe,u => Fail{S.Unsupported{"load","base-unsafe",S.At{0,0,0,0}}},u =>
      S.choose(Result<S.Error,S.Node>,String.contains(source,"\n  import \""),u =>
        Fail{S.Unsupported{"check","foreign-definition",S.At{0,0,0,0}}},u =>
        lowered(R.declaration(name),u => tokens(depth,L.tokenize(String.length(source),source)))))

def selected(items: List<&2,Selected>, +name: String) -> Maybe<&2,S.Node>:
  match items:
    case Nil{}: None{}
    case Con{Selected{key,+node},+tail}:
      S.choose(Maybe<&2,S.Node>,String.eq(key,name),u => Some{node},u => selected(tail,name))

def nodes(node: S.Node) -> List<&2,S.Node>:
  match node:
    case S.Sequence{items}: items
    case _: [node]

def constructors(nodes: List<&2,S.Node>) -> List<&2,Use>:
  match nodes:
    case Nil{}: Nil{}
    case Con{S.Constructor{token,args},tail}: Con{Use{S.text(token),True{}},constructors(tail)}
    case Con{head,tail}: constructors(tail)

def declarations(nodes: List<&2,S.Node>) -> List<&2,Use>:
  match nodes:
    case Nil{}: Nil{}
    case Con{S.Function{token,params,result,body},tail}: Con{Use{S.text(token),False{}},declarations(tail)}
    case Con{S.Datatype{token,data,ctors},tail}:
      Con{Use{S.text(token),False{}},List.append(&2,Use,constructors(ctors),declarations(tail))}
    case Con{head,tail}: declarations(tail)

def put_selection(+name: String, node: Maybe<&2,S.Node>, tail: Slice) -> Slice:
  match node tail:
    case None{} Slice{tree,checked,unchecked}: Slice{tree,checked,Con{name,unchecked}}
    case Some{value} Slice{tree,checked,unchecked}:
      Slice{S.Sequence{List.append(&2,S.Node,nodes(value),nodes(tree))},Con{name,checked},unchecked}

# Partition follows source order, independently of discovery order.
def partition(book: List<&2,Decl>, +items: List<&2,Selected>) -> Slice:
  match book:
    case Nil{}: Slice{S.Sequence{Nil{}},Nil{},Nil{}}
    case Con{Decl{+name,values,source,unsafe},tail}:
      put_selection(name,selected(items,name),partition(tail,items))

def visit_tree(parser: Nat, +name: String, +book: List<&2,Decl>, +pending: List<&2,String>,
  +seen: List<&2,String>, +items: List<&2,Selected>, +tree: S.Node,
  next: List<&2,String> -> List<&2,String> -> List<&2,Selected> -> Result<S.Error,Slice>) -> Result<S.Error,Slice>:
  S.bind(List<&2,Use>,Slice,references(parser,tree,Nil{}),refs =>
    next(List.append(&2,String,dependencies(refs,book,Nil{}),pending),Con{name,seen},Con{Selected{name,tree},items}))

def visit_decl(+parser: Nat, declaration: Maybe<&2,Decl>, +book: List<&2,Decl>, +pending: List<&2,String>,
  +seen: List<&2,String>, +items: List<&2,Selected>,
  next: List<&2,String> -> List<&2,String> -> List<&2,Selected> -> Result<S.Error,Slice>) -> Result<S.Error,Slice>:
  match declaration:
    case None{}: next(pending,seen,items)
    case Some{+decl}:
      match decl:
        case Decl{+name,+values,source,unsafe}:
          S.bind(S.Node,Slice,parse(parser,decl),tree =>
            visit_tree(parser,name,book,pending,seen,items,tree,next))

def visit(depth: Nat, +parser: Nat, pending: List<&2,String>, +book: List<&2,Decl>,
  +seen: List<&2,String>, +items: List<&2,Selected>) -> Result<S.Error,Slice>:
  match depth pending:
    case _ Nil{}: Done{partition(book,items)}
    case 0n Con{h,t}: Fail{S.Exhausted{"base-slice",S.At{0,0,0,0}}}
    case 1n+ +n Con{+name,+tail}:
      S.choose(Result<S.Error,Slice>,member(seen,name),u => visit(n,parser,tail,book,seen,items),u =>
        visit_decl(parser,lookup(book,name),book,tail,seen,items,
          todo => visited => selected_items => visit(n,parser,todo,book,visited,selected_items)))

def slice(+depth: Nat, +book: List<&2,Decl>, +roots: S.Node) -> Result<S.Error,Slice>:
  S.bind(List<&2,Use>,Slice,references(depth,roots,Nil{}),refs =>
    visit(depth,depth,dependencies(refs,book,Nil{}),book,Nil{},Nil{}))

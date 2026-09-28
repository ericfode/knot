import Base
import ./syntax.bend as S
import ./lex.bend as L
import ./parse.bend as P
import ./imports.bend as I
import ./qualify.bend as Q
import ./base-load.bend as B
import ./base-pin.bend as H
import ./path-host.bend as F

type Receipt is Data:
  Receipt{tree: S.Node, files: List<&2,String>, checked_base: List<&2,String>, unchecked_base: List<&2,String>}

type State is Data:
  State{done: List<&2,String>, active: List<&2,String>, reversed: List<&2,S.Node>, globals: Q.Symbols, base: List<&2,B.Decl>, has_base: Bool}

type Input is Data:
  Contents{text: String}
  ReadError{error: S.Error}

type Step is Data:
  Visit{path: String, namespace: String, entry: Bool}
  Imports{path: String, namespace: String, remaining: List<&2,I.Import>, aliases: List<&2,Q.Alias>, body: String}
  Source{path: String, namespace: String, result: Input}
  BaseSource{result: Input}

type Origin is Data:
  UserSource{path: String, namespace: String}
  PinnedBase{}

type Action is Data:
  Stopped{error: S.Error}
  Finished{receipt: Receipt}
  Advance{tasks: List<&2,Step>, state: State}
  Read{path: String, cap: U32, missing: Bool, origin: Origin, tasks: List<&2,Step>, state: State}

def base_path() -> String:
  ".toolchain/bend-2.0.29-574b6d3/bend2/base.bend"

def base_hash() -> String:
  H.expected()

def known(path: String, state: State) -> Bool:
  match state:
    case State{done,active,reversed,globals,base,has_base}: I.member(path,done)

def cyclic(path: String, state: State) -> Bool:
  match state:
    case State{done,active,reversed,globals,base,has_base}: I.member(path,active)

def enter(path: String, state: State) -> State:
  match state:
    case State{done,active,reversed,globals,base,has_base}:
      State{done,Con{path,active},reversed,globals,base,has_base}

def has_base(state: State) -> Bool:
  match state:
    case State{done,active,reversed,globals,base,loaded}: loaded

def base_names(state: State) -> Q.Symbols:
  match state:
    case State{done,active,reversed,globals,base,loaded}: globals

def symbols(left: Q.Symbols, right: Q.Symbols) -> Q.Symbols:
  match left right:
    case Q.Symbols{lt,lc} Q.Symbols{rt,rc}:
      Q.Symbols{List.append(&2,String,lt,rt),List.append(&2,String,lc,rc)}

def overlaps(left: List<&2,String>, +right: List<&2,String>) -> Bool:
  match left:
    case Nil{}: False{}
    case Con{head,tail}: Bool.or(Q.contains(right,head),overlaps(tail,right))

def collides(left: Q.Symbols, right: Q.Symbols) -> Bool:
  match left right:
    case Q.Symbols{lt,lc} Q.Symbols{rt,rc}: Bool.or(overlaps(lt,rt),overlaps(lc,rc))

def install_base(+text: String, state: State) -> Result<S.Error,State>:
  match state:
    case State{+done,+active,+reversed,+globals,base,loaded}:
      +inventory = B.inventory(text)
      +names : Q.Symbols = Q.Symbols{B.term_names(inventory),B.ctor_names(inventory)}
      S.choose(Result<S.Error,State>,collides(globals,names),u =>
        Fail{S.Invalid{"load","duplicate-global",S.At{0,0,0,0}}},u =>
        Done{State{done,active,reversed,symbols(globals,names),inventory,True{}}})

def leave(path: String, +tree: S.Node, state: State) -> Result<S.Error,State>:
  match tree state:
    case S.Sequence{items} State{done,Con{head,active},reversed,globals,base,loaded}:
      Done{State{Con{path,done},active,List.append(&2,S.Node,List.reverse(&2,S.Node,items),reversed),
        symbols(globals,Q.Symbols{Q.term_names(tree),Q.ctor_names(tree)}),base,loaded}}
    case _ _: Fail{S.Internal{"load","module-stack"}}

def parsed(value: P.Parsed) -> S.Node:
  match value:
    case P.Parsed{tree,rest}: tree

def body(+characters: Nat, +depth: Nat, +namespace: String, +aliases: List<&2,Q.Alias>,
  +globals: Q.Symbols, text: String) -> Result<S.Error,S.Node>:
  S.bind(List<&2,S.Token>,S.Node,L.tokenize(characters,text),tokens =>
    S.bind(P.Parsed,S.Node,P.parse(depth,tokens),tree => Q.qualify(namespace,aliases,globals,parsed(tree))))

def joined(base: S.Node, root: S.Node) -> Result<S.Error,S.Node>:
  match base root:
    case S.Sequence{left} S.Sequence{right}: Done{S.Sequence{List.append(&2,S.Node,left,right)}}
    case _ _: Fail{S.Internal{"load","expected-book"}}

def sliced(+root: S.Node, +files: List<&2,String>, value: Result<S.Error,B.Slice>) -> Result<S.Error,Receipt>:
  match value:
    case Fail{error}: Fail{error}
    case Done{B.Slice{base,+checked,+unchecked}}:
      S.bind(S.Node,Receipt,joined(base,root),tree => Done{Receipt{tree,files,checked,unchecked}})

def finish(depth: Nat, state: State) -> Result<S.Error,Receipt>:
  match state:
    case State{done,active,reversed,globals,base,loaded}:
      +root : S.Node = S.Sequence{List.reverse(&2,S.Node,reversed)}
      sliced(root,List.reverse(&2,String,done),B.slice(depth,base,root))

def read_result(result: Result<&1,&1,U32 & String,String>, next: Result<S.Error,String> -> IO(Unit)) -> IO(Unit):
  match result:
    case Fail{(code,message)}: next(Fail{S.Host{"read",String.concat([U32.show(code),"\t",message])}})
    case Done{text}: next(Done{text})

def read_pair(pair: File & Result<&1,&1,U32 & String,String>, next: Result<S.Error,String> -> IO(Unit)) -> IO(Unit):
  (file,result) = pair
  do IO<Unit>:
    File.close(file)
    read_result(result,next)

def opened(result: Result<&1,&1,U32 & String,File>, cap: U32, +missing: Bool,
  next: Result<S.Error,String> -> IO(Unit)) -> IO(Unit):
  match result:
    case Fail{(+code,message)}:
      next(S.choose(Result<S.Error,String>,Bool.and(missing,Bool.or(U32.is_eq(code,2),U32.is_eq(code,20))),u =>
        Fail{S.Invalid{"load","missing-module",S.At{0,0,0,0}}},u =>
        Fail{S.Host{"open",String.concat([U32.show(code),"\t",message])}}))
    case Done{file}:
      IO.bind(File & Result<&1,&1,U32 & String,String>,Unit,File.read(file,cap),pair => read_pair(pair,next))

def read(path: String, +cap: U32, +missing: Bool, next: Result<S.Error,String> -> IO(Unit)) -> IO(Unit):
  IO.bind(Result<&1,&1,U32 & String,File>,Unit,File.open(path,"r"),result => opened(result,cap,missing,next))

def read_canonical(result: Result<S.Error,Unit>, path: String, cap: U32, missing: Bool,
  next: Result<S.Error,String> -> IO(Unit)) -> IO(Unit):
  match result:
    case Fail{error}: next(Fail{error})
    case Done{unit}: read(path,cap,missing,next)

def read_source(+path: String, +cap: U32, +missing: Bool, origin: Origin,
  next: Result<S.Error,String> -> IO(Unit)) -> IO(Unit):
  match origin:
    case UserSource{file,namespace}:
      F.check(path,result => read_canonical(result,path,cap,missing,next))
    case PinnedBase{}: read(path,cap,missing,next)

def received(result: Result<S.Error,String>) -> Input:
  match result:
    case Fail{error}: ReadError{error}
    case Done{text}: Contents{text}

def stopped(result: Result<S.Error,Receipt>) -> Action:
  match result:
    case Fail{error}: Stopped{error}
    case Done{receipt}: Finished{receipt}

def step_header(result: Result<S.Error,I.Header>, +path: String, +namespace: String,
  tail: List<&2,Step>, state: State) -> Action:
  match result:
    case Fail{error}: Stopped{error}
    case Done{I.Header{imports,body}}: Advance{Con{Imports{path,namespace,imports,Nil{},body},tail},state}

def width(+code: U32) -> Nat:
  S.choose(Nat,U32.is_lt(code,128),u => 1n,u =>
  S.choose(Nat,U32.is_lt(code,2048),u => 2n,u =>
  S.choose(Nat,U32.is_lt(code,65536),u => 3n,u => 4n)))

# The budget counts UTF-8 bytes. Decoding never shortens input (a malformed
# subpart becomes one three-byte U+FFFD), so text within the budget was read whole.
def within(text: String, +budget: Nat) -> Bool:
  match text:
    case SNil{}: True{}
    case SCon{c,tail}:
      +cost = width(Char.to_u32(c))
      S.choose(Bool,Nat.is_le(cost,budget),u => within(tail,Nat.sub(budget,cost)),u => False{})

def step_source(result: Input, +path: String, +namespace: String, +characters: Nat,
  +tail: List<&2,Step>, +state: State) -> Action:
  match result:
    case ReadError{error}: Stopped{error}
    case Contents{+text}:
      S.choose(Action,within(text,characters),u => step_header(I.header(text),path,namespace,tail,state),u =>
        Stopped{S.Exhausted{"lex",S.At{0,0,0,0}}})

def step_state(result: Result<S.Error,State>, tail: List<&2,Step>) -> Action:
  match result:
    case Fail{error}: Stopped{error}
    case Done{after}: Advance{tail,after}

def checked_base(result: Result<S.Error,String>, tail: List<&2,Step>, state: State) -> Action:
  match result:
    case Fail{error}: Stopped{error}
    case Done{text}: step_state(install_base(text,state),tail)

def step_base(result: Input, tail: List<&2,Step>, state: State) -> Action:
  match result:
    case ReadError{error}: Stopped{error}
    case Contents{text}: checked_base(H.verify(text),tail,state)

def step_target(result: Result<S.Error,I.Target>, +alias: String, +path: String, +namespace: String,
  +remaining: List<&2,I.Import>, +aliases: List<&2,Q.Alias>, +text: String,
  tail: List<&2,Step>, state: State) -> Action:
  match result:
    case Fail{error}: Stopped{error}
    case Done{I.Target{target,+space}}:
      Advance{Con{Visit{target,space,False{}},Con{Imports{path,namespace,remaining,Con{Q.Alias{alias,space},aliases},text},tail}},state}

def step_body(result: Result<S.Error,S.Node>, +path: String, +state: State,
  tail: List<&2,Step>) -> Action:
  match result:
    case Fail{error}: Stopped{error}
    case Done{tree}: step_state(leave(path,tree,state),tail)

# The stack contains suspended import headers; active and done distinguish a
# back edge from a shared dependency. Only the Base inventory is sliced.
def plan(tasks: List<&2,Step>, +state: State, +bundle: String, +characters: Nat, +depth: Nat) -> Action:
  match tasks:
    case Nil{}: stopped(finish(depth,state))
    case Con{Visit{+path,+namespace,+entry},+tail}:
      S.choose(Action,cyclic(path,state),u => Stopped{S.Invalid{"load","cycle",S.At{0,0,0,0}}},u =>
      S.choose(Action,known(path,state),u => Advance{tail,state},u =>
        Read{path,65537,Bool.not(entry),UserSource{path,namespace},tail,enter(path,state)}))
    case Con{Source{path,namespace,result},tail}: step_source(result,path,namespace,characters,tail,state)
    case Con{BaseSource{result},tail}: step_base(result,tail,state)
    case Con{Imports{+path,+namespace,Nil{},aliases,text},+tail}:
      step_body(body(characters,depth,namespace,aliases,base_names(state),text),path,state,tail)
    case Con{Imports{+path,+namespace,Con{I.Import{+target,+alias},+rest},+aliases,+text},+tail}:
      +resume : Step = Imports{path,namespace,rest,aliases,text}
      S.choose(Action,String.eq(target,"Base"),u =>
        S.choose(Action,has_base(state),u => Advance{Con{resume,tail},state},u =>
          Read{base_path(),131073,False{},PinnedBase{},Con{resume,tail},state}),u =>
        step_target(I.resolve(path,namespace,bundle,target),alias,path,namespace,rest,aliases,text,tail,state))

def delivered(origin: Origin, result: Input) -> Step:
  match origin:
    case UserSource{path,namespace}: Source{path,namespace,result}
    case PinnedBase{}: BaseSource{result}

def run(fuel: Nat, action: Action, +bundle: String, +characters: Nat, +depth: Nat,
  next: Result<S.Error,Receipt> -> IO(Unit)) -> IO(Unit):
  match fuel action:
    case _ Stopped{error}: next(Fail{error})
    case _ Finished{receipt}: next(Done{receipt})
    case 0n _: next(Fail{S.Exhausted{"load",S.At{0,0,0,0}}})
    case 1n+ +n Advance{tasks,state}:
      run(n,plan(tasks,state,bundle,characters,depth),bundle,characters,depth,next)
    case 1n+ +n Read{path,cap,missing,+origin,+tasks,+state}:
      read_source(path,cap,missing,origin,result =>
        run(n,plan(Con{delivered(origin,received(result)),tasks},state,bundle,characters,depth),bundle,characters,depth,next))

# The seed's bundle prefix is realpath(root) + "/"; for "/" that is "//", which
# contains nothing, so the root directory has no equivalent containment here.
def start(+path: String, +bundle: String) -> Action:
  S.choose(Action,Bool.xor(String.starts_with(path,"/"),String.starts_with(bundle,"/")),u =>
    Stopped{S.Unsupported{"load","mixed-path-roots",S.At{0,0,0,0}}},u =>
  S.choose(Action,Bool.or(I.climbs(I.normalize(path)),I.climbs(I.normalize(bundle))),u =>
    Stopped{S.Unsupported{"load","path-identity",S.At{0,0,0,0}}},u =>
  S.choose(Action,String.eq(I.normalize(bundle),"/"),u =>
    Stopped{S.Unsupported{"load","root-bundle",S.At{0,0,0,0}}},u =>
    Advance{[Visit{I.normalize(path),"",True{}}],State{Nil{},Nil{},Nil{},Q.Symbols{Nil{},Nil{}},Nil{},False{}}})))

def begin(result: Result<S.Error,Unit>, +path: String, +bundle: String, characters: Nat, depth: Nat,
  next: Result<S.Error,Receipt> -> IO(Unit)) -> IO(Unit):
  match result:
    case Fail{error}: next(Fail{error})
    case Done{unit}: run(1024n,start(path,bundle),I.normalize(bundle),characters,depth,next)

def entry_path(result: Result<S.Error,Unit>, +path: String, +bundle: String, +characters: Nat, +depth: Nat,
  next: Result<S.Error,Receipt> -> IO(Unit)) -> IO(Unit):
  match result:
    case Fail{error}: next(Fail{error})
    case Done{unit}: F.check(path,checked => begin(checked,path,bundle,characters,depth,next))

def load_roots(mixed: Bool, +path: String, +bundle: String, +characters: Nat, +depth: Nat,
  next: Result<S.Error,Receipt> -> IO(Unit)) -> IO(Unit):
  match mixed:
    case True{}: run(1024n,start(path,bundle),bundle,characters,depth,next)
    case False{}: F.check(bundle,result => entry_path(result,path,bundle,characters,depth,next))

def load(+path: String, +bundle: String, characters: Nat, depth: Nat,
  next: Result<S.Error,Receipt> -> IO(Unit)) -> IO(Unit):
  load_roots(Bool.xor(String.starts_with(path,"/"),String.starts_with(bundle,"/")),path,bundle,characters,depth,next)

def named(+path: String, files: List<&2,String>) -> Bool:
  match files:
    case Nil{}: False{}
    case Con{file,rest}: Bool.or(I.same_file(path,file),named(path,rest))

# An output may not name a file the load read: the entry, a module or the pinned
# Base. Only canonical spellings are compared, so a climbing output is refused.
def written(+output: String, receipt: Receipt) -> Result<S.Error,Unit>:
  match receipt:
    case Receipt{root,files,checked,unchecked}:
      +path = I.normalize(output)
      S.choose(Result<S.Error,Unit>,I.climbs(path),u => Fail{S.Host{"arguments","output-path"}},u =>
      S.choose(Result<S.Error,Unit>,named(path,Con{base_path(),files}),u =>
        Fail{S.Host{"arguments","source-is-output"}},u => Done{Unit{}}))

# The path query rejects symlink components and inexact case in the output too.
def canonical_output(result: Result<S.Error,Unit>) -> Result<S.Error,Unit>:
  match result:
    case Fail{S.Host{phase,code}}: Fail{S.Host{phase,code}}
    case Fail{error}: Fail{S.Host{"arguments","output-path"}}
    case Done{unit}: Done{unit}

def guarded(+output: String, result: Result<S.Error,Receipt>,
  next: Result<S.Error,Receipt> -> IO(Unit)) -> IO(Unit):
  match result:
    case Fail{error}: next(Fail{error})
    case Done{+receipt}:
      F.check(output,query => next(S.bind(Unit,Receipt,canonical_output(query),u =>
        S.bind(Unit,Receipt,written(output,receipt),v => Done{receipt}))))

def tree(receipt: Receipt) -> S.Node:
  match receipt:
    case Receipt{root,files,checked,unchecked}: root

def lines(+prefix: String, names: List<&2,String>) -> String:
  match names:
    case Nil{}: ""
    case Con{name,rest}: String.concat([prefix,name,"\n",lines(prefix,rest)])

def describe(receipt: Receipt) -> String:
  match receipt:
    case Receipt{root,files,checked,unchecked}:
      String.concat(["BasePin\t",base_hash(),"\n",lines("Module\t",files),
        lines("BaseChecked\t",checked),lines("BaseUnchecked\t",unchecked)])

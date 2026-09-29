import Base
import ./syntax.bend as S
import ./image-plan.bend as P

# knot-image-1, decoding: the words of an image back to its Plan. The inverse of image-layout.bend.

# A refused image is `HostFailure image` with the reason of vm/serializer.py where it has one; an
# image past a resource limit of SPEC section 4 is exhausted, never malformed.
def malformed(-A: Type, reason: String) -> Result<S.Error,A>:
  Fail{S.Host{"image",reason}}

# A record of a section: its payload (the words after its length word) and its offset.
type Located is Data:
  Located{at: U32, words: List<&2,U32>}

type Read is Data:
  Read{items: List<&2,Located>, rest: List<&2,U32>, at: U32}

# One word per step: `Counting` expects a section's count, `Length` the length word of the next
# record and `Payload` the words left in the current one.
type Reader is Data:
  Counting{at: U32}
  Length{count: U32, at: U32, items: List<&2,Located>}
  Payload{count: U32, left: U32, start: U32, at: U32, payload: List<&2,U32>, items: List<&2,Located>}

def finished(items: List<&2,Located>, rest: List<&2,U32>, at: U32) -> Result<S.Error,Read>:
  Done{Read{List.reverse(&2,Located,items),rest,at}}

# The record limit is checked when the count is read (SPEC section 4), before anything it governs.
def read_section(words: List<&2,U32>, reader: Reader) -> Result<S.Error,Read>:
  match words reader:
    case Nil{} _: malformed(Read,"truncated")
    case Con{+count,+tail} Counting{+at}:
      S.choose(Result<S.Error,Read>,U32.is_gt(count,P.table_records()),u => P.exhausted(Read),u =>
        S.choose(Result<S.Error,Read>,U32.is_eq(count,0),u => finished(Nil{},tail,U32.add(at,1)),u => read_section(tail,Length{count,U32.add(at,1),Nil{}})))
    case Con{+length,tail} Length{+count,+at,items}:
      S.choose(Result<S.Error,Read>,U32.is_lt(length,2),u => malformed(Read,"record length"),u =>
        read_section(tail,Payload{count,U32.sub(length,1),at,U32.add(at,1),Nil{},items}))
    case Con{+word,+tail} Payload{+count,+left,+start,+at,+payload,+items}:
      S.choose(Result<S.Error,Read>,U32.is_gt(left,1),u => read_section(tail,Payload{count,U32.sub(left,1),start,U32.add(at,1),Con{word,payload},items}),u =>
        S.choose(Result<S.Error,Read>,U32.is_eq(count,1),u => finished(Con{Located{start,List.reverse(&2,U32,Con{word,payload})},items},tail,U32.add(at,1)),u =>
          read_section(tail,Length{U32.sub(count,1),U32.add(at,1),Con{Located{start,List.reverse(&2,U32,Con{word,payload})},items}})))

def section_read(words: List<&2,U32>, +at: U32) -> Result<S.Error,Read>:
  read_section(words,Counting{at})

type Split is Data:
  Split{head: List<&2,U32>, rest: List<&2,U32>}

def split_words(count: Nat, words: List<&2,U32>, acc: List<&2,U32>) -> Result<S.Error,Split>:
  match count words:
    case 0n words: Done{Split{List.reverse(&2,U32,acc),words}}
    case 1n+ +n Con{head,tail}: split_words(n,tail,Con{head,acc})
    case 1n+ +n Nil{}: malformed(Split,"length")

type Header is Data:
  Header{total: U32, entry: U32, main: U32, offsets: List<&2,U32>, representation: List<&2,U32>}

def parsed_header(head: List<&2,U32>) -> Result<S.Error,Header>:
  match head:
    case Con{+magic_word,Con{+version,Con{+total,Con{+entry,Con{+main,Con{+o1,Con{+o2,Con{+o3,Con{+o4,Con{+o5,Con{+o6,Con{+reserved,Con{+r0,Con{+r1,Con{+r2,Con{+r3,Con{+r4,Con{+r5,Con{+r6,Con{+r7,Con{+r8,Con{+r9,Con{+r10,Con{+r11,Con{+d0,Con{+d1,Con{+d2,Con{+d3,Con{+d4,Con{+d5,Con{+d6,Con{+d7,Nil{}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}:
      S.choose(Result<S.Error,Header>,Bool.and(U32.is_eq(magic_word,P.magic()),U32.is_eq(version,1)),u =>
        S.choose(Result<S.Error,Header>,Bool.and(U32.is_lt(entry,2),U32.is_eq(reserved,0)),u =>
          S.choose(Result<S.Error,Header>,P.same_words([d0,d1,d2,d3,d4,d5,d6,d7],P.digest()),u =>
            Done{Header{total,entry,main,[o1,o2,o3,o4,o5,o6],[r0,r1,r2,r3,r4,r5,r6,r7,r8,r9,r10,r11]}},u => malformed(Header,"registry digest")),u => malformed(Header,"header")),u => malformed(Header,"magic"))
    case _: malformed(Header,"length")

type Gathered is Data:
  Gathered{sections: List<&2,List<&2,Located>>, rest: List<&2,U32>, at: U32}

type Stage is Data:
  Fresh{words: List<&2,U32>, at: U32, done: List<&2,List<&2,Located>>}
  Fetched{read: Read, later: List<&2,U32>, done: List<&2,List<&2,Located>>}

# The six sections follow the header in order, adjacent, from the offsets the header names.
def read_sections(fuel: Nat, offsets: List<&2,U32>, stage: Stage) -> Result<S.Error,Gathered>:
  match fuel offsets stage:
    case 0n _ _: malformed(Gathered,"sections")
    case 1n+ +n Nil{} Fresh{words,at,done}: Done{Gathered{List.reverse(&2,List<&2,Located>,done),words,at}}
    case 1n+ +n Con{+offset,+later} Fresh{+words,+at,done}:
      S.choose(Result<S.Error,Gathered>,U32.is_eq(at,offset),u =>
        S.bind(Read,Gathered,section_read(words,at),read => read_sections(n,Nil{},Fetched{read,later,done})),u => malformed(Gathered,"section offset"))
    case 1n+ +n offsets Fetched{Read{items,rest,at},later,done}: read_sections(n,later,Fresh{rest,at,Con{items,done}})

# Names hold identifiers: bytes 1..127. A wider name is refused as unsupported, never misread.
def ascii_text(bytes: List<&2,U32>, acc: String) -> Result<S.Error,String>:
  match bytes:
    case Nil{}: Done{String.reverse(acc)}
    case Con{+byte,+tail}:
      S.choose(Result<S.Error,String>,U32.is_eq(byte,0),u => malformed(String,"name padding"),u =>
        S.choose(Result<S.Error,String>,U32.is_lt(byte,128),u => ascii_text(tail,SCon{Char.from_u32(byte),acc}),u => P.unsupported(String,"image-name")))

def unpacked(words: List<&2,U32>) -> List<&2,U32>:
  match words:
    case Nil{}: Nil{}
    case Con{+word,tail}:
      Con{U32.and(word,255),Con{U32.and(U32.shrn(word,8n),255),Con{U32.and(U32.shrn(word,16n),255),Con{U32.shrn(word,24n),unpacked(tail)}}}}

def zeros(bytes: List<&2,U32>) -> Bool:
  match bytes:
    case Nil{}: True{}
    case Con{byte,tail}: Bool.and(U32.is_eq(byte,0),zeros(tail))

def named(split: Split) -> Result<S.Error,String>:
  match split:
    case Split{used,rest}:
      S.choose(Result<S.Error,String>,zeros(rest),u => ascii_text(used,SNil{}),u => malformed(String,"name padding"))

def name_text(located: Located) -> Result<S.Error,String>:
  match located:
    case Located{at,Con{+size,+packed}}:
      S.choose(Result<S.Error,String>,Bool.and(U32.is_gt(size,0),U32.is_eq(P.count(packed),U32.shrn(U32.add(size,3),2n))),u =>
        S.bind(Split,String,split_words(U32.to_nat(size),unpacked(packed),Nil{}),split => named(split)),u => malformed(String,"name length"))
    case _: malformed(String,"name length")

def has_name(seen: List<&2,String>, +text: String) -> Bool:
  match seen:
    case Nil{}: False{}
    case Con{head,tail}: Bool.or(String.eq(head,text),has_name(tail,text))

# Names come oldest first; `seen` holds them newest first while they are read.
def decoded_names(records: List<&2,Located>, +seen: List<&2,String>) -> Result<S.Error,List<&2,String>>:
  match records:
    case Nil{}: Done{List.reverse(&2,String,seen)}
    case Con{head,tail}:
      S.bind(String,List<&2,String>,name_text(head),+text =>
        S.choose(Result<S.Error,List<&2,String>>,has_name(seen,text),u => malformed(List<&2,String>,"duplicate name"),u => decoded_names(tail,Con{text,seen})))

def name_at(names: List<&2,String>, +index: U32) -> Result<S.Error,String>:
  match names:
    case Nil{}: malformed(String,"name index")
    case Con{+head,+tail}: S.choose(Result<S.Error,String>,U32.is_eq(index,0),u => Done{head},u => name_at(tail,U32.sub(index,1)))

# [kind, n, data...]: a scalar holds one word, a String its Chr codes.
def decode_constant(located: Located) -> Result<S.Error,P.Constant>:
  match located:
    case Located{at,Con{+kind,Con{+n,+data}}}:
      S.choose(Result<S.Error,P.Constant>,Bool.and(U32.is_lt(kind,4),U32.is_eq(P.count(data),n)),u =>
        S.choose(Result<S.Error,P.Constant>,Bool.or(U32.is_eq(kind,3),U32.is_eq(n,1)),u => Done{P.Constant{kind,data}},u => malformed(P.Constant,"scalar constant width")),u => malformed(P.Constant,"constant record"))
    case _: malformed(P.Constant,"constant record")

def decoded_constants(records: List<&2,Located>) -> Result<S.Error,List<&2,P.Constant>>:
  match records:
    case Nil{}: Done{Nil{}}
    case Con{head,tail}:
      S.bind(P.Constant,List<&2,P.Constant>,decode_constant(head),constant =>
        S.bind(List<&2,P.Constant>,List<&2,P.Constant>,decoded_constants(tail),rest => Done{Con{constant,rest}}))

def constant_of(constants: List<&2,P.Constant>, +index: U32) -> Result<S.Error,P.Constant>:
  match constants:
    case Nil{}: malformed(P.Constant,"constant index")
    case Con{+head,+tail}: S.choose(Result<S.Error,P.Constant>,U32.is_eq(index,0),u => Done{head},u => constant_of(tail,U32.sub(index,1)))

type Grouped is Data:
  Grouped{constructors: List<&2,P.Constructor>, rest: List<&2,Located>}

def decode_constructors(left: Nat, records: List<&2,Located>, +type_index: U32, +tag: U32, +names: List<&2,String>, acc: List<&2,P.Constructor>) -> Result<S.Error,Grouped>:
  match left records:
    case 0n records: Done{Grouped{List.reverse(&2,P.Constructor,acc),records}}
    case 1n+ +n Con{Located{at,Con{+owner,Con{+index,Con{+name,Con{+arity,+fields}}}}},+rest}:
      S.choose(Result<S.Error,Grouped>,Bool.and(U32.is_eq(owner,type_index),Bool.and(U32.is_eq(index,tag),U32.is_eq(P.count(fields),arity))),u =>
        S.bind(String,Grouped,name_at(names,name),text => decode_constructors(n,rest,type_index,U32.add(tag,1),names,Con{P.Constructor{text,fields},acc})),u => malformed(Grouped,"constructor record"))
    case 1n+ +n Con{other,rest}: malformed(Grouped,"constructor record")
    case 1n+ +n Nil{}: malformed(Grouped,"constructor count")

type Shaped is Data:
  Shaped{shapes: List<&2,P.Shape>, constructors: List<&2,Located>}

type Shaping is Data:
  Next{types: List<&2,Located>, constructors: List<&2,Located>, first: U32, index: U32, acc: List<&2,P.Shape>}
  Taken{grouped: Grouped, text: String, types: List<&2,Located>, first: U32, index: U32, acc: List<&2,P.Shape>}

def arrow_kind(+kind: U32, +domain: U32, +result: U32) -> P.Shape:
  Bool.pick(P.Shape,U32.is_eq(kind,1),P.Arrow{domain,result},P.Erased{domain,result})

# Types are read in table order; a constructor row belongs to the type that owns it, densely tagged.
def decode_shapes(fuel: Nat, +names: List<&2,String>, mode: Shaping) -> Result<S.Error,Shaped>:
  match fuel mode:
    case 0n _: malformed(Shaped,"types")
    case 1n+ +n Next{Nil{},constructors,first,index,acc}: Done{Shaped{List.reverse(&2,P.Shape,acc),constructors}}
    case 1n+ +n Next{Con{Located{at,Con{+kind,Con{+name,Con{+a,Con{+b,Nil{}}}}}},+tail},+constructors,+first,+index,+acc}:
      S.choose(Result<S.Error,Shaped>,U32.is_eq(kind,0),u =>
        S.choose(Result<S.Error,Shaped>,U32.is_eq(a,first),u =>
          S.bind(String,Shaped,name_at(names,name),+text =>
            S.bind(Grouped,Shaped,decode_constructors(U32.to_nat(b),constructors,index,0,names,Nil{}),grouped =>
              decode_shapes(n,names,Taken{grouped,text,tail,U32.add(first,b),index,acc}))),u => malformed(Shaped,"constructor grouping")),u =>
        S.choose(Result<S.Error,Shaped>,Bool.or(U32.is_eq(kind,1),U32.is_eq(kind,2)),u =>
          S.choose(Result<S.Error,Shaped>,U32.is_eq(name,P.none()),u =>
            decode_shapes(n,names,Next{tail,constructors,first,U32.add(index,1),Con{arrow_kind(kind,a,b),acc}}),u => malformed(Shaped,"arrow name")),u =>
          S.choose(Result<S.Error,Shaped>,Bool.and(U32.is_eq(kind,3),Bool.and(U32.is_eq(a,0),U32.is_eq(b,0))),u =>
            S.bind(String,Shaped,name_at(names,name),text => decode_shapes(n,names,Next{tail,constructors,first,U32.add(index,1),Con{P.Opaque{text},acc}})),u => malformed(Shaped,"type record"))))
    case 1n+ +n Next{other,constructors,first,index,acc}: malformed(Shaped,"type record")
    case 1n+ +n Taken{Grouped{constructors,rest},text,tail,first,index,acc}:
      decode_shapes(n,names,Next{tail,rest,first,U32.add(index,1),Con{P.Algebraic{text,constructors},acc}})

type Head is Data:
  Head{name: String, result: U32, slots: U32, root: U32, parameters: List<&2,U32>}

def decode_head(located: Located, names: List<&2,String>) -> Result<S.Error,Head>:
  match located:
    case Located{at,Con{+name,Con{+result,Con{+arity,Con{+slots,Con{+root,+parameters}}}}}}:
      S.choose(Result<S.Error,Head>,U32.is_eq(P.count(parameters),arity),u =>
        S.choose(Result<S.Error,Head>,U32.is_gt(arity,4096),u => P.exhausted(Head),u =>
          S.choose(Result<S.Error,Head>,U32.is_gt(slots,65536),u => P.exhausted(Head),u =>
            S.bind(String,Head,name_at(names,name),text => Done{Head{text,result,slots,root,parameters}}))),u => malformed(Head,"function record"))
    case _: malformed(Head,"function record")

def decode_heads(records: List<&2,Located>, +names: List<&2,String>) -> Result<S.Error,List<&2,Head>>:
  match records:
    case Nil{}: Done{Nil{}}
    case Con{head,tail}:
      S.bind(Head,List<&2,Head>,decode_head(head,names),first =>
        S.bind(List<&2,Head>,List<&2,Head>,decode_heads(tail,names),rest => Done{Con{first,rest}}))

# ---------------------------------------------------------------- the node stream

# Nodes are read in emission order. A record's children are the newest entries of the stack, in
# order, and the record takes their place: each node has one parent, and the roots that remain are
# the functions' bodies. The offsets a record lists must be the offsets of the entries it takes.
type Item is Data:
  Whole{node: P.Node}
  Branching{row: P.Row}
  Defaulted{node: P.Node}

type Entry is Data:
  Entry{at: U32, item: Item}

type Popped is Data:
  Popped{entries: List<&2,Entry>, rest: List<&2,Entry>}

type Children is Data:
  Children{nodes: List<&2,P.Node>, rest: List<&2,Entry>}

def pop(remaining: Nat, stack: List<&2,Entry>, acc: List<&2,Entry>) -> Result<S.Error,Popped>:
  match remaining stack:
    case 0n stack: Done{Popped{acc,stack}}
    case 1n+ +n Con{entry,rest}: pop(n,rest,Con{entry,acc})
    case 1n+ +n Nil{}: malformed(Popped,"child offset")

def child_nodes(entries: List<&2,Entry>, offsets: List<&2,U32>) -> Result<S.Error,List<&2,P.Node>>:
  match entries offsets:
    case Nil{} Nil{}: Done{Nil{}}
    case Con{Entry{+at,Whole{node}},more} Con{+offset,later}:
      S.choose(Result<S.Error,List<&2,P.Node>>,U32.is_eq(at,offset),u =>
        S.bind(List<&2,P.Node>,List<&2,P.Node>,child_nodes(more,later),rest => Done{Con{node,rest}}),u => malformed(List<&2,P.Node>,"child offset"))
    case _ _: malformed(List<&2,P.Node>,"child offset")

def collected(popped: Popped, offsets: List<&2,U32>) -> Result<S.Error,Children>:
  match popped:
    case Popped{entries,rest}: S.bind(List<&2,P.Node>,Children,child_nodes(entries,offsets),nodes => Done{Children{nodes,rest}})

def children(+offsets: List<&2,U32>, stack: List<&2,Entry>) -> Result<S.Error,Children>:
  S.bind(Popped,Children,pop(U32.to_nat(P.count(offsets)),stack,Nil{}),popped => collected(popped,offsets))

def entry_of(node: P.Node, +at: U32, rest: List<&2,Entry>) -> Result<S.Error,List<&2,Entry>>:
  Done{Con{Entry{at,Whole{node}},rest}}

def counted_entry(op: U32, kids: Children, +at: U32, +type_id: U32, +x: U32) -> Result<S.Error,List<&2,Entry>>:
  match op kids:
    case 1 Children{nodes,rest}: entry_of(P.Intrinsic{type_id,x,nodes},at,rest)
    case 4 Children{nodes,rest}: entry_of(P.Construct{type_id,x,nodes},at,rest)
    case 6 Children{nodes,rest}: entry_of(P.Application{type_id,x,nodes},at,rest)
    case 12 Children{nodes,rest}: entry_of(P.Foreign{type_id,x,nodes},at,rest)
    case _ _: malformed(List<&2,Entry>,"opcode")

# [x, n, children...]: Intrinsic, Construct, Application and Foreign.
def counted_operation(op: U32, x: List<&2,U32>, at: U32, type_id: U32, stack: List<&2,Entry>) -> Result<S.Error,List<&2,Entry>>:
  match x:
    case Con{+first,Con{+n,+offsets}}:
      S.choose(Result<S.Error,List<&2,Entry>>,U32.is_eq(P.count(offsets),n),u =>
        S.bind(Children,List<&2,Entry>,children(offsets,stack),kids => counted_entry(op,kids,at,type_id,first)),u => malformed(List<&2,Entry>,"operand count"))
    case _: malformed(List<&2,Entry>,"operand count")

def literal_operation(x: List<&2,U32>, +at: U32, +type_id: U32, stack: List<&2,Entry>, constants: List<&2,P.Constant>) -> Result<S.Error,List<&2,Entry>>:
  match x:
    case Con{index,Nil{}}: S.bind(P.Constant,List<&2,Entry>,constant_of(constants,index),constant => entry_of(P.Literal{type_id,constant},at,stack))
    case _: malformed(List<&2,Entry>,"lit length")

def scalar_operation(op: U32, x: List<&2,U32>, +at: U32, +type_id: U32, stack: List<&2,Entry>) -> Result<S.Error,List<&2,Entry>>:
  match op x:
    case 3 Con{tag,Nil{}}: entry_of(P.Value{type_id,tag},at,stack)
    case 5 Con{slot,Nil{}}: entry_of(P.Reference{type_id,slot},at,stack)
    case _ _: malformed(List<&2,Entry>,"node length")

def let_built(kids: Children, +at: U32, +type_id: U32, +slot: U32) -> Result<S.Error,List<&2,Entry>>:
  match kids:
    case Children{Con{value,Con{body,Nil{}}},rest}: entry_of(P.Let{type_id,slot,value,body},at,rest)
    case _: malformed(List<&2,Entry>,"let length")

def let_operation(x: List<&2,U32>, +at: U32, +type_id: U32, stack: List<&2,Entry>) -> Result<S.Error,List<&2,Entry>>:
  match x:
    case Con{+slot,Con{value,Con{body,Nil{}}}}:
      S.bind(Children,List<&2,Entry>,children([value,body],stack),kids => let_built(kids,at,type_id,slot))
    case _: malformed(List<&2,Entry>,"let length")

def body_entry(kids: Children, +op: U32, +at: U32, +a: U32, +b: U32, +c: U32) -> Result<S.Error,List<&2,Entry>>:
  match kids:
    case Children{Con{+node,Nil{}},+rest}:
      S.choose(Result<S.Error,List<&2,Entry>>,U32.is_eq(op,9),u => Done{Con{Entry{at,Branching{P.Branch{a,b,c,node}}},rest}},u => Done{Con{Entry{at,Defaulted{node}},rest}})
    case _: malformed(List<&2,Entry>,"body length")

def branch_operation(x: List<&2,U32>, at: U32, stack: List<&2,Entry>) -> Result<S.Error,List<&2,Entry>>:
  match x:
    case Con{+key,Con{+first,Con{+fields,Con{body,Nil{}}}}}: S.bind(Children,List<&2,Entry>,children([body],stack),kids => body_entry(kids,9,at,key,first,fields))
    case _: malformed(List<&2,Entry>,"branch length")

def default_operation(x: List<&2,U32>, at: U32, stack: List<&2,Entry>) -> Result<S.Error,List<&2,Entry>>:
  match x:
    case Con{body,Nil{}}: S.bind(Children,List<&2,Entry>,children([body],stack),kids => body_entry(kids,2,at,0,0,0))
    case _: malformed(List<&2,Entry>,"default length")

def closure_built(captures: List<&2,U32>, kids: Children, +at: U32, +type_id: U32, +live: U32, +slots: U32) -> Result<S.Error,List<&2,Entry>>:
  match kids:
    case Children{Con{node,Nil{}},rest}: entry_of(P.Closure{type_id,live,slots,captures,node},at,rest)
    case _: malformed(List<&2,Entry>,"closure length")

def closure_kids(split: Split, stack: List<&2,Entry>, +at: U32, +type_id: U32, +live: U32, +slots: U32) -> Result<S.Error,List<&2,Entry>>:
  match split:
    case Split{+captures,Con{body,Nil{}}}:
      S.bind(Children,List<&2,Entry>,children([body],stack),kids => closure_built(captures,kids,at,type_id,live,slots))
    case _: malformed(List<&2,Entry>,"closure length")

def closure_operation(x: List<&2,U32>, +at: U32, +type_id: U32, stack: List<&2,Entry>) -> Result<S.Error,List<&2,Entry>>:
  match x:
    case Con{site,Con{+live,Con{+slots,Con{+n,+rest}}}}:
      S.bind(Split,List<&2,Entry>,split_words(U32.to_nat(n),rest,Nil{}),+split => closure_kids(split,stack,at,type_id,live,slots))
    case _: malformed(List<&2,Entry>,"closure length")

def invoke_built(kids: Children, +at: U32, +type_id: U32) -> Result<S.Error,List<&2,Entry>>:
  match kids:
    case Children{Con{callee,arguments},rest}: entry_of(P.Invoke{type_id,callee,arguments},at,rest)
    case _: malformed(List<&2,Entry>,"invoke length")

def invoke_operation(x: List<&2,U32>, +at: U32, +type_id: U32, stack: List<&2,Entry>) -> Result<S.Error,List<&2,Entry>>:
  match x:
    case Con{+function,Con{+n,+arguments}}:
      S.choose(Result<S.Error,List<&2,Entry>>,U32.is_eq(P.count(arguments),n),u =>
        S.bind(Children,List<&2,Entry>,children(Con{function,arguments},stack),kids => invoke_built(kids,at,type_id)),u => malformed(List<&2,Entry>,"invoke length"))
    case _: malformed(List<&2,Entry>,"invoke length")

type Rowing is Data:
  Rowing{rows: List<&2,P.Row>, rest: List<&2,Entry>}

def row_prepended(row: P.Row, rowing: Rowing) -> Result<S.Error,Rowing>:
  match rowing:
    case Rowing{rows,rest}: Done{Rowing{Con{row,rows},rest}}

# The rows of a Case, from its row words and the arms that its record takes: a tag row is an arm's
# offset or `none`, a key row is a key and an arm whose own key it repeats.
def rows_from(mode: U32, words: List<&2,U32>, entries: List<&2,Entry>) -> Result<S.Error,Rowing>:
  match mode words entries:
    case 0 Nil{} entries: Done{Rowing{Nil{},entries}}
    case 0 Con{4294967295,more} entries: S.bind(Rowing,Rowing,rows_from(0,more,entries),rest => row_prepended(P.Missing{},rest))
    case 0 Con{+w,more} Con{Entry{+at,Branching{row}},later}:
      S.choose(Result<S.Error,Rowing>,U32.is_eq(at,w),u => S.bind(Rowing,Rowing,rows_from(0,more,later),rest => row_prepended(row,rest)),u => malformed(Rowing,"case arm"))
    case 1 Nil{} entries: Done{Rowing{Nil{},entries}}
    case 1 Con{+key,Con{+w,more}} Con{Entry{+at,Branching{P.Branch{+k,first,fields,body}}},later}:
      S.choose(Result<S.Error,Rowing>,Bool.and(U32.is_eq(at,w),U32.is_eq(k,key)),u =>
        S.bind(Rowing,Rowing,rows_from(1,more,later),rest => row_prepended(P.Branch{k,first,fields,body},rest)),u => malformed(Rowing,"case key"))
    case _ _ _: malformed(Rowing,"case arm")

def arm_offsets(mode: U32, words: List<&2,U32>) -> List<&2,U32>:
  match mode words:
    case 0 Nil{}: Nil{}
    case 0 Con{4294967295,more}: arm_offsets(0,more)
    case 0 Con{w,more}: Con{w,arm_offsets(0,more)}
    case 1 Con{key,Con{w,more}}: Con{w,arm_offsets(1,more)}
    case _ _: Nil{}

def case_done(rowing: Rowing, +default: U32, below: List<&2,Entry>, +at: U32, +type_id: U32, +slot: U32, +scrutinee: U32, +mode: U32) -> Result<S.Error,List<&2,Entry>>:
  match rowing:
    case Rowing{rows,Nil{}}:
      S.choose(Result<S.Error,List<&2,Entry>>,U32.is_eq(default,P.none()),u => entry_of(P.Case{type_id,slot,scrutinee,mode,rows,None{}},at,below),u => malformed(List<&2,Entry>,"case default"))
    case Rowing{rows,Con{Entry{+d,Defaulted{node}},Nil{}}}:
      S.choose(Result<S.Error,List<&2,Entry>>,U32.is_eq(default,d),u => entry_of(P.Case{type_id,slot,scrutinee,mode,rows,Some{node}},at,below),u => malformed(List<&2,Entry>,"case default"))
    case _: malformed(List<&2,Entry>,"case arm kind")

def case_after(popped: Popped, words: List<&2,U32>, +default: U32, +at: U32, +type_id: U32, +slot: U32, +scrutinee: U32, +mode: U32) -> Result<S.Error,List<&2,Entry>>:
  match popped:
    case Popped{entries,below}:
      S.bind(Rowing,List<&2,Entry>,rows_from(mode,words,entries),rowing => case_done(rowing,default,below,at,type_id,slot,scrutinee,mode))

def case_split(split: Split, stack: List<&2,Entry>, +at: U32, +type_id: U32, +slot: U32, +scrutinee: U32, +mode: U32) -> Result<S.Error,List<&2,Entry>>:
  match split:
    case Split{+words,Con{+default,Nil{}}}:
      S.bind(Popped,List<&2,Entry>,pop(U32.to_nat(U32.add(P.count(arm_offsets(mode,words)),Bool.pick(U32,U32.is_eq(default,P.none()),0,1))),stack,Nil{}),popped =>
        case_after(popped,words,default,at,type_id,slot,scrutinee,mode))
    case _: malformed(List<&2,Entry>,"case length")

def case_operation(x: List<&2,U32>, +at: U32, +type_id: U32, stack: List<&2,Entry>) -> Result<S.Error,List<&2,Entry>>:
  match x:
    case Con{+slot,Con{+scrutinee,Con{+mode,Con{+n,+tail}}}}:
      S.choose(Result<S.Error,List<&2,Entry>>,Bool.and(U32.is_lt(mode,2),U32.is_le(n,P.count(tail))),u =>
        S.bind(Split,List<&2,Entry>,split_words(U32.to_nat(Bool.pick(U32,U32.is_eq(mode,0),n,U32.mul(n,2))),tail,Nil{}),split => case_split(split,stack,at,type_id,slot,scrutinee,mode)),u => malformed(List<&2,Entry>,"case length"))
    case _: malformed(List<&2,Entry>,"case length")

def operation(op: U32, x: List<&2,U32>, at: U32, type_id: U32, stack: List<&2,Entry>, constants: List<&2,P.Constant>) -> Result<S.Error,List<&2,Entry>>:
  match op:
    case 0: literal_operation(x,at,type_id,stack,constants)
    case 1: counted_operation(1,x,at,type_id,stack)
    case 2: default_operation(x,at,stack)
    case 3: scalar_operation(3,x,at,type_id,stack)
    case 4: counted_operation(4,x,at,type_id,stack)
    case 5: scalar_operation(5,x,at,type_id,stack)
    case 6: counted_operation(6,x,at,type_id,stack)
    case 7: let_operation(x,at,type_id,stack)
    case 8: case_operation(x,at,type_id,stack)
    case 9: branch_operation(x,at,stack)
    case 10: closure_operation(x,at,type_id,stack)
    case 11: invoke_operation(x,at,type_id,stack)
    case 12: counted_operation(12,x,at,type_id,stack)
    case _: malformed(List<&2,Entry>,"opcode")

def nodes_from(records: List<&2,Located>, stack: List<&2,Entry>, +constants: List<&2,P.Constant>) -> Result<S.Error,List<&2,Entry>>:
  match records:
    case Nil{}: Done{stack}
    case Con{Located{at,Con{op,Con{type_id,x}}},tail}:
      S.bind(List<&2,Entry>,List<&2,Entry>,operation(op,x,at,type_id,stack,constants),next => nodes_from(tail,next,constants))
    case Con{other,tail}: malformed(List<&2,Entry>,"node record")

def functions_from(heads: List<&2,Head>, entries: List<&2,Entry>) -> Result<S.Error,List<&2,P.Function>>:
  match heads entries:
    case Nil{} Nil{}: Done{Nil{}}
    case Con{Head{name,result,slots,root,parameters},more} Con{Entry{+at,Whole{body}},later}:
      S.choose(Result<S.Error,List<&2,P.Function>>,U32.is_eq(at,root),u =>
        S.bind(List<&2,P.Function>,List<&2,P.Function>,functions_from(more,later),rest => Done{Con{P.Function{name,parameters,result,slots,body},rest}}),u => malformed(List<&2,P.Function>,"function root"))
    case _ _: malformed(List<&2,P.Function>,"unreachable node")

def planned(+functions: List<&2,P.Function>, shapes: List<&2,P.Shape>, +entry: U32, +main: U32, representation: List<&2,U32>) -> Result<S.Error,P.Plan>:
  S.choose(Result<S.Error,P.Plan>,U32.is_eq(main,P.main_index(functions,0)),u => Done{P.Plan{entry,representation,shapes,functions}},u => malformed(P.Plan,"main index"))

def assembled(entries: List<&2,Entry>, heads: List<&2,Head>, shaped: Shaped, +entry: U32, +main: U32, representation: List<&2,U32>) -> Result<S.Error,P.Plan>:
  match shaped:
    case Shaped{shapes,Nil{}}:
      S.bind(List<&2,P.Function>,P.Plan,functions_from(heads,entries),functions => planned(functions,shapes,entry,main,representation))
    case _: malformed(P.Plan,"constructor count")

def decode_nodes(stack: List<&2,Entry>, heads: List<&2,Head>, shaped: Shaped, +entry: U32, +main: U32, representation: List<&2,U32>) -> Result<S.Error,P.Plan>:
  assembled(List.reverse(&2,Entry,stack),heads,shaped,entry,main,representation)

def decode_stage(shaped: Shaped, heads: List<&2,Head>, nodes: List<&2,Located>, constants: List<&2,P.Constant>, +entry: U32, +main: U32, representation: List<&2,U32>) -> Result<S.Error,P.Plan>:
  S.bind(List<&2,Entry>,P.Plan,nodes_from(nodes,Nil{},constants),stack => decode_nodes(stack,heads,shaped,entry,main,representation))

def decode_constants_stage(constants: List<&2,P.Constant>, shaped: Shaped, heads: List<&2,Head>, nodes: List<&2,Located>, +entry: U32, +main: U32, representation: List<&2,U32>) -> Result<S.Error,P.Plan>:
  decode_stage(shaped,heads,nodes,constants,entry,main,representation)

def located_count(records: List<&2,Located>, +size: U32) -> U32:
  match records:
    case Nil{}: size
    case Con{head,tail}: located_count(tail,U32.add(size,1))

def decode_shapes_stage(+names: List<&2,String>, +types: List<&2,Located>, constructors: List<&2,Located>, functions: List<&2,Located>, constants: List<&2,Located>, nodes: List<&2,Located>,
    +entry: U32, +main: U32, representation: List<&2,U32>) -> Result<S.Error,P.Plan>:
  S.bind(Shaped,P.Plan,decode_shapes(U32.to_nat(U32.add(U32.mul(3,located_count(types,0)),2)),names,Next{types,constructors,0,0,Nil{}}),shaped =>
    S.bind(List<&2,Head>,P.Plan,decode_heads(functions,names),heads =>
      S.bind(List<&2,P.Constant>,P.Plan,decoded_constants(constants),pool => decode_constants_stage(pool,shaped,heads,nodes,entry,main,representation))))

def decode_sections(gathered: Gathered, +entry: U32, +main: U32, representation: List<&2,U32>) -> Result<S.Error,P.Plan>:
  match gathered:
    case Gathered{Con{types,Con{constructors,Con{functions,Con{constants,Con{nodes,Con{names,Nil{}}}}}}},Nil{},at}:
      S.bind(List<&2,String>,P.Plan,decoded_names(names,Nil{}),listed => decode_shapes_stage(listed,types,constructors,functions,constants,nodes,entry,main,representation))
    case Gathered{sections,Nil{},at}: malformed(P.Plan,"sections")
    case Gathered{sections,rest,at}: malformed(P.Plan,"trailing words")

def decode_body(header: Header, rest: List<&2,U32>, +total_words: U32) -> Result<S.Error,P.Plan>:
  match header:
    case Header{+total,+entry,+main,+offsets,+representation}:
      S.choose(Result<S.Error,P.Plan>,U32.is_eq(total,total_words),u =>
        S.bind(Gathered,P.Plan,read_sections(16n,offsets,Fresh{rest,32,Nil{}}),gathered => decode_sections(gathered,entry,main,representation)),u => malformed(P.Plan,"total"))

def decode_split(split: Split, +total_words: U32) -> Result<S.Error,P.Plan>:
  match split:
    case Split{head,rest}: S.bind(Header,P.Plan,parsed_header(head),header => decode_body(header,rest,total_words))

# The words of an image, back to its plan. The size limit comes first, even for a malformed image.
def decode(+words: List<&2,U32>) -> Result<S.Error,P.Plan>:
  S.choose(Result<S.Error,P.Plan>,U32.is_gt(P.count(words),P.image_words()),u => P.exhausted(P.Plan),u =>
    S.bind(Split,P.Plan,split_words(32n,words,Nil{}),split => decode_split(split,P.count(words))))

# Bytes to words, little-endian: the input of `decode` from a file of `File.read_bytes`.
def words_onto(bytes: List<&2,U32>, acc: List<&2,U32>) -> Result<S.Error,List<&2,U32>>:
  match bytes:
    case Nil{}: Done{List.reverse(&2,U32,acc)}
    case Con{+a,Con{+b,Con{+c,Con{+d,tail}}}}:
      words_onto(tail,Con{U32.or(a,U32.or(U32.shln(b,8n),U32.or(U32.shln(c,16n),U32.shln(d,24n)))),acc})
    case _: malformed(List<&2,U32>,"length")

def words_of(bytes: List<&2,U32>) -> Result<S.Error,List<&2,U32>>:
  words_onto(bytes,Nil{})

# ---------------------------------------------------------------- the round trip

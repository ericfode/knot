import Base
import ./word.bend as W
import ./validate.bend as V

# ---------------------------------------------------------------- words, cells and memory

# Zero marks an empty slot. An immediate is (v << 1) | 1 for v < 2^31; every
# other nonzero word is the 8-byte-aligned address of a cell (SPEC §5).
def immediate(+v: U32) -> U32:
  U32.add(U32.shln(v,1n),1)

def is_pointer(+w: U32) -> Bool:
  Bool.and(Bool.not(U32.is_eq(w,0)),U32.is_eq(U32.and(w,1),0))

def boxed(+v: U32) -> Bool:
  U32.is_ge(v,2147483648)

# In words: the image at byte 4096, the frame region at the next 64 KiB
# boundary, 16 MiB of frames, then the heap up to 4 GiB.
def region_words() -> U32:
  4194304

def memory_words() -> U32:
  1073741824

def heap_base(+total: U32) -> U32:
  U32.add(U32.mul(U32.div(U32.add(U32.add(4096,U32.mul(4,total)),65535),65536),16384),region_words())

# Cell classes: 0 Object, 1 Closure, 2 Big, 3 Action, 4 Activation, 5 Request.
# free[k] heads the LIFO list of free cells of 4 << k words.
type Heap is Data:
  Heap{memory: W.Store, bump: U32, free: List<&2,U32>}

type Cell is Data:
  Cell{heap: Heap, word: U32}

def memory_of(heap: Heap) -> W.Store:
  match heap:
    case Heap{memory,bump,free}: memory

def load_word(+heap: Heap, +address: U32, +i: U32) -> U32:
  W.read(memory_of(heap),U32.add(U32.shrn(address,2n),i))

def stored_word(heap: Heap, +address: U32, +i: U32, word: U32) -> Heap:
  match heap:
    case Heap{memory,bump,free}: Heap{W.write(memory,U32.add(U32.shrn(address,2n),i),word),bump,free}

def writes(words: List<&2,U32>, memory: W.Store, +at: U32) -> W.Store:
  match words:
    case Nil{}: memory
    case Con{w,rest}: writes(rest,W.write(memory,at,w),U32.add(at,1))

def zeros(n: Nat) -> List<&2,U32>:
  match n:
    case 0n: Nil{}
    case 1n+m: Con{0,zeros(m)}

def replaced(xs: List<&2,U32>, +i: U32, +x: U32) -> List<&2,U32>:
  match xs:
    case Nil{}: Nil{}
    case Con{y,+rest}: W.choose(List<&2,U32>,U32.is_eq(i,0),u => Con{x,rest},u => Con{y,replaced(rest,U32.sub(i,1),x)})

# The smallest k with 4 << k words holding `words`.
def size_class(fuel: Nat, +words: U32, +k: U32) -> U32:
  match fuel:
    case 0n: k
    case 1n+f: W.choose(U32,U32.is_ge(U32.shln(4,U32.to_nat(k)),words),u => k,u => size_class(f,words,U32.add(k,1)))

def class_of(+words: U32) -> U32:
  size_class(29n,words,0)

def filled(+memory: W.Store, +at: U32, +rc: U32, +class: U32, +payload: List<&2,U32>, +words: U32) -> W.Store:
  writes(List.append(&2,U32,[rc,U32.add(U32.shln(W.count(U32,payload),3n),class)],List.append(&2,U32,payload,zeros(U32.to_nat(U32.sub(words,U32.add(2,W.count(U32,payload))))))),memory,at)

# Pop the class's free list, else take the bump pointer; write rc, header,
# payload and zeroed padding. A cell past 4 GiB is heap exhaustion.
def allocate(+heap: Heap, +rc: U32, +class: U32, +payload: List<&2,U32>) -> Result<W.Stop,Cell>:
  match heap:
    case Heap{+memory,+bump,+free}:
      +k = class_of(U32.add(2,W.count(U32,payload)))
      +words = U32.shln(4,U32.to_nat(k))
      +head = W.nth(free,k)
      W.choose(Result<W.Stop,Cell>,Bool.not(U32.is_eq(head,0)),
        u => Done{Cell{Heap{filled(memory,U32.shrn(head,2n),rc,class,payload,words),bump,replaced(free,k,W.read(memory,U32.shrn(head,2n)))},head}},
        u => W.choose(Result<W.Stop,Cell>,U32.is_gt(words,U32.sub(memory_words(),bump)),u => Fail{W.Exhausted{2,"heap"}},
          u => Done{Cell{Heap{filled(memory,bump,rc,class,payload,words),U32.add(bump,words),free},U32.shln(bump,2n)}}))

def alloc(+heap: Heap, +class: U32, +payload: List<&2,U32>) -> Result<W.Stop,Cell>:
  allocate(heap,1,class,payload)

def bind(-A: Data, -B: Data, result: Result<W.Stop,A>, next: A -> Result<W.Stop,B>) -> Result<W.Stop,B>:
  match result:
    case Fail{stop}: Fail{stop}
    case Done{value}: next(value)

def with_cell(-B: Data, result: Result<W.Stop,Cell>, next: Heap -> U32 -> Result<W.Stop,B>) -> Result<W.Stop,B>:
  match result:
    case Fail{stop}: Fail{stop}
    case Done{Cell{heap,word}}: next(heap,word)

# ---------------------------------------------------------------- reference counts

def rc_of(+heap: Heap, +w: U32) -> U32:
  load_word(heap,w,0)

def mortal(+heap: Heap, +w: U32) -> Bool:
  Bool.and(is_pointer(w),Bool.not(W.is_none(rc_of(heap,w))))

# dup and drop ignore zero, immediates and immortal cells (SPEC §5).
def dup(+heap: Heap, +w: U32) -> Result<W.Stop,Heap>:
  +rc = rc_of(heap,w)
  W.choose(Result<W.Stop,Heap>,Bool.not(mortal(heap,w)),u => Done{heap},u =>
  W.choose(Result<W.Stop,Heap>,U32.is_eq(rc,0),u => Fail{W.Internal{"dangling pointer"}},u =>
  W.choose(Result<W.Stop,Heap>,U32.is_eq(rc,4294967294),u => Fail{W.Exhausted{2,"RCOverflow"}},u =>
    Done{stored_word(heap,w,0,U32.add(rc,1))})))

def dups(words: List<&2,U32>, +heap: Heap) -> Result<W.Stop,Heap>:
  match words:
    case Nil{}: Done{heap}
    case Con{+w,rest}: bind(Heap,Heap,dup(heap,w),heap => dups(rest,heap))

# Owning edges: Object fields, Closure captures, Action operands and
# Activation slots; a Big has none. Metadata words are never edges.
def edges(+heap: Heap, +q: U32) -> List<&2,U32>:
  +header = load_word(heap,q,1)
  +length = U32.shrn(header,3n)
  +class = U32.and(header,7)
  +skip = Bool.pick(U32,W.or(U32.is_eq(class,1),W.or(U32.is_eq(class,3),U32.is_eq(class,5))),1,Bool.pick(U32,U32.is_eq(class,2),length,2))
  W.slice(U32.to_nat(U32.sub(length,Bool.pick(U32,U32.is_gt(skip,length),length,skip))),memory_of(heap),U32.add(U32.shrn(q,2n),U32.add(2,skip)))

def freed(+heap: Heap, +q: U32) -> Heap:
  match heap:
    case Heap{+memory,bump,+free}:
      +k = class_of(U32.add(2,U32.shrn(W.read(memory,U32.add(U32.shrn(q,2n),1)),3n)))
      Heap{W.write(W.write(memory,U32.shrn(q,2n),W.nth(free,k)),U32.add(U32.shrn(q,2n),1),U32.shln(4,U32.to_nat(k))),bump,replaced(free,k,q)}

type Pending is Data:
  Pending{heap: Heap, work: List<&2,U32>, size: U32}

def with_pending(-B: Data, result: Result<W.Stop,Pending>, next: Heap -> List<&2,U32> -> U32 -> Result<W.Stop,B>) -> Result<W.Stop,B>:
  match result:
    case Fail{stop}: Fail{stop}
    case Done{Pending{heap,work,size}}: next(heap,work,size)

# Decrement each edge, last to first; a count reaching zero joins the worklist,
# which lives in the frame region's free words.
def decremented(edges: List<&2,U32>, +heap: Heap, +work: List<&2,U32>, +size: U32, +room: U32) -> Result<W.Stop,Pending>:
  match edges:
    case Nil{}: Done{Pending{heap,work,size}}
    case Con{+e,+rest}:
      +rc = rc_of(heap,e)
      W.choose(Result<W.Stop,Pending>,Bool.not(mortal(heap,e)),u => decremented(rest,heap,work,size,room),u =>
      W.choose(Result<W.Stop,Pending>,U32.is_eq(rc,0),u => Fail{W.Internal{"rc underflow"}},u =>
      W.choose(Result<W.Stop,Pending>,U32.is_eq(rc,1),
        u => W.choose(Result<W.Stop,Pending>,U32.is_ge(size,room),u => Fail{W.Exhausted{3,"frames"}},
               u => decremented(rest,stored_word(heap,e,0,0),Con{e,work},U32.add(size,1),room)),
        u => decremented(rest,stored_word(heap,e,0,U32.sub(rc,1)),work,size,room))))

def release(fuel: Nat, +heap: Heap, work: List<&2,U32>, +size: U32, +room: U32) -> Result<W.Stop,Heap>:
  match fuel work:
    case _ Nil{}: Done{heap}
    case 0n _: Fail{W.Internal{"release fuel"}}
    case 1n+ +f Con{+q,rest}:
      with_pending(Heap,decremented(List.reverse(&2,U32,edges(heap,q)),heap,rest,U32.sub(size,1),room),heap => work => size =>
        release(f,freed(heap,q),work,size,room))

def drop(+heap: Heap, +room: U32, +w: U32) -> Result<W.Stop,Heap>:
  +rc = rc_of(heap,w)
  W.choose(Result<W.Stop,Heap>,Bool.not(mortal(heap,w)),u => Done{heap},u =>
  W.choose(Result<W.Stop,Heap>,U32.is_eq(rc,0),u => Fail{W.Internal{"rc underflow"}},u =>
  W.choose(Result<W.Stop,Heap>,U32.is_eq(rc,1),
    u => W.choose(Result<W.Stop,Heap>,U32.is_eq(room,0),u => Fail{W.Exhausted{3,"frames"}},
           u => release(U32.to_nat(memory_words()),stored_word(heap,w,0,0),[w],1,room)),
    u => Done{stored_word(heap,w,0,U32.sub(rc,1))})))

def drops(words: List<&2,U32>, +heap: Heap, +room: U32) -> Result<W.Stop,Heap>:
  match words:
    case Nil{}: Done{heap}
    case Con{+w,rest}: bind(Heap,Heap,drop(heap,room,w),heap => drops(rest,heap,room))

# ---------------------------------------------------------------- code

# The loaded image: record offsets by table index and the constant pool words.
type Code is Data:
  Code{image: W.Store, types: W.Store, constructors: W.Store, functions: W.Store, names: W.Store, pool: W.Store, representation: List<&2,U32>, terminal: U32}

def code_word(+code: Code, +at: U32) -> U32:
  match code:
    case Code{image,types,constructors,functions,names,pool,reps,terminal}: W.read(image,at)

def type_record(+code: Code, +t: U32) -> U32:
  match code:
    case Code{image,types,constructors,functions,names,pool,reps,terminal}: W.read(types,t)

def function_record(+code: Code, +f: U32) -> U32:
  match code:
    case Code{image,types,constructors,functions,names,pool,reps,terminal}: W.read(functions,f)

def name_record(+code: Code, +n: U32) -> U32:
  match code:
    case Code{image,types,constructors,functions,names,pool,reps,terminal}: W.read(names,n)

def pool_word(+code: Code, +c: U32) -> U32:
  match code:
    case Code{image,types,constructors,functions,names,pool,reps,terminal}: W.read(pool,c)

def rep(+code: Code, +r: U32) -> U32:
  match code:
    case Code{image,types,constructors,functions,names,pool,reps,terminal}: W.nth(reps,r)

def terminal(code: Code) -> U32:
  match code:
    case Code{image,types,constructors,functions,names,pool,reps,terminal}: terminal

def is_rep(+code: Code, +t: U32, +r: U32) -> Bool:
  Bool.and(Bool.not(W.is_none(t)),U32.is_eq(t,rep(code,r)))

def type_kind(+code: Code, +t: U32) -> U32:
  W.choose(U32,W.is_none(t),u => W.none(),u => code_word(code,U32.add(type_record(code,t),1)))

def constructor_count(+code: Code, +t: U32) -> U32:
  code_word(code,U32.add(type_record(code,t),4))

def constructor_record(+code: Code, +t: U32, +tag: U32) -> U32:
  match code:
    case Code{+image,types,constructors,functions,names,pool,reps,terminal}:
      W.read(constructors,U32.add(code_word(Code{image,types,constructors,functions,names,pool,reps,terminal},U32.add(W.read(types,t),3)),tag))

def field_count(+code: Code, +t: U32, +tag: U32) -> U32:
  code_word(code,U32.add(constructor_record(code,t,tag),4))

def field_type(+code: Code, +t: U32, +tag: U32, +i: U32) -> U32:
  code_word(code,U32.add(constructor_record(code,t,tag),U32.add(5,i)))

def node_op(+code: Code, +at: U32) -> Nat:
  U32.to_nat(code_word(code,U32.add(at,1)))

def node_type(+code: Code, +at: U32) -> U32:
  code_word(code,U32.add(at,2))

def operand(+code: Code, +at: U32, +i: U32) -> U32:
  code_word(code,U32.add(at,U32.add(3,i)))

def node_last(+code: Code, +at: U32) -> U32:
  code_word(code,U32.sub(U32.add(at,code_word(code,at)),1))

# ---------------------------------------------------------------- frames

# A frame record is [value[n], node, aux, head] (SPEC §6); `Gather` keeps its
# filled operands newest first and reserves `need` slots.
type Frame is Data:
  Top{phase: U32}
  Gather{node: U32, need: U32, got: List<&2,U32>}
  Bind{node: U32}
  Scope{depth: U32}
  Call{caller: U32}
  InvokeFunction{node: U32}
  InvokeArgument{node: U32, function: U32}

def frame_words(frame: Frame) -> U32:
  match frame:
    case Gather{node,need,got}: U32.add(need,3)
    case Call{caller}: 4
    case InvokeArgument{node,function}: 4
    case _: 3

# The current Activation, the frames newest first, and the words they occupy.
type Stack is Data:
  Stack{act: U32, frames: List<&2,Frame>, top: U32}

def room(stack: Stack) -> U32:
  match stack:
    case Stack{act,frames,top}: U32.sub(region_words(),top)

def act_of(stack: Stack) -> U32:
  match stack:
    case Stack{act,frames,top}: act

def pushed(+stack: Stack, +frame: Frame) -> Result<W.Stop,Stack>:
  match stack:
    case Stack{act,frames,+top}:
      W.choose(Result<W.Stop,Stack>,U32.is_gt(frame_words(frame),U32.sub(region_words(),top)),u => Fail{W.Exhausted{3,"frames"}},
        u => Done{Stack{act,Con{frame,frames},U32.add(top,frame_words(frame))}})

def with_act(stack: Stack, act: U32) -> Stack:
  match stack:
    case Stack{old,frames,top}: Stack{act,frames,top}

# Activation payload: owner, depth, slot[capacity].
def depth_of(+heap: Heap, +act: U32) -> U32:
  load_word(heap,act,3)

def slot(+heap: Heap, +act: U32, +i: U32) -> U32:
  load_word(heap,act,U32.add(4,i))

def bound(heap: Heap, +act: U32, +i: U32, w: U32) -> Heap:
  stored_word(heap,act,U32.add(4,i),w)

def deepened(heap: Heap, +act: U32, depth: U32) -> Heap:
  stored_word(heap,act,3,depth)

def binds(words: List<&2,U32>, heap: Heap, +act: U32, +i: U32) -> Heap:
  match words:
    case Nil{}: heap
    case Con{w,rest}: binds(rest,bound(heap,act,i,w),act,U32.add(i,1))

# ---------------------------------------------------------------- inspection

def cell_class(+heap: Heap, +w: U32) -> U32:
  U32.and(load_word(heap,w,1),7)

# A Request is an inert value that only Top's loop reads (SPEC §5, D23); its `k` is its last payload word.
def is_request(+heap: Heap, +w: U32) -> Bool:
  Bool.and(is_pointer(w),U32.is_eq(cell_class(heap,w),5))

def continuation(+heap: Heap, +w: U32) -> U32:
  load_word(heap,w,U32.add(U32.shrn(load_word(heap,w,1),3n),1))

# The word read at type t is of that type (SPEC §6): Nat, U32 and Char admit an
# immediate or a Big cell, File an immediate, and an algebraic type a nullary
# tag or an Object of its own type whose tag has fields.
def admits(+code: Code, +heap: Heap, +t: U32, +w: U32) -> Bool:
  W.choose(Bool,W.or(is_rep(code,t,0),W.or(is_rep(code,t,1),is_rep(code,t,2))),
    u => W.or(U32.is_eq(U32.and(w,1),1),Bool.and(is_pointer(w),U32.is_eq(cell_class(heap,w),2))),u =>
  W.choose(Bool,is_rep(code,t,11),u => U32.is_eq(U32.and(w,1),1),u =>
  W.choose(Bool,Bool.not(U32.is_eq(type_kind(code,t),0)),u => False{},u =>
  W.choose(Bool,U32.is_eq(U32.and(w,1),1),
    u => Bool.and(U32.is_lt(U32.shrn(w,1n),constructor_count(code,t)),U32.is_eq(field_count(code,t,U32.shrn(w,1n)),0)),
    u => Bool.and(Bool.and(is_pointer(w),U32.is_eq(cell_class(heap,w),0)),
          Bool.and(U32.is_eq(load_word(heap,w,2),t),
          Bool.and(U32.is_lt(load_word(heap,w,3),constructor_count(code,t)),Bool.not(U32.is_eq(field_count(code,t,load_word(heap,w,3)),0)))))))))

def ill_typed(-A: Data) -> Result<W.Stop,A>:
  Fail{W.Refused{"image","ill-typed"}}

def unsupported(-A: Data) -> Result<W.Stop,A>:
  Fail{W.Unsupported{"vm","effect"}}

# The class is read first: a Request is refused whatever type the word is read at (SPEC §6, D23).
def inspected_at(-A: Data, +code: Code, +heap: Heap, +t: U32, +w: U32, next: Unit -> Result<W.Stop,A>) -> Result<W.Stop,A>:
  W.choose(Result<W.Stop,A>,is_request(heap,w),u => unsupported(A),u =>
  W.choose(Result<W.Stop,A>,admits(code,heap,t,w),next,u => ill_typed(A)))

# The value of a Nat, U32 or Char word, and the canonical word of a value.
def scalar(+heap: Heap, +w: U32) -> U32:
  W.choose(U32,U32.is_eq(U32.and(w,1),1),u => U32.shrn(w,1n),u => load_word(heap,w,2))

def word_of(+heap: Heap, +v: U32) -> Result<W.Stop,Cell>:
  W.choose(Result<W.Stop,Cell>,boxed(v),u => alloc(heap,2,[v]),u => Done{Cell{heap,immediate(v)}})

# §6.1's tag of an inspected word: Nat's logical view (Zero or Succ), Char's
# one constructor Chr whatever its code, an immediate's value, or an Object's
# payload tag.
def tag_of(+code: Code, +heap: Heap, +t: U32, +w: U32) -> U32:
  W.choose(U32,is_rep(code,t,0),u => Bool.pick(U32,U32.is_eq(scalar(heap,w),0),0,1),u =>
  W.choose(U32,is_rep(code,t,2),u => 0,u =>
    W.choose(U32,U32.is_eq(U32.and(w,1),1),u => U32.shrn(w,1n),u => load_word(heap,w,3))))

# ---------------------------------------------------------------- primitives

def truth(b: Bool) -> U32:
  immediate(Bool.to_u32(b))

def order(+a: U32, +b: U32) -> U32:
  W.choose(U32,U32.is_lt(a,b),u => 0,u => Bool.pick(U32,U32.is_eq(a,b),1,2))

# Comparison k of is_eq, is_ne, is_lt, is_le, is_gt, is_ge, unsigned.
def compared(+k: U32, +a: U32, +b: U32) -> Bool:
  W.nth_bool([U32.is_eq(a,b),U32.is_ne(a,b),U32.is_lt(a,b),U32.is_le(a,b),U32.is_gt(a,b),U32.is_ge(a,b)],k)

def shifted(left: Bool, +a: U32, +n: U32) -> U32:
  W.choose(U32,U32.is_ge(n,32),u => 0,u => Bool.pick(U32,left,U32.shln(a,U32.to_nat(n)),U32.shrn(a,U32.to_nat(n))))

def spaced(+c: U32) -> Bool:
  W.or(W.within(c,9,13),U32.is_eq(c,32))

def digits(fuel: Nat, +v: U32, +acc: List<&2,U32>) -> List<&2,U32>:
  match fuel:
    case 0n: acc
    case 1n+f: W.choose(List<&2,U32>,U32.is_lt(v,10),u => Con{U32.add(48,v),acc},u => digits(f,U32.div(v,10),Con{U32.add(48,U32.mod(v,10)),acc}))

def code_words(codes: List<&2,U32>) -> List<&2,U32>:
  match codes:
    case Nil{}: Nil{}
    case Con{c,rest}: Con{immediate(c),code_words(rest)}

# The Char words of a String, each cell inspected at String and each
# character at Char.
def chars(fuel: Nat, +code: Code, +heap: Heap, +w: U32) -> Result<W.Stop,List<&2,U32>>:
  match fuel:
    case 0n: Fail{W.Internal{"string fuel"}}
    case 1n+f:
      inspected_at(List<&2,U32>,code,heap,rep(code,3),w,u =>
      W.choose(Result<W.Stop,List<&2,U32>>,U32.is_eq(U32.and(w,1),1),u => Done{Nil{}},u =>
      inspected_at(List<&2,U32>,code,heap,rep(code,2),load_word(heap,w,4),u =>
        bind(List<&2,U32>,List<&2,U32>,chars(f,code,heap,load_word(heap,w,5)),rest => Done{Con{load_word(heap,w,4),rest}}))))

def string_of(+code: Code, +heap: Heap, +w: U32) -> Result<W.Stop,List<&2,U32>>:
  chars(U32.to_nat(memory_words()),code,heap,w)

def scalars_of(words: List<&2,U32>, +heap: Heap) -> List<&2,U32>:
  match words:
    case Nil{}: Nil{}
    case Con{w,rest}: Con{scalar(heap,w),scalars_of(rest,heap)}

# SCon cells from the chain's last character to its first, each holding a
# new reference to its character.
def chain(last_first: List<&2,U32>, +code: Code, +heap: Heap, +tail: U32) -> Result<W.Stop,Cell>:
  match last_first:
    case Nil{}: Done{Cell{heap,tail}}
    case Con{+c,rest}:
      bind(Heap,Cell,dup(heap,c),heap =>
        with_cell(Cell,alloc(heap,0,[rep(code,3),1,c,tail]),heap => w => chain(rest,code,heap,w)))

# Nat results are checked before narrowing: above 2^32-1 is NatRange.
def nat_sum(+heap: Heap, +a: U32, +b: U32) -> Result<W.Stop,Cell>:
  W.choose(Result<W.Stop,Cell>,U32.is_gt(b,U32.sub(W.none(),a)),u => Fail{W.Exhausted{2,"NatRange"}},u => word_of(heap,U32.add(a,b)))

def nat_product(+heap: Heap, +a: U32, +b: U32) -> Result<W.Stop,Cell>:
  W.choose(Result<W.Stop,Cell>,Bool.and(Bool.not(U32.is_eq(a,0)),U32.is_gt(b,U32.div(W.none(),a))),u => Fail{W.Exhausted{2,"NatRange"}},u => word_of(heap,U32.mul(a,b)))

def immediate_cell(+heap: Heap, +w: U32) -> Result<W.Stop,Cell>:
  Done{Cell{heap,w}}

def string_cell(+code: Code, +heap: Heap, +w: U32, next: List<&2,U32> -> Result<W.Stop,Cell>) -> Result<W.Stop,Cell>:
  bind(List<&2,U32>,Cell,string_of(code,heap,w),next)

# SPEC §9 on inspected operand words `a` and `b`; the result is allocated
# before any operand is dropped. A String operand is read whole first, each
# SCon cell and its Char word, `a` then `b`, even the `b` append moves.
def computed(id: Nat, +code: Code, +heap: Heap, +a: U32, +b: U32, +x: U32, +y: U32) -> Result<W.Stop,Cell>:
  match id:
    case 0n: word_of(heap,U32.add(x,y))
    case 1n: word_of(heap,U32.sub(x,y))
    case 2n: word_of(heap,U32.mul(x,y))
    case 3n: word_of(heap,W.choose(U32,U32.is_eq(y,0),u => 0,u => U32.div(x,y)))
    case 4n: word_of(heap,W.choose(U32,U32.is_eq(y,0),u => x,u => U32.mod(x,y)))
    case 5n: word_of(heap,U32.not(x))
    case 6n: word_of(heap,U32.and(x,y))
    case 7n: immediate_cell(heap,immediate(order(x,y)))
    case 8n: immediate_cell(heap,truth(compared(0,x,y)))
    case 9n: immediate_cell(heap,truth(compared(1,x,y)))
    case 10n: immediate_cell(heap,truth(compared(2,x,y)))
    case 11n: immediate_cell(heap,truth(compared(3,x,y)))
    case 12n: immediate_cell(heap,truth(compared(4,x,y)))
    case 13n: immediate_cell(heap,truth(compared(5,x,y)))
    case 14n: word_of(heap,shifted(True{},x,y))
    case 15n: word_of(heap,shifted(False{},x,y))
    case 16n: immediate_cell(heap,a)
    case 17n: immediate_cell(heap,a)
    case 18n: immediate_cell(heap,a)
    case 19n: immediate_cell(heap,a)
    case 20n: immediate_cell(heap,truth(U32.is_eq(x,y)))
    case 21n: immediate_cell(heap,truth(spaced(x)))
    case 22n: nat_sum(heap,x,y)
    case 23n: word_of(heap,W.choose(U32,U32.is_lt(x,y),u => 0,u => U32.sub(x,y)))
    case 24n: nat_product(heap,x,y)
    case 25n: immediate_cell(heap,immediate(order(x,y)))
    case 26n: immediate_cell(heap,truth(compared(0,x,y)))
    case 27n: immediate_cell(heap,truth(compared(1,x,y)))
    case 28n: immediate_cell(heap,truth(compared(2,x,y)))
    case 29n: immediate_cell(heap,truth(compared(3,x,y)))
    case 30n: immediate_cell(heap,truth(compared(4,x,y)))
    case 31n: immediate_cell(heap,truth(compared(5,x,y)))
    case 32n: chain(List.reverse(&2,U32,code_words(digits(10n,x,Nil{}))),code,heap,immediate(0))
    case 33n: chain(List.reverse(&2,U32,code_words(digits(10n,x,Nil{}))),code,heap,immediate(0))
    case 34n: string_cell(code,heap,a,s => string_cell(code,heap,b,t => immediate_cell(heap,truth(W.same(scalars_of(s,heap),scalars_of(t,heap))))))
    case 35n: string_cell(code,heap,a,s => string_cell(code,heap,b,t => chain(List.reverse(&2,U32,s),code,heap,b)))
    case 36n: string_cell(code,heap,a,s => chain(s,code,heap,immediate(0)))
    case 37n: string_cell(code,heap,a,s => word_of(heap,W.count(U32,s)))
    case 38n: string_cell(code,heap,a,s => immediate_cell(heap,truth(U32.is_eq(W.count(U32,s),0))))
    case _: Fail{W.Refused{"image","prim"}}

def compute(+id: U32, +code: Code, +heap: Heap, +a: U32, +b: U32) -> Result<W.Stop,Cell>:
  computed(U32.to_nat(id),code,heap,a,b,scalar(heap,a),scalar(heap,b))

# Operands the prim moves into its result: append's tail and the word-keeping
# conversions. Every other operand is dropped after the result exists.
def moved(+id: U32, +i: U32) -> Bool:
  W.or(Bool.and(U32.is_eq(id,35),U32.is_eq(i,1)),Bool.and(W.within(id,16,19),U32.is_eq(i,0)))

def dropped_operands(+id: U32, words: List<&2,U32>, +i: U32) -> List<&2,U32>:
  match words:
    case Nil{}: Nil{}
    case Con{+w,+rest}: W.choose(List<&2,U32>,moved(id,i),u => dropped_operands(id,rest,U32.add(i,1)),u => Con{w,dropped_operands(id,rest,U32.add(i,1))})

# A String operand is read whole by the prim itself, in operand order (SPEC §9): no prim takes one beside another representation.
def operand_read(+code: Code, +heap: Heap, +w: U32, +r: U32) -> Result<W.Stop,Unit>:
  W.choose(Result<W.Stop,Unit>,U32.is_eq(r,3),u => Done{Unit{}},u => inspected_at(Unit,code,heap,rep(code,r),w,u => Done{Unit{}}))

def operands_read(-A: Data, +code: Code, +heap: Heap, words: List<&2,U32>, inputs: List<&2,U32>, next: Unit -> Result<W.Stop,A>) -> Result<W.Stop,A>:
  match words inputs:
    case Con{w,ws} Con{r,rs}: bind(Unit,A,operand_read(code,heap,w,r),u => operands_read(A,code,heap,ws,rs,next))
    case _ _: next(Unit{})

def primitive_inputs(entry: Maybe<&2,V.Primitive>) -> List<&2,U32>:
  match entry:
    case Some{V.Primitive{inputs,output}}: inputs
    case None{}: Nil{}

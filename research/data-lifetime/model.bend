import Base

# Policy 0 copies Data; policy 1 counts its incoming obligations.
type Cell is Data:
  Cell{id: U32, kind: U32, tag: U32, refs: U32, children: List<&2,U32>}

type Holder is Data:
  Holder{slot: U32, ref: U32}

type Heap is Data:
  Heap{policy: U32, limit: U32, ceiling: U32, next: U32,
    cells: List<&2,Cell>, roots: List<&2,Holder>, pending: List<&2,U32>,
    readers: List<&2,Holder>, cost: List<&2,U32>, drops: List<&2,U32>}

# Reusable snapshots are model metadata; the public transition consumes Store.
type Store is Type:
  Store{heap: Heap}

type Command is Data:
  Alloc{dst: U32, kind: U32, tag: U32, children: List<&2,U32>}
  Share{src: U32, dst: U32}
  Take{src: U32, children: List<&2,U32>}
  Transfer{src: U32, dst: U32}
  Release{src: U32}
  Clean{budget: Nat}
  Pin{src: U32, lease: U32}
  Ack{lease: U32}
  Cycle{}

def choose(-A: Type, test: Bool, yes: Unit -> A, no: Unit -> A) -> A:
  match test:
    case True{}: yes(Unit{})
    case False{}: no(Unit{})

def bind(-A: Data, -B: Data, result: Result<U32,A>, next: A -> Result<U32,B>) -> Result<U32,B>:
  match result:
    case Fail{e}: Fail{e}
    case Done{x}: next(x)

def length(xs: List<&2,U32>) -> U32:
  match xs:
    case Nil{}: 0
    case Con{h,t}: U32.add(1,length(t))

def at(n: Nat, xs: List<&2,U32>) -> U32:
  match n xs:
    case 0n Nil{}: 0
    case 0n Con{h,t}: h
    case 1n+n Nil{}: 0
    case 1n+n Con{h,t}: at(n,t)

def set(n: Nat, xs: List<&2,U32>, value: U32) -> List<&2,U32>:
  match n xs:
    case 0n Nil{}: Nil{}
    case 0n Con{h,t}: Con{value,t}
    case 1n+n Nil{}: Nil{}
    case 1n+n Con{h,t}: Con{h,set(n,t,value)}

def add(+xs: List<&2,U32>, +n: Nat, value: U32) -> List<&2,U32>:
  set(n,xs,U32.add(at(n,xs),value))

def maximum(+a: U32, +b: U32) -> U32:
  Bool.pick(U32,U32.is_lt(a,b),b,a)

def member(+x: U32, xs: List<&2,U32>) -> Bool:
  match xs:
    case Nil{}: False{}
    case Con{h,t}: Bool.or(U32.is_eq(x,h),member(x,t))

def root(+slot: U32, roots: List<&2,Holder>) -> U32:
  match roots:
    case Nil{}: 0
    case Con{Holder{s,r},t}: choose(U32,U32.is_eq(slot,s),u => r,u => root(slot,t))

def omit(+slot: U32, roots: List<&2,Holder>) -> List<&2,Holder>:
  match roots:
    case Nil{}: Nil{}
    case Con{+h,+t}:
      match h:
        case Holder{s,r}: choose(List<&2,Holder>,U32.is_eq(slot,s),u => t,u => Con{h,omit(slot,t)})

def omit_all(slots: List<&2,U32>, roots: List<&2,Holder>) -> List<&2,Holder>:
  match slots:
    case Nil{}: roots
    case Con{h,t}: omit_all(t,omit(h,roots))

def install(slots: List<&2,U32>, refs: List<&2,U32>, roots: List<&2,Holder>) -> List<&2,Holder>:
  match slots refs:
    case Con{s,ss} Con{r,rs}: install(ss,rs,Con{Holder{s,r},roots})
    case _ _: roots

def vacant(slots: List<&2,U32>, +roots: List<&2,Holder>) -> Bool:
  match slots:
    case Nil{}: True{}
    case Con{+h,+t}:
      Bool.and(U32.is_eq(root(h,roots),0),Bool.and(Bool.not(member(h,t)),vacant(t,roots)))

def gather(slots: List<&2,U32>, +roots: List<&2,Holder>) -> Result<U32,List<&2,U32>>:
  match slots:
    case Nil{}: Done{Nil{}}
    case Con{+h,+t}:
      +r = root(h,roots)
      choose(Result<U32,List<&2,U32>>,Bool.or(U32.is_eq(r,0),member(h,t)),u => Fail{1},u =>
        bind(List<&2,U32>,List<&2,U32>,gather(t,roots),rest => Done{Con{r,rest}}))

def cell(+ref: U32, cells: List<&2,Cell>) -> Result<U32,Cell>:
  match cells:
    case Nil{}: Fail{5}
    case Con{+h,+t}:
      match h:
        case Cell{id,k,v,n,cs}: choose(Result<U32,Cell>,U32.is_eq(ref,id),u => Done{h},u => cell(ref,t))

def erase(+ref: U32, cells: List<&2,Cell>) -> List<&2,Cell>:
  match cells:
    case Nil{}: Nil{}
    case Con{+h,+t}:
      match h:
        case Cell{id,k,v,n,cs}: choose(List<&2,Cell>,U32.is_eq(ref,id),u => t,u => Con{h,erase(ref,t)})

def count(+ref: U32, cells: List<&2,Cell>, +n: U32) -> List<&2,Cell>:
  match cells:
    case Nil{}: Nil{}
    case Con{+h,+t}:
      match h:
        case Cell{+id,k,v,old,cs}:
          choose(List<&2,Cell>,U32.is_eq(ref,id),u => Con{Cell{id,k,v,n,cs},t},u => Con{h,count(ref,t,n)})

def payload(c: Cell) -> U32:
  match c:
    case Cell{i,k,t,n,cs}: U32.add(2,length(cs))

def words(policy: U32, +c: Cell) -> U32:
  match c:
    case Cell{i,k,t,n,cs}:
      U32.add(payload(c),Bool.pick(U32,Bool.and(U32.is_eq(k,1),U32.is_eq(policy,1)),1,0))

def initial(policy: U32, limit: U32, ceiling: U32) -> Heap:
  Heap{policy,limit,ceiling,1,Nil{},Nil{},Nil{},Nil{},[0,0,0,0,0,0,0,0,0,0],Nil{}}

def with_roots(heap: Heap, roots: List<&2,Holder>) -> Heap:
  match heap:
    case Heap{p,l,c,n,cs,rs,q,r,m,d}: Heap{p,l,c,n,cs,roots,q,r,m,d}

def with_readers(heap: Heap, readers: List<&2,Holder>) -> Heap:
  match heap:
    case Heap{p,l,c,n,cs,rs,q,r,m,d}: Heap{p,l,c,n,cs,rs,q,readers,m,d}

def charged(heap: Heap, index: Nat, amount: U32) -> Heap:
  match heap:
    case Heap{p,l,c,n,cs,rs,q,r,m,d}: Heap{p,l,c,n,cs,rs,q,r,add(m,index,amount),d}

def queued(heap: Heap, +pending: List<&2,U32>) -> Heap:
  match heap:
    case Heap{p,l,c,n,cs,rs,q,r,+m,d}:
      Heap{p,l,c,n,cs,rs,pending,r,set(9n,m,maximum(at(9n,m),length(pending))),d}

type Allocation is Data:
  Allocation{heap: Heap, ref: U32}

def allocate(+heap: Heap, kind: U32, tag: U32, children: List<&2,U32>) -> Result<U32,Allocation>:
  match heap:
    case Heap{+p,+limit,c,+n,cs,rs,q,r,+m,d}:
      +value : Cell = Cell{n,kind,tag,1,children}
      +size = words(p,value)
      +live = at(7n,m)
      choose(Result<U32,Allocation>,Bool.or(U32.is_gt(size,limit),Bool.or(U32.is_gt(live,U32.sub(limit,size)),U32.is_eq(n,4294967295))),
        u => Fail{3},u =>
          Done{Allocation{Heap{p,limit,c,U32.add(n,1),Con{value,cs},rs,q,r,
            set(8n,set(7n,add(m,0n,1),U32.add(live,size)),maximum(at(8n,m),U32.add(live,size))),d},n}})

def free(heap: Heap, +value: Cell) -> Heap:
  match heap value:
    case Heap{+p,l,c,n,cs,rs,q,r,+m,d} Cell{id,k,t,refs,children}:
      Heap{p,l,c,n,erase(id,cs),rs,q,r,set(7n,add(m,1n,1),U32.sub(at(7n,m),words(p,value))),d}

def retained(value: Cell, heap: Heap) -> Result<U32,Heap>:
  match value heap:
    case Cell{+id,k,t,+refs,cs} Heap{p,l,+ceiling,n,cells,rs,q,r,m,d}:
      choose(Result<U32,Heap>,U32.is_eq(k,1),u =>
        choose(Result<U32,Heap>,U32.is_lt(refs,ceiling),u =>
          Done{Heap{p,l,ceiling,n,count(id,cells,U32.add(refs,1)),rs,q,r,add(m,4n,1),d}},u => Fail{3}),u => Fail{2})

def acquire(+heap: Heap, ref: U32) -> Result<U32,Heap>:
  match heap:
    case Heap{p,l,c,n,cells,rs,q,r,m,d}:
      bind(Cell,Heap,cell(ref,cells),value => retained(value,heap))

def acquire_all(refs: List<&2,U32>, heap: Heap) -> Result<U32,Heap>:
  match refs:
    case Nil{}: Done{heap}
    case Con{h,t}: bind(Heap,Heap,acquire(heap,h),next => acquire_all(t,next))

def decremented(heap: Heap, ref: U32, refs: U32) -> Heap:
  match heap:
    case Heap{p,l,c,n,cs,rs,q,r,m,d}: Heap{p,l,c,n,count(ref,cs,U32.sub(refs,1)),rs,q,r,m,d}

def data_cell(value: Cell) -> Result<U32,Unit>:
  match value:
    case Cell{i,k,t,n,cs}: Bool.pick(Result<U32,Unit>,U32.is_eq(k,1),Done{Unit{}},Fail{1})

def data_edges(refs: List<&2,U32>, +cells: List<&2,Cell>) -> Result<U32,Unit>:
  match refs:
    case Nil{}: Done{Unit{}}
    case Con{h,t}:
      bind(Cell,Unit,cell(h,cells),value =>
        bind(Unit,Unit,data_cell(value),u => data_edges(t,cells)))

type CopyFrame is Data:
  Visit{ref: U32}
  Assemble{kind: U32, tag: U32, shape: List<&2,U32>}

type Copying is Data:
  Copying{heap: Heap, frames: List<&2,CopyFrame>, values: List<&2,U32>}

def visits(refs: List<&2,U32>, tail: List<&2,CopyFrame>) -> List<&2,CopyFrame>:
  match refs:
    case Nil{}: tail
    case Con{h,t}: Con{Visit{h},visits(t,tail)}

def copying(pair: Allocation, frames: List<&2,CopyFrame>, values: List<&2,U32>) -> Result<U32,Copying>:
  match pair:
    case Allocation{heap,ref}:
      Done{Copying{heap,frames,Con{ref,values}}}


def assemble(shape: List<&2,U32>, values: List<&2,U32>, heap: Heap, kind: U32, tag: U32, frames: List<&2,CopyFrame>) -> Result<U32,Copying>:
  match shape values:
    case Nil{} _:
      bind(Allocation,Copying,allocate(heap,kind,tag,Nil{}),pair => copying(pair,frames,values))
    case Con{x,Nil{}} Con{a,rest}:
      bind(Allocation,Copying,allocate(heap,kind,tag,[a]),pair => copying(pair,frames,rest))
    case Con{x,Con{y,Nil{}}} Con{b,Con{a,rest}}:
      bind(Allocation,Copying,allocate(heap,kind,tag,[a,b]),pair => copying(pair,frames,rest))
    case _ _: Fail{5}

def enter_copy(value: Cell, heap: Heap, frames: List<&2,CopyFrame>, values: List<&2,U32>) -> Result<U32,Copying>:
  match value:
    case Cell{i,k,t,n,+cs}:
      Done{Copying{heap,visits(cs,Con{Assemble{k,t,cs},frames}),values}}

def lookup(heap: Heap, ref: U32) -> Result<U32,Cell>:
  match heap:
    case Heap{p,l,c,n,cells,rs,q,r,m,d}: cell(ref,cells)

def copy_step(state: Copying) -> Result<U32,Copying>:
  match state:
    case Copying{heap,Nil{},values}: Done{state}
    case Copying{+heap,Con{Visit{ref},tail},values}:
      bind(Cell,Copying,lookup(heap,ref),value => enter_copy(value,heap,tail,values))
    case Copying{heap,Con{Assemble{k,t,+shape},tail},values}:
      assemble(shape,values,charged(charged(heap,2n,U32.add(2,length(shape))),3n,length(shape)),k,t,tail)

def copy_run(fuel: Nat, +state: Copying) -> Result<U32,Allocation>:
  match fuel state:
    case _ Copying{heap,Nil{},Con{ref,Nil{}}}: Done{Allocation{heap,ref}}
    case 0n _: Fail{3}
    case 1n+n _: bind(Copying,Allocation,copy_step(state),next => copy_run(n,next))

def copy(heap: Heap, ref: U32) -> Result<U32,Allocation>:
  copy_run(65536n,Copying{heap,[Visit{ref}],Nil{}})

def held(pair: Allocation, dst: U32) -> Heap:
  match pair:
    case Allocation{heap,ref}:
      match heap:
        case Heap{p,l,c,n,cs,rs,q,r,m,d}: Heap{p,l,c,n,cs,Con{Holder{dst,ref},rs},q,r,m,d}


def constructed(pair: Allocation, dst: U32, slots: List<&2,U32>) -> Heap:
  match pair:
    case Allocation{heap,ref}:
      match heap:
        case Heap{p,l,c,n,cs,rs,q,r,m,d}:
          Heap{p,l,c,n,cs,Con{Holder{dst,ref},omit_all(slots,rs)},q,r,m,d}


def alloc(+heap: Heap, +dst: U32, +kind: U32, tag: U32, +slots: List<&2,U32>) -> Result<U32,Heap>:
  match heap:
    case Heap{p,l,c,n,+cells,+rs,q,r,m,d}:
      choose(Result<U32,Heap>,Bool.and(vacant([dst],rs),Bool.and(U32.is_le(kind,1),U32.is_le(length(slots),2))),u =>
        bind(List<&2,U32>,Heap,gather(slots,rs),+refs =>
          bind(Unit,Heap,choose(Result<U32,Unit>,U32.is_eq(kind,1),u => data_edges(refs,cells),u => Done{Unit{}}),u =>
            bind(Allocation,Heap,allocate(heap,kind,tag,refs),pair => Done{constructed(pair,dst,slots)}))),u => Fail{1})

def shared(value: Cell, +heap: Heap, +dst: U32) -> Result<U32,Heap>:
  match value heap:
    case Cell{+id,k,t,n,cs} Heap{p,l,c,next,cells,rs,q,r,m,d}:
      choose(Result<U32,Heap>,U32.is_eq(k,1),u =>
        choose(Result<U32,Heap>,U32.is_eq(p,0),u =>
          bind(Allocation,Heap,copy(heap,id),pair => Done{held(pair,dst)}),u =>
          bind(Heap,Heap,acquire(heap,id),next => Done{held(Allocation{next,id},dst)})),u => Fail{2})

def share(+heap: Heap, src: U32, +dst: U32) -> Result<U32,Heap>:
  match heap:
    case Heap{p,l,c,n,cells,+rs,q,r,m,d}:
      +ref = root(src,rs)
      choose(Result<U32,Heap>,Bool.and(Bool.not(U32.is_eq(ref,0)),vacant([dst],rs)),u =>
        bind(Cell,Heap,cell(ref,cells),value => shared(value,heap,dst)),u => Fail{1})

def transferred(heap: Heap, src: U32, slots: List<&2,U32>, refs: List<&2,U32>) -> Heap:
  match heap:
    case Heap{p,l,c,n,cs,rs,q,r,m,d}: Heap{p,l,c,n,cs,install(slots,refs,omit(src,rs)),q,r,m,d}

def opened(+value: Cell, +heap: Heap, src: U32, +slots: List<&2,U32>) -> Result<U32,Heap>:
  match value heap:
    case Cell{+id,k,t,+refs,+children} Heap{p,l,c,n,cs,rs,q,r,m,d}:
      +charged_heap = charged(charged(heap,3n,length(children)),5n,
        Bool.pick(U32,Bool.and(U32.is_eq(p,1),U32.is_eq(k,1)),1,0))
      bind(Heap,Heap,choose(Result<U32,Heap>,U32.is_eq(refs,1),u => Done{free(charged_heap,value)},u =>
        bind(Heap,Heap,acquire_all(children,charged_heap),next => Done{decremented(next,id,refs)})),next =>
          Done{transferred(next,src,slots,children)})

def take_cell(+value: Cell, +heap: Heap, src: U32, +slots: List<&2,U32>) -> Result<U32,Heap>:
  match value heap:
    case Cell{id,k,t,refs,children} Heap{p,l,c,n,cs,rs,q,readers,m,d}:
      choose(Result<U32,Heap>,Bool.and(vacant(slots,rs),U32.is_eq(length(slots),length(children))),u =>
        choose(Result<U32,Heap>,List.is_empty(&2,Holder,readers),u => opened(value,heap,src,slots),u => Fail{2}),u => Fail{1})

def take(+heap: Heap, +src: U32, slots: List<&2,U32>) -> Result<U32,Heap>:
  match heap:
    case Heap{p,l,c,n,cs,rs,q,r,m,d}:
      +ref = root(src,rs)
      choose(Result<U32,Heap>,U32.is_eq(ref,0),u => Fail{1},u =>
        bind(Cell,Heap,cell(ref,cs),value => take_cell(value,heap,src,slots)))

def move(+heap: Heap, +src: U32, +dst: U32) -> Result<U32,Heap>:
  match heap:
    case Heap{p,l,c,n,cs,+rs,q,r,m,d}:
      +ref = root(src,rs)
      choose(Result<U32,Heap>,Bool.and(Bool.not(U32.is_eq(ref,0)),vacant([dst],rs)),u =>
        Done{with_roots(heap,Con{Holder{dst,ref},omit(src,rs)})},u => Fail{1})

def release(+heap: Heap, +src: U32) -> Result<U32,Heap>:
  match heap:
    case Heap{p,l,c,n,cs,+rs,q,r,m,d}:
      +ref = root(src,rs)
      choose(Result<U32,Heap>,U32.is_eq(ref,0),u => Fail{1},u =>
        Done{queued(with_roots(heap,omit(src,rs)),Con{ref,q})})

def dropped(heap: Heap, kind: U32, tag: U32) -> Heap:
  match heap:
    case Heap{p,l,c,n,cs,rs,q,r,m,+d}:
      Heap{p,l,c,n,cs,rs,q,r,m,Bool.pick(List<&2,U32>,U32.is_eq(kind,0),Con{tag,d},d)}

def release_cell(+value: Cell, +heap: Heap) -> Heap:
  match value heap:
    case Cell{+id,+k,t,+refs,+children} Heap{p,l,c,n,cs,rs,q,r,m,d}:
      +charged_heap = charged(heap,5n,Bool.pick(U32,Bool.and(U32.is_eq(p,1),U32.is_eq(k,1)),1,0))
      choose(Heap,U32.is_eq(refs,1),u =>
        queued(dropped(free(charged(charged_heap,3n,length(children)),value),k,t),List.append(&2,U32,children,q)),u =>
          decremented(charged_heap,id,refs))

def clean_step(+heap: Heap) -> Result<U32,Heap>:
  match heap:
    case Heap{p,l,c,n,cs,rs,Nil{},r,m,d}: Done{heap}
    case Heap{p,l,c,n,cs,rs,Con{ref,tail},r,m,d}:
      bind(Cell,Heap,cell(ref,cs),value => Done{release_cell(value,charged(queued(heap,tail),6n,1))})

def continue_clean(result: Result<U32,Heap>, original: Heap, next: Heap -> Heap & U32) -> Heap & U32:
  match result:
    case Fail{error}: (original,error)
    case Done{heap}: next(heap)

def clean(fuel: Nat, +heap: Heap) -> Heap & U32:
  match fuel heap:
    case _ Heap{p,l,c,n,cs,rs,Nil{},r,m,d}: (heap,0)
    case 0n _: (heap,3)
    case 1n+n Heap{p,l,c,next,cs,rs,q,Con{h,t},m,d}: (heap,3)
    case 1n+n _:
      continue_clean(clean_step(heap),heap,next => clean(n,next))

def pin(+heap: Heap, src: U32, +lease: U32) -> Result<U32,Heap>:
  match heap:
    case Heap{p,l,c,n,cs,rs,q,+r,m,d}:
      +ref = root(src,rs)
      choose(Result<U32,Heap>,Bool.and(Bool.not(U32.is_eq(ref,0)),U32.is_eq(root(lease,r),0)),u =>
        Done{with_readers(heap,Con{Holder{lease,ref},r})},u => Fail{1})

def ack(+heap: Heap, +lease: U32) -> Result<U32,Heap>:
  match heap:
    case Heap{p,l,c,n,cs,rs,q,+r,m,d}:
      choose(Result<U32,Heap>,U32.is_eq(root(lease,r),0),u => Fail{1},u => Done{with_readers(heap,omit(lease,r))})

def commit(result: Result<U32,Heap>, original: Heap) -> Heap & U32:
  match result:
    case Fail{error}: (original,error)
    case Done{heap}: (heap,0)

def step(command: Command, +heap: Heap) -> Heap & U32:
  match command:
    case Alloc{dst,kind,tag,slots}: commit(alloc(heap,dst,kind,tag,slots),heap)
    case Share{src,dst}: commit(share(heap,src,dst),heap)
    case Take{src,slots}: commit(take(heap,src,slots),heap)
    case Transfer{src,dst}: commit(move(heap,src,dst),heap)
    case Release{src}: commit(release(heap,src),heap)
    case Clean{budget}: clean(budget,heap)
    case Pin{src,lease}: commit(pin(heap,src,lease),heap)
    case Ack{lease}: commit(ack(heap,lease),heap)
    case Cycle{}: (heap,2)

def wrapped(pair: Heap & U32) -> Store & U32:
  (heap,status) = pair
  (Store{heap},status)

def transition(command: Command, store: Store) -> Store & U32:
  match store:
    case Store{heap}: wrapped(step(command,heap))

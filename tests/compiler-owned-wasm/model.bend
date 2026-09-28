import Base

# Independent allocation metadata. Values are scalar observations of owners.
type Cell is Data:
  Cell{pointer: U32, slots: U32, value: U32}
type Pool is Data:
  Pool{end: U32, next: U32, free: List<&2,Cell>, live: List<&2,Cell>}
type Selection is Data:
  Missing{}
  Selected{cell: Cell, rest: List<&2,Cell>}
type Allocation is Data:
  Allocated{pool: Pool, pointer: U32}
  Rejected{pool: Pool, status: U32}

def choose(-A: Type, test: Bool, yes: Unit -> A, no: Unit -> A) -> A:
  match test:
    case True{}: yes(Unit{})
    case False{}: no(Unit{})

def restore(head: Cell, tail: Selection) -> Selection:
  match tail:
    case Missing{}: Missing{}
    case Selected{cell,rest}: Selected{cell,Con{head,rest}}

def select(cells: List<&2,Cell>, +key: U32, +by_class: Bool) -> Selection:
  match cells:
    case Nil{}: Missing{}
    case Con{+cell,+tail}:
      match cell:
        case Cell{pointer,slots,value}:
          choose(Selection,U32.is_eq(Bool.pick(U32,by_class,slots,pointer),key),u => Selected{cell,tail},u => restore(cell,select(tail,key,by_class)))

def initial(capacity: U32) -> Pool: Pool{U32.add(65536,capacity),65536,Nil{},Nil{}}

def reserve(selected: Selection, +pool: Pool, +slots: U32, +value: U32) -> Allocation:
  match selected pool:
    case Selected{Cell{+pointer,old,discarded},rest} Pool{end,next,free,live}:
      Allocated{Pool{end,next,rest,Con{Cell{pointer,slots,value},live}},pointer}
    case Missing{} Pool{end,+next,free,live}:
      +size = U32.add(16,U32.mul(4,slots))
      choose(Allocation,U32.is_gt(size,U32.sub(end,next)),u => Rejected{pool,3},u =>
        Allocated{Pool{end,U32.add(next,size),free,Con{Cell{U32.add(next,12),slots,value},live}},U32.add(next,12)})

def alloc(+pool: Pool, +slots: U32, +value: U32) -> Allocation:
  match pool:
    case Pool{end,next,free,live}:
      choose(Allocation,U32.is_lt(slots,4096),u => reserve(select(free,slots,True{}),pool,slots,value),u => Rejected{pool,3})

def recycled(selected: Selection, +pool: Pool) -> Pool & U32:
  match selected pool:
    case Missing{} _: (pool,5)
    case Selected{cell,rest} Pool{end,next,free,live}: (Pool{end,next,Con{cell,free},rest},0)

def release(+pool: Pool, pointer: U32) -> Pool & U32:
  match pool:
    case Pool{end,next,free,live}: recycled(select(live,pointer,False{}),pool)

def free_head(cells: List<&2,Cell>, +slots: U32) -> U32:
  match cells:
    case Nil{}: 0
    case Con{Cell{pointer,size,value},+tail}: choose(U32,U32.is_eq(slots,size),u => pointer,u => free_head(tail,slots))

def free_next(cells: List<&2,Cell>, +pointer: U32, +slots: U32) -> U32:
  match cells:
    case Nil{}: 0
    case Con{Cell{address,size,value},+tail}: choose(U32,U32.is_eq(pointer,address),u => free_head(tail,slots),u => free_next(tail,pointer,slots))

def cell_words(selected: Selection, +free: List<&2,Cell>, +live: Bool) -> List<&2,U32>:
  match selected:
    case Missing{}: Nil{}
    case Selected{Cell{+pointer,+slots,value},rest}:
      [pointer,Bool.pick(U32,live,1,0),Bool.pick(U32,live,1,free_next(free,pointer,slots)),slots,value]

def words(+pool: Pool, +pointer: U32) -> List<&2,U32>:
  match pool:
    case Pool{end,next,+free,+live}:
      choose(List<&2,U32>,U32.is_ge(pointer,next),u => Nil{},u =>
        choose(List<&2,U32>,List.is_empty(&2,U32,cell_words(select(live,pointer,False{}),free,True{})),u =>
          cell_words(select(free,pointer,False{}),free,False{}),u => cell_words(select(live,pointer,False{}),free,True{})))

def at(index: Nat, values: List<&2,U32>) -> U32:
  match index values:
    case 0n Nil{}: 0
    case 0n Con{head,tail}: head
    case 1n+n Nil{}: 0
    case 1n+n Con{head,tail}: at(n,tail)

def cells(fuel: Nat, +pool: Pool, +pointer: U32) -> List<&2,U32>:
  match fuel:
    case 0n: Nil{}
    case 1n+n:
      +entry = words(pool,pointer)
      choose(List<&2,U32>,List.is_empty(&2,U32,entry),u => Nil{},u =>
        List.append(&2,U32,entry,cells(n,pool,U32.add(pointer,U32.add(16,U32.mul(4,at(3n,entry)))))))

def snapshot(+pool: Pool) -> List<&2,U32>:
  match pool:
    case Pool{end,+next,+free,live}:
      List.append(&2,U32,[next,U32.from_nat(List.length(&2,Cell,live)),free_head(free,0),free_head(free,1),free_head(free,2)],cells(4096n,pool,65548))

def allocated_release(result: Allocation) -> Pool & U32:
  match result:
    case Rejected{pool,status}: (pool,status)
    case Allocated{pool,pointer}: release(pool,pointer)

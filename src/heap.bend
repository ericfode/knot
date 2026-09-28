import Base
import 0xc409b77d3230ca33374caf6b0993f0cb/bytes.bend as B
import ./syntax.bend as S
import ./wasm-bytes.bend as W
import ./heap-code.bend as A

type Layout is Data:
  Layout{reusable: Bool, edges: List<&2,Bool>}

# Payload p is [tag][live slots]. Prefix p-12/p-8/p-4 is state/count/layout.
# Free cells use count as the next link. Dropping cells stay live until scanned.
def slots(layout: Layout) -> U32:
  match layout:
    case Layout{kind,edges}: U32.from_nat(List.length(&2,Bool,edges))

def bytes(count: U32) -> U32: U32.mul(4,U32.add(count,4))
def class_address(count: U32) -> U32: U32.mul(4,count)
def frame_address(index: U32) -> U32: U32.add(16384,U32.mul(8,index))
def payload_address(header: U32) -> U32: U32.add(header,12)

def fail(status: U32) -> List<&2,A.Instruction>:
  [A.word(status),A.global_set(4),A.op(0)]

def outcome(+status: U32) -> List<&2,A.Instruction>:
  [A.word(status),A.global_set(4),A.word(status),A.op(15)]

def prefix(pointer: U32, offset: U32) -> List<&2,A.Instruction>:
  [A.get(pointer),A.word(12),A.op(107),A.load(offset)]

def write_prefix(pointer: U32, offset: U32, value: List<&2,A.Instruction>) -> List<&2,A.Instruction>:
  A.concat([[A.get(pointer),A.word(12),A.op(107)],value,[A.save(offset)]])

def retain_count(pointer: U32, count: U32) -> List<&2,A.Instruction>:
  write_prefix(pointer,4,[A.get(count),A.word(1),A.op(106)])

def begin_drop(+pointer: U32, frame: U32) -> List<&2,A.Instruction>:
  A.concat([write_prefix(pointer,0,[A.word(2)]),write_prefix(pointer,4,[A.word(0)]),A.write_field(frame,4,[A.word(1)])])

def stack_room() -> List<&2,A.Instruction>:
  A.concat([
    A.guard([A.global_get(5),A.global_get(7),A.op(79)],outcome(3)),
    A.guard([A.global_get(5),A.word(4096),A.op(79)],outcome(3))])

def recycle(+pointer: U32, +class: U32) -> List<&2,A.Instruction>:
  A.concat([write_prefix(pointer,0,[A.word(0)]),write_prefix(pointer,4,[A.get(class),A.load(0)]),
    [A.get(class),A.get(pointer),A.save(0),A.global_get(1),A.word(1),A.op(107),A.global_set(1)]])

def unique_open(base: U32) -> List<&2,A.Instruction>:
  [A.get(0),A.call(U32.add(base,10)),A.op(15)]

def bump_global(+index: U32, amount: U32) -> List<&2,A.Instruction>:
  [A.global_get(index),A.word(amount),A.op(106),A.global_set(index)]

def maximum_global(+current: U32, +peak: U32) -> List<&2,A.Instruction>:
  A.guard([A.global_get(current),A.global_get(peak),A.op(75)],[A.global_get(current),A.global_set(peak)])

def slot_address(pointer: U32, index: U32) -> List<&2,A.Instruction>:
  [A.get(pointer),A.get(index),A.word(4),A.op(108),A.op(106)]

def loop(body: List<&2,A.Instruction>) -> List<&2,A.Instruction>:
  [A.Block{2,[A.Block{3,body}]}]

def edge_cases(edges: List<&2,Bool>, +index: U32) -> List<&2,A.Instruction>:
  match edges:
    case Nil{}: [A.word(0),A.op(15)]
    case Con{edge,tail}:
      A.concat([A.guard([A.get(1),A.word(index),A.op(70)],[A.word(Bool.pick(U32,edge,1,0)),A.op(15)]),edge_cases(tail,U32.add(index,1))])

def layout_cases(layouts: List<&2,Layout>, +index: U32, +query: U32) -> List<&2,A.Instruction>:
  match layouts:
    case Nil{}: fail(5)
    case Con{Layout{+kind,+edges},tail}:
      +value = Bool.pick(U32,U32.is_eq(query,0),U32.from_nat(List.length(&2,Bool,edges)),Bool.pick(U32,kind,1,0))
      A.concat([A.guard([A.get(0),A.word(index),A.op(70)],S.choose(List<&2,A.Instruction>,U32.is_eq(query,2),u => edge_cases(edges,0),u => [A.word(value),A.op(15)])),layout_cases(tail,U32.add(index,1),query)])

def query(layouts: List<&2,Layout>, +kind: U32) -> A.Function:
  A.FunctionCode{"",Bool.pick(U32,U32.is_eq(kind,2),2,1),0,A.concat([layout_cases(layouts,0,kind),[A.word(0)]])}

# Internal pointer validation is defensive; exported memory is privileged.
def range(+pointer: U32) -> List<&2,A.Instruction>:
  A.concat([
    A.guard([A.get(pointer),A.word(65548),A.op(73)],fail(5)),
    A.guard([A.get(pointer),A.global_get(0),A.op(79)],fail(5)),
    A.guard([A.get(pointer),A.word(3),A.op(113)],fail(5))])

def validate() -> A.Function:
  A.FunctionCode{"",1,0,A.concat([range(0),
    A.guard(A.concat([prefix(0,0),[A.word(1),A.op(71)]]),fail(5)),
    A.guard(A.concat([prefix(0,4),[A.op(69)]]),fail(5)),[A.get(0)]])}

# Source function indices precede this fixed runtime family.
# alloc/share/open/release/enqueue/clean: 0..5; slots/kind/edge/valid/free/count: 6..11.
def allocate(+base: U32) -> A.Function:
  +fresh : List<&2,A.Instruction> = A.concat([
    [A.get(1),A.word(4),A.op(106),A.word(4),A.op(108),A.set(4)],
    A.guard([A.get(4),A.word(131072),A.global_get(0),A.op(107),A.op(75)],fail(3)),
    [A.global_get(0),A.word(12),A.op(106),A.set(3),
      A.global_get(0),A.get(4),A.op(106),A.global_set(0)]])
  +reuse : List<&2,A.Instruction> = A.concat([
    range(3),A.guard(A.concat([prefix(3,0),[A.op(69),A.op(69)]]),fail(5)),
    A.guard(A.concat([prefix(3,8),[A.call(U32.add(base,6)),A.get(1),A.op(71)]]),fail(5)),
    [A.get(2)],prefix(3,4),[A.save(0)]])
  A.FunctionCode{"__heap_alloc",1,4,A.concat([
    [A.word(0),A.global_set(4)],
    A.guard([A.global_get(2),A.word(2147483647),A.op(79)],fail(3)),
    [A.get(0),A.call(U32.add(base,6)),A.set(1)],
    A.guard([A.get(1),A.word(4096),A.op(79)],fail(3)),
    [A.get(1),A.word(4),A.op(108),A.tee(2),A.load(0),A.set(3),
      A.get(3),A.op(69),A.When{fresh,reuse}],
    write_prefix(3,0,[A.word(1)]),write_prefix(3,4,[A.word(1)]),write_prefix(3,8,[A.get(0)]),
    bump_global(1,1),bump_global(2,1),maximum_global(1,3),[A.get(3)]])}

def share(+base: U32) -> A.Function:
  A.FunctionCode{"__heap_share",1,1,A.concat([
    [A.word(0),A.global_set(4)],
    [A.get(0),A.call(U32.add(base,9)),A.op(26)],
    A.guard(A.concat([prefix(0,8),[A.call(U32.add(base,7)),A.op(69)]]),fail(5)),
    prefix(0,4),[A.set(1)],
    A.guard([A.get(1),A.global_get(8),A.op(79)],fail(3)),
    retain_count(0,1),[A.get(0)]])}

def free(+base: U32) -> A.Function:
  A.FunctionCode{"",1,1,A.concat([
    range(0),A.guard(A.concat([prefix(0,0),[A.op(69)]]),fail(5)),
    A.guard(A.concat([prefix(0,0),[A.word(2),A.op(75)]]),fail(5)),
    A.guard([A.global_get(1),A.op(69)],fail(5)),
    prefix(0,8),[A.call(U32.add(base,6)),A.word(4),A.op(108),A.set(1)],
    recycle(0,1),[A.word(0)]])}

# Count repeated child edges before publishing any shared-open acquire.
def occurrences(+base: U32) -> A.Function:
  +scan : List<&2,A.Instruction> = A.concat([
    [A.get(3),A.get(2),A.op(79),A.branch_if(1)],
    prefix(0,8),[A.get(3),A.call(U32.add(base,8)),A.When{
      A.concat([slot_address(0,3),[A.load(4),A.get(1),A.op(70),A.When{[A.get(4),A.word(1),A.op(106),A.set(4)],Nil{}}]]),Nil{}}],
    [A.get(3),A.word(1),A.op(106),A.set(3),A.branch(0)]])
  A.FunctionCode{"",2,3,A.concat([prefix(0,8),[A.call(U32.add(base,6)),A.set(2)],loop(scan),[A.get(4)]])}

def open(+base: U32) -> A.Function:
  +preflight : List<&2,A.Instruction> = A.concat([
    [A.get(2),A.get(1),A.op(79),A.branch_if(1)],
    prefix(0,8),[A.get(2),A.call(U32.add(base,8)),A.When{
      A.concat([slot_address(0,2),[A.load(4),A.tee(3),A.call(U32.add(base,9)),A.op(26)],
        A.guard(A.concat([prefix(3,8),[A.call(U32.add(base,7)),A.op(69)]]),fail(5)),
        [A.get(0),A.get(3),A.call(U32.add(base,11)),A.set(4)],
        A.guard([A.get(4),A.global_get(8),A.op(75)],fail(3)),
        A.guard(A.concat([prefix(3,4),[A.global_get(8),A.get(4),A.op(107),A.op(75)]]),fail(3))]),Nil{}}],
    [A.get(2),A.word(1),A.op(106),A.set(2),A.branch(0)]])
  +acquire : List<&2,A.Instruction> = A.concat([
    [A.get(2),A.get(1),A.op(79),A.branch_if(1)],
    prefix(0,8),[A.get(2),A.call(U32.add(base,8)),A.When{
      A.concat([slot_address(0,2),[A.load(4),A.call(U32.add(base,1)),A.op(26)]]),Nil{}}],
    [A.get(2),A.word(1),A.op(106),A.set(2),A.branch(0)]])
  A.FunctionCode{"__heap_open",1,4,A.concat([
    [A.word(0),A.global_set(4)],
    [A.get(0),A.call(U32.add(base,9)),A.op(26)],
    A.guard(A.concat([prefix(0,4),[A.word(1),A.op(70)]]),unique_open(base)),
    A.guard(A.concat([prefix(0,8),[A.call(U32.add(base,7)),A.op(69)]]),fail(5)),
    prefix(0,8),[A.call(U32.add(base,6)),A.set(1)],loop(preflight),
    [A.word(0),A.set(2)],loop(acquire),write_prefix(0,4,A.concat([prefix(0,4),[A.word(1),A.op(107)]])),[A.word(0)]])}

def enqueue(+base: U32) -> A.Function:
  A.FunctionCode{"__heap_enqueue",1,1,A.concat([
    [A.word(0),A.global_set(4),A.get(0),A.call(U32.add(base,9)),A.op(26)],
    stack_room(),
    [A.global_get(5),A.word(8),A.op(108),A.word(16384),A.op(106),A.set(1)],
    A.write_field(1,0,[A.get(0)]),A.write_field(1,4,[A.word(0)]),
    bump_global(5,1),maximum_global(5,6),[A.word(0)]])}

# cursor=0 owns one release. cursor=k+1 owns the unvisited fields from slot k.
# A full stack leaves that cursor untouched: raising the bound resumes it.
def clean(+base: U32) -> A.Function:
  +begin : List<&2,A.Instruction> = A.concat([
    [A.get(2),A.call(U32.add(base,9)),A.op(26)],prefix(2,4),[A.word(1),A.op(75),A.When{
      A.concat([
        A.guard(A.concat([prefix(2,8),[A.call(U32.add(base,7)),A.op(69)]]),fail(5)),
        write_prefix(2,4,A.concat([prefix(2,4),[A.word(1),A.op(107)]])),
        [A.global_get(5),A.word(1),A.op(107),A.global_set(5)]]),
      begin_drop(2,1)}]])
  +descend : List<&2,A.Instruction> = A.concat([
    stack_room(),
    slot_address(2,5),[A.load(4),A.call(U32.add(base,4)),A.op(26)],
    A.write_field(1,4,[A.get(3),A.word(1),A.op(106)])])
  +scan : List<&2,A.Instruction> = A.concat([
    A.guard(A.concat([prefix(2,0),[A.word(2),A.op(71)]]),fail(5)),
    prefix(2,8),[A.call(U32.add(base,6)),A.set(4),A.get(3),A.word(1),A.op(107),A.set(5),
      A.get(5),A.get(4),A.op(79),A.When{
        [A.get(2),A.call(U32.add(base,10)),A.op(26),A.global_get(5),A.word(1),A.op(107),A.global_set(5)],
        A.concat([prefix(2,8),[A.get(5),A.call(U32.add(base,8)),A.When{descend,A.write_field(1,4,[A.get(3),A.word(1),A.op(106)])}]])}]])
  +step : List<&2,A.Instruction> = A.concat([
    A.guard([A.global_get(5),A.op(69)],outcome(0)),
    A.guard([A.get(0),A.op(69)],outcome(3)),
    [A.global_get(5),A.word(1),A.op(107),A.word(8),A.op(108),A.word(16384),A.op(106),A.set(1)],
    A.field(1,0),[A.set(2)],A.field(1,4),[A.set(3),A.get(3),A.op(69),A.When{begin,scan}],
    [A.get(0),A.word(1),A.op(107),A.set(0),A.branch(0)]])
  A.FunctionCode{"__heap_clean",1,5,A.concat([[A.word(0),A.global_set(4)],loop(step),[A.word(0)]])}

def release(+base: U32) -> A.Function:
  A.FunctionCode{"__heap_release",1,0,A.concat([
    [A.get(0),A.call(U32.add(base,4)),A.When{[A.op(0)],Nil{}},
      A.word(2147483647),A.call(U32.add(base,5)),A.When{[A.op(0)],Nil{}},A.word(0)]])}

def counter(name: String, index: U32) -> A.Function:
  A.FunctionCode{name,0,0,[A.global_get(index)]}

def limit(name: String, +index: U32, +ceiling: U32, minimum: U32) -> A.Function:
  A.FunctionCode{name,1,1,A.concat([
    A.guard([A.get(0),A.word(ceiling),A.op(75)],fail(5)),
    A.guard([A.get(0),A.word(minimum),A.op(73)],fail(5)),
    [A.global_get(index),A.set(1),A.get(0),A.global_set(index),A.word(0),A.global_set(4),A.get(1)]])}

def functions(+layouts: List<&2,Layout>, +base: U32) -> List<&2,A.Function>:
  [allocate(base),share(base),open(base),release(base),enqueue(base),clean(base),
    query(layouts,0),query(layouts,1),query(layouts,2),validate(),free(base),occurrences(base),
    counter("__heap_live",1),counter("__heap_allocations",2),counter("__heap_peak",3),
    counter("__heap_pending",5),counter("__heap_status",4),counter("__heap_peak_pending",6),
    limit("__heap_stack_limit",7,4096,0),limit("__heap_rc_limit",8,2147483647,1),counter("__heap_bump",0)]

def global(+cap: U32, value: U32) -> Result<S.Error,B.Builder>:
  W.concat(cap,[W.bytes(cap,[127,1,65]),W.positive_signed(cap,value),W.bytes(cap,[11])])

def sections(+cap: U32) -> Result<S.Error,B.Builder>:
  S.bind(B.Builder,B.Builder,W.bytes(cap,[1,1,2,2]),memory =>
    S.bind(B.Builder,B.Builder,W.concat(cap,[W.bytes(cap,[9]),global(cap,65536),global(cap,0),global(cap,0),global(cap,0),global(cap,0),global(cap,0),global(cap,0),global(cap,4096),global(cap,2147483647)]),globals =>
      W.concat(cap,[W.section(cap,5,memory),W.section(cap,6,globals)])))

def memory_export(+cap: U32) -> Result<S.Error,B.Builder>:
  W.concat(cap,[W.name(cap,"__heap_memory"),W.bytes(cap,[2,0])])

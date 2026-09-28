import Base
import ./model/word.bend as W
import ./model/decode.bend as D
import ./model/encode.bend as E
import ./model/memory.bend as H
import ./model/machine.bend as M
import ./model/audit.bend as A

# Laws of the knot-vm-1 model: bounded, computed equations on committed golden
# images (vm/check-model.py requires each fixture to equal its .kimg words) and
# symbolic equations over whole machine states.

def value_on() -> List<&2,U32>:
  [1196247371,1,75,0,0,32,38,49,56,57,62,0,4294967295,4294967295,4294967295,4294967295,4294967295,
   4294967295,4294967295,4294967295,4294967295,4294967295,4294967295,4294967295,967372322,
   1597628945,3931068771,212603004,2186566430,3374278737,2120669052,453228302,1,5,0,0,0,2,2,5,0,0,1,
   0,5,0,1,2,0,1,6,3,0,0,0,58,0,1,4,3,0,1,4,3,4,1734437958,3,3,6710863,3,2,28239,3,4,1852399981]

def closure_captures() -> List<&2,U32>:
  [1196247371,1,162,0,1,32,48,66,81,82,143,0,4294967295,4294967295,4294967295,4294967295,4294967295,
   4294967295,4294967295,4294967295,4294967295,4294967295,4294967295,4294967295,967372322,
   1597628945,3931068771,212603004,2186566430,3374278737,2120669052,453228302,3,5,0,0,0,2,5,0,1,2,1,
   5,1,4294967295,0,1,3,5,0,0,2,0,5,0,1,3,0,7,1,0,1,2,0,0,2,8,4,1,2,3,122,0,0,6,5,1,0,0,136,0,11,4,
   5,0,1,4,5,0,0,7,4,1,0,2,83,87,10,10,2,0,1,3,2,0,1,91,4,5,2,2,4,3,0,0,6,11,1,108,1,112,6,7,1,2,98,
   116,4,3,0,0,4,3,0,1,7,6,1,0,2,128,132,6,3,4,1734437958,3,4,1919508816,3,3,6710863,3,2,28239,3,4,
   1885435763,3,4,1852399981]

def recursion_map() -> List<&2,U32>:
  [1196247371,1,238,0,2,32,43,66,87,88,208,0,4294967295,4294967295,4294967295,4294967295,4294967295,
   4294967295,4294967295,4294967295,4294967295,4294967295,4294967295,4294967295,967372322,
   1597628945,3931068771,212603004,2186566430,3374278737,2120669052,453228302,2,5,0,0,0,2,5,0,1,2,2,
   4,5,0,0,2,0,5,0,1,3,0,5,1,0,4,0,7,1,1,5,2,0,1,3,7,6,0,1,1,111,0,7,7,1,1,3,166,1,6,8,1,0,0,202,0,
   20,4,3,0,1,7,9,0,0,1,0,89,4,3,0,0,7,9,0,1,1,0,100,10,8,0,0,0,0,2,93,104,4294967295,4,3,1,0,7,9,1,
   0,1,0,121,4,5,0,1,6,6,0,0,1,132,4,5,1,2,6,6,1,1,1,142,7,4,1,1,2,136,146,7,9,1,1,1,2,152,10,8,1,0,
   1,0,2,125,159,4294967295,4,3,0,1,4,3,0,0,4,3,1,0,7,4,1,1,2,180,184,7,4,1,1,2,176,188,6,6,1,1,1,
   195,9,3,4,1734437958,4,5,1734437958,115,3,3,6710863,3,2,28239,3,4,1886352467,3,4,1752397136,3,4,
   1885957222,4,8,1885957222,1819042143,3,4,1852399981]

def string_append_mortal() -> List<&2,U32>:
  [1196247371,1,247,0,3,32,53,82,112,126,199,0,4294967295,1,2,3,0,4294967295,4294967295,4294967295,
   4294967295,4294967295,4294967295,4294967295,967372322,1597628945,3931068771,212603004,2186566430,
   3374278737,2120669052,453228302,4,5,0,0,0,2,5,3,1,0,0,5,0,2,2,1,5,0,3,3,2,5,5,0,0,4,0,5,0,1,5,0,
   6,2,0,6,1,1,5,3,0,7,0,7,3,1,8,2,2,3,4,8,9,3,2,2,135,3,3,8,10,0,2,2,150,3,3,7,11,3,1,1,161,1,6,12,
   0,0,0,192,3,4,3,1,97,4,0,1,7,5,3,2,97,55,14,4,5,3,0,4,5,3,1,7,1,3,35,2,127,131,4,5,3,0,4,5,3,1,7,
   1,0,34,2,142,146,4,5,1,0,6,1,3,32,1,157,4,0,3,0,4,0,1,1,6,6,3,2,1,171,7,6,3,0,2,167,175,4,0,3,2,
   7,6,0,1,2,181,188,13,3,4,1819242306,3,3,3289941,3,4,1918986307,4,6,1769108563,26478,4,5,
   1936482630,101,3,4,1702195796,3,3,7497795,3,4,1818840659,3,4,1852785491,6,13,1769108563,
   1630431086,1852141680,100,5,9,1769108563,1697539950,113,4,8,775041877,2003789939,3,4,1852399981]

def foreign_print() -> List<&2,U32>:
  [1196247371,1,191,1,1,32,73,110,124,130,151,0,4294967295,1,2,3,4294967295,4294967295,0,4294967295,
   4294967295,4294967295,4,4294967295,967372322,1597628945,3931068771,212603004,2186566430,
   3374278737,2120669052,453228302,8,5,0,0,0,1,5,3,1,0,0,5,0,2,1,1,5,0,3,2,2,5,0,4,4,2,5,1,
   4294967295,0,4,5,1,4294967295,5,4,5,2,4294967295,4294967295,6,6,5,0,0,0,0,6,2,0,5,1,1,5,3,0,6,0,
   7,3,1,7,2,2,3,6,4,0,8,1,4294967295,7,4,1,9,2,1,3,2,7,10,7,1,1,135,3,6,11,7,0,0,145,1,5,3,2,118,
   109,4,4,5,3,0,6,12,7,1,1,131,4,0,3,0,6,6,7,0,1,141,12,3,4,1953066581,3,3,3289941,3,4,1918986307,
   4,6,1769108563,26478,4,5,1328435017,80,3,3,7497795,3,4,1818840659,3,4,1852785491,3,4,1953066309,
   3,4,1953259848,4,8,1882083145,1953393010,3,4,1852399981]

def none12() -> List<&2,U32>:
  +o = W.none()
  [o,o,o,o,o,o,o,o,o,o,o,o]

# value-on's plan, written by hand: Flag{Off,On} and `main` returning On.
def flag_plan() -> W.Plan:
  W.Plan{0,[W.Algebraic{M.text("Flag"),[W.Constructor{M.text("Off"),[]},W.Constructor{M.text("On"),[]}]}],
    [W.Function{M.text("main"),[],0,0,W.Value{0,1}}],none12()}

def reencoded(result: Result<String,W.Plan>) -> List<&2,U32>:
  match result:
    case Fail{reason}: Nil{}
    case Done{plan}: E.encode(plan)

def canonical(images: List<&2,List<&2,U32>>) -> Bool:
  match images:
    case Nil{}: True{}
    case Con{+w,rest}: Bool.and(W.same(reencoded(D.decode(w)),w),canonical(rest))

def fixtures() -> List<&2,List<&2,U32>>:
  [value_on(),closure_captures(),recursion_map(),string_append_mortal(),foreign_print()]

# One run of an image's entry, audited before every transition: its outcome,
# whether every count balanced, the mortal cells left live and the lines printed.
type Summary is Data:
  Summary{outcome: M.Outcome, balanced: Bool, live: U32, printed: List<&2,List<&2,U32>>}

def printed(run: A.Run) -> List<&2,List<&2,U32>>:
  match run:
    case A.Ran{code,M.Machine{control,stack,heap,meter,out},ok}: List.reverse(&2,List<&2,U32>,out)
    case _: Nil{}

def summary(+run: A.Run) -> Summary:
  Summary{A.outcome_of(run),A.balanced_run(run),A.leak_of(run),printed(run)}

def ran(+words: List<&2,U32>) -> Summary:
  summary(A.run_words(words,100000n,1000000))

def described(+result: U32, +tag: U32, tree: String) -> Summary:
  Summary{M.Described{result,tag,M.text(tree)},True{},0,Nil{}}

# ---------------------------------------------------------------- codec

law words_round_trip:
  {W.pack(W.unpack([0,1,255,256,2147483648,4294967295,1196247371])) == [0,1,255,256,2147483648,4294967295,1196247371] : List<&2,U32>}

law plan_encodes_image:
  {E.encode(flag_plan()) == value_on() : List<&2,U32>}

law image_decodes_plan:
  {D.decode(value_on()) == Done{flag_plan()} : Result<String,W.Plan>}

law images_canonical:
  {canonical(fixtures()) == True{} : Bool}

# ---------------------------------------------------------------- validation

law magic_refused:
  {E.admit(H.replaced(value_on(),0,0)) == Fail{W.Refused{"image","magic"}} : Result<W.Stop,W.Plan>}

law opcode_refused:
  {E.admit(H.replaced(value_on(),59,13)) == Fail{W.Refused{"image","node record"}} : Result<W.Stop,W.Plan>}

law tag_refused:
  {E.admit(H.replaced(value_on(),61,2)) == Fail{W.Refused{"image","validator: main: value is not a nullary constructor"}} : Result<W.Stop,W.Plan>}

law layout_refused:
  {E.admit(H.replaced(value_on(),4,W.none())) == Fail{W.Refused{"image","noncanonical"}} : Result<W.Stop,W.Plan>}

# Every single-word mutation of value-on's function, constant and node
# sections (words 49-61) is refused or runs soundly.
law mutations_sound:
  {A.all_sound(A.mutations(13n,value_on(),49),100000n,1000000) == True{} : Bool}

# ---------------------------------------------------------------- the machine

law entry_needs_fuel:
  for code: H.Code
  for f: U32
  for ops: List<&2,U32>
  for stack: H.Stack
  for heap: H.Heap
  for calls: U32
  for quantum: U32
  for out: List<&2,List<&2,U32>>
  {M.entered(code,M.Callee{f},ops,stack,heap,M.Meter{0,calls,quantum},out) == Fail{W.Exhausted{1,"fuel"}} : Result<W.Stop,M.Machine>}

law finished_is_final:
  for code: H.Code
  for outcome: M.Outcome
  for stack: H.Stack
  for heap: H.Heap
  for meter: M.Meter
  for out: List<&2,List<&2,U32>>
  {M.step(code,M.Machine{M.Finished{outcome},stack,heap,meter,out}) == Done{M.Machine{M.Finished{outcome},stack,heap,meter,out}} : Result<W.Stop,M.Machine>}

law tail_skips_scopes:
  {M.tail([H.Scope{2},H.Scope{1},H.Call{0}]) == True{} : Bool}

law operands_are_not_tail:
  {M.tail([H.Scope{1},H.Gather{0,2,Nil{}},H.Call{0}]) == False{} : Bool}

law nat_sum_bound:
  for heap: H.Heap
  {H.nat_sum(heap,4294967295,1) == Fail{W.Exhausted{2,"NatRange"}} : Result<W.Stop,H.Cell>}

law nat_product_bound:
  for heap: H.Heap
  {H.nat_product(heap,65536,65536) == Fail{W.Exhausted{2,"NatRange"}} : Result<W.Stop,H.Cell>}

law division_by_zero:
  for code: H.Code
  for heap: H.Heap
  for a: U32
  for b: U32
  for x: U32
  {H.computed(3n,code,heap,a,b,x,0) == Done{H.Cell{heap,1}} : Result<W.Stop,H.Cell>}

law remainder_by_zero:
  for code: H.Code
  for heap: H.Heap
  for a: U32
  for b: U32
  for x: U32
  {H.computed(4n,code,heap,a,b,x,0) == H.word_of(heap,x) : Result<W.Stop,H.Cell>}

law wide_shifts_vanish:
  for a: U32
  {H.shifted(True{},a,32) == 0 : U32}

# ---------------------------------------------------------------- runs: answer, RC audit, zero leak

law value_on_runs:
  {ran(value_on()) == described(0,1,"On{}") : Summary}

law closure_captures_runs:
  {ran(closure_captures()) == described(1,0,"Pair{On{},Off{}}") : Summary}

law recursion_map_runs:
  {ran(recursion_map()) == described(1,1,"Push{Off{},Push{On{},Stop{}}}") : Summary}

law string_append_mortal_runs:
  {ran(string_append_mortal()) == described(0,1,"True{}") : Summary}

law foreign_print_runs:
  {ran(foreign_print()) == Summary{M.Emitted{},True{},0,[M.text("vm")]} : Summary}

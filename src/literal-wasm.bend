import Base
import ./syntax.bend as S
import ./core.bend as C
import ./literal-types.bend as L
import ./machine-code.bend as A
import ./machine-lower.bend as M
import ./machine-runtime.bend as R
import ./machine-vm.bend as V
import ./primitive-wasm.bend as P
import ./wasm-bytes.bend as W
import 0xc409b77d3230ca33374caf6b0993f0cb/bytes.bend as B

def primitive(kind: Maybe<&2,U32>) -> Bool:
  match kind:
    case None{}: False{}
    case Some{value}: True{}

def enabled(types: List<&2,C.Datatype>) -> Bool:
  match types:
    case Nil{}: False{}
    case Con{head,tail}: Bool.or(primitive(L.kind(head)),enabled(tail))

def selected(book: C.Book) -> Bool:
  match book:
    case C.Book{types,functions}: enabled(types)

def repeat(n: Nat, +value: U32) -> List<&2,U32>:
  match n:
    case 0n: Nil{}
    case 1n+k: Con{value,repeat(k,value)}

def type_bytes(+n: U32) -> List<&2,U32>:
  A.seq([[96],A.unsigned(n),repeat(U32.to_nat(n),127),[1,127]])

def types(entries: List<&2,M.Entry>) -> List<&2,U32>:
  match entries:
    case Nil{}: Nil{}
    case Con{M.Entry{signature,entry,slots},tail}:
      A.seq([type_bytes(M.live(M.parameters(signature))),types(tail)])

def indices(entries: List<&2,M.Entry>, +index: U32) -> List<&2,U32>:
  match entries:
    case Nil{}: Nil{}
    case Con{head,tail}: A.seq([A.unsigned(index),indices(tail,U32.add(index,1))])

def exports(entries: List<&2,M.Entry>, +index: U32) -> List<&2,U32>:
  match entries:
    case Nil{}: Nil{}
    case Con{M.Entry{C.Signature{token,params,result},entry,slots},tail}:
      A.seq([A.size(W.chars(S.text(token))),[0],A.unsigned(index),exports(tail,U32.add(index,1))])

def arguments(params: List<&2,C.Parameter>, +level: U32, +index: U32) -> List<&2,U32>:
  match params:
    case Nil{}: Nil{}
    case Con{C.Parameter{token,+q,typ},+tail}:
      A.seq([A.i32(U32.add(5242880,U32.mul(level,4))),
        S.choose(List<&2,U32>,U32.is_eq(q,0),u => A.i32(0),u => A.get(index)),A.store(0),
        arguments(tail,U32.add(level,1),U32.add(index,Bool.pick(U32,U32.is_eq(q,0),0,1)))])

def wrappers(entries: List<&2,M.Entry>) -> List<&2,U32>:
  match entries:
    case Nil{}: Nil{}
    case Con{M.Entry{signature,entry,slots},tail}:
      A.seq([A.function(0,A.seq([arguments(M.parameters(signature),0,0),A.invoke(9,A.i32(entry),A.i32(slots))])),wrappers(tail)])

def metadata(entries: List<&2,M.Entry>) -> List<&2,U32>:
  match entries:
    case Nil{}: Nil{}
    case Con{M.Entry{signature,entry,slots},tail}:
      A.seq([A.word(entry),A.word(slots),A.word(U32.from_nat(List.length(&2,C.Parameter,M.parameters(signature)))),metadata(tail)])

def instruction_bytes(code: List<&2,M.Instruction>, reversed: List<&2,U32>) -> List<&2,U32>:
  match code:
    case Nil{}: List.reverse(&2,U32,reversed)
    case Con{M.Instruction{op,a,b,c,next},tail}:
      instruction_bytes(tail,List.append(&2,U32,List.reverse(&2,U32,A.seq([A.word(op),A.word(a),A.word(b),A.word(c),A.word(next)])),reversed))

def instructions(code: List<&2,M.Instruction>) -> List<&2,U32>:
  instruction_bytes(code,Nil{})

def runtime(code_base: U32) -> List<&2,U32>:
  A.seq([R.allocator(),R.natural(),R.count(),R.reverse(),R.append(),R.equal(),R.length(),R.show(),P.function(),V.function(code_base)])

# B.finish copies each chunk with Base's List.append, which is not tail
# recursive, so a chunk's length is a stack depth on the Bun lane. A section
# body therefore enters its builder as runs of at most 4096 bytes.
def appended(runs: List<&2,List<&2,U32>>, builder: B.Builder) -> Result<S.Error,B.Builder>:
  match runs:
    case Nil{}: Done{builder}
    case Con{run,tail}: S.bind(B.Builder,B.Builder,W.checked(B.append(builder,run)),next => appended(tail,next))

def section(+cap: U32, id: U32, data: List<&2,U32>) -> Result<S.Error,B.Builder>:
  S.bind(B.Builder,B.Builder,appended(A.runs(4096,data),B.empty(cap)),body => W.section(cap,id,body))

def binary(+entries: List<&2,M.Entry>, code: List<&2,M.Instruction>, +cap: U32) -> Result<S.Error,List<&2,U32>>:
  +count = U32.from_nat(List.length(&2,M.Entry,entries))
  +data = A.seq([repeat(16n,0),metadata(entries),instructions(List.reverse(&2,M.Instruction,code))])
  S.choose(Result<S.Error,List<&2,U32>>,U32.is_le(A.length(data),1048576),u =>
    S.bind(B.Builder,List<&2,U32>,W.concat(cap,[
      W.bytes(cap,[0,97,115,109,1,0,0,0]),
      section(cap,1,A.seq([A.unsigned(U32.add(count,2)),type_bytes(2),type_bytes(3),types(entries)])),
      section(cap,3,A.seq([A.unsigned(U32.add(count,10)),[0,0,0,0,0,0,0,0,1,0],indices(entries,2)])),
      section(cap,5,A.seq([[1,1],A.unsigned(1024),A.unsigned(1024)])),
      section(cap,6,A.seq([[1,127,1],A.i32(23068672),[11]])),
      section(cap,7,A.seq([A.unsigned(count),exports(entries,10)])),
      section(cap,10,A.seq([A.unsigned(U32.add(count,10)),runtime(U32.add(16,U32.mul(count,12))),wrappers(entries)])),
      section(cap,11,A.seq([[1,0,65,0,11],A.size(data)]))]),builder => Done{B.finish(builder)}),u =>
        Fail{S.Exhausted{"emit",S.At{0,0,0,0}}})

def module(value: M.Module, cap: U32) -> Result<S.Error,List<&2,U32>>:
  match value:
    case M.Module{entries,M.Assembly{entry,count,slots,code}}: binary(entries,code,cap)

def emit(book: C.Book, depth: Nat, +cap: U32) -> Result<S.Error,List<&2,U32>>:
  S.bind(M.Module,List<&2,U32>,M.book(book,depth),value => module(value,cap))

import Base
import 0xc409b77d3230ca33374caf6b0993f0cb/bytes.bend as B
import ./syntax.bend as S
import ./wasm-bytes.bend as W

type Instruction is Data:
  Byte{opcode: U32}
  Index{opcode: U32, value: U32}
  Word{value: U32}
  Memory{opcode: U32, offset: U32}
  Block{opcode: U32, body: List<&2,Instruction>}
  When{yes: List<&2,Instruction>, no: List<&2,Instruction>}
type Chunk is Data:
  InstructionOne{value: Instruction}
  InstructionList{values: List<&2,Instruction>}
type Function is Data:
  FunctionCode{name: String, arity: U32, locals: U32, body: List<&2,Instruction>}

def encode(fuel: Nat, chunk: Chunk, +cap: U32) -> Result<S.Error,B.Builder>:
  match fuel chunk:
    case 0n _: Fail{S.Exhausted{"emit",S.At{0,0,0,0}}}
    case 1n+n InstructionOne{Byte{opcode}}: W.bytes(cap,[opcode])
    case 1n+n InstructionOne{Index{opcode,value}}: W.concat(cap,[W.bytes(cap,[opcode]),W.unsigned(cap,value)])
    case 1n+n InstructionOne{Word{value}}: W.concat(cap,[W.bytes(cap,[65]),W.positive_signed(cap,value)])
    case 1n+n InstructionOne{Memory{opcode,offset}}: W.concat(cap,[W.bytes(cap,[opcode,2]),W.unsigned(cap,offset)])
    case 1n+n InstructionOne{Block{opcode,body}}:
      W.concat(cap,[W.bytes(cap,[opcode,64]),encode(n,InstructionList{body},cap),W.bytes(cap,[11])])
    case 1n+ +n InstructionOne{When{yes,no}}:
      W.concat(cap,[W.bytes(cap,[4,64]),encode(n,InstructionList{yes},cap),W.bytes(cap,[5]),encode(n,InstructionList{no},cap),W.bytes(cap,[11])])
    case 1n+n InstructionList{Nil{}}: W.bytes(cap,Nil{})
    case 1n+ +n InstructionList{Con{head,tail}}:
      W.concat(cap,[encode(n,InstructionOne{head},cap),encode(n,InstructionList{tail},cap)])

def concat(parts: List<&2,List<&2,Instruction>>) -> List<&2,Instruction>:
  match parts:
    case Nil{}: Nil{}
    case Con{head,tail}: List.append(&2,Instruction,head,concat(tail))

def get(index: U32) -> Instruction: Index{32,index}
def set(index: U32) -> Instruction: Index{33,index}
def tee(index: U32) -> Instruction: Index{34,index}
def call(index: U32) -> Instruction: Index{16,index}
def op(opcode: U32) -> Instruction: Byte{opcode}
def word(value: U32) -> Instruction: Word{value}
def load(offset: U32) -> Instruction: Memory{40,offset}
def save(offset: U32) -> Instruction: Memory{54,offset}
def global_get(index: U32) -> Instruction: Index{35,index}
def global_set(index: U32) -> Instruction: Index{36,index}
def branch(index: U32) -> Instruction: Index{12,index}
def branch_if(index: U32) -> Instruction: Index{13,index}

def guard(condition: List<&2,Instruction>, rejected: List<&2,Instruction>) -> List<&2,Instruction>:
  concat([condition,[When{rejected,Nil{}}]])

def field(address: U32, offset: U32) -> List<&2,Instruction>: [get(address),load(offset)]
def write_field(address: U32, offset: U32, value: List<&2,Instruction>) -> List<&2,Instruction>:
  concat([[get(address)],value,[save(offset)]])

def signature(+arity: U32, +cap: U32) -> Result<S.Error,B.Builder>:
  W.concat(cap,[W.bytes(cap,[96]),W.unsigned(cap,arity),W.bytes(cap,List.replicate(U32,U32.to_nat(arity),127)),W.bytes(cap,[1,127])])

def locals(+count: U32, +cap: U32) -> Result<S.Error,B.Builder>:
  S.choose(Result<S.Error,B.Builder>,U32.is_eq(count,0),u => W.bytes(cap,[0]),u =>
    W.concat(cap,[W.bytes(cap,[1]),W.unsigned(cap,count),W.bytes(cap,[127])]))

def body(function: Function, +cap: U32) -> Result<S.Error,B.Builder>:
  match function:
    case FunctionCode{name,arity,count,instructions}:
      S.bind(B.Builder,B.Builder,W.concat(cap,[locals(count,cap),encode(65536n,InstructionList{instructions},cap),W.bytes(cap,[11])]),bytes => W.sized(cap,bytes))

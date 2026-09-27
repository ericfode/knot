import Base
import 0xc409b77d3230ca33374caf6b0993f0cb/bytes.bend as B
import ../../src/syntax.bend as S
import ../../src/wasm-bytes.bend as W

type Instruction is Data:
  CodeByte{opcode: U32}
  CodeIndex{opcode: U32, value: U32}
  CodeWord{value: U32}
  CodeNegativeOne{}
  CodeMemory{opcode: U32, offset: U32}
  CodeBlock{opcode: U32, body: List<&2,Instruction>}
  CodeIf{yes: List<&2,Instruction>, no: List<&2,Instruction>}
type Chunk is Data:
  OneInstruction{value: Instruction}
  InstructionList{values: List<&2,Instruction>}
type Function is Data:
  FunctionCode{name: String, arity: U32, locals: U32, body: List<&2,Instruction>}

def encode(fuel: Nat, chunk: Chunk, +cap: U32) -> Result<S.Error,B.Builder>:
  match fuel chunk:
    case 0n _: Fail{S.Exhausted{"emit",S.At{0,0,0,0}}}
    case 1n+n OneInstruction{CodeByte{opcode}}: W.bytes(cap,[opcode])
    case 1n+n OneInstruction{CodeIndex{opcode,value}}: W.concat(cap,[W.bytes(cap,[opcode]),W.unsigned(cap,value)])
    case 1n+n OneInstruction{CodeWord{value}}: W.concat(cap,[W.bytes(cap,[65]),W.positive_signed(cap,value)])
    case 1n+n OneInstruction{CodeNegativeOne{}}: W.bytes(cap,[65,127])
    case 1n+n OneInstruction{CodeMemory{opcode,offset}}: W.concat(cap,[W.bytes(cap,[opcode,2]),W.unsigned(cap,offset)])
    case 1n+n OneInstruction{CodeBlock{opcode,body}}:
      W.concat(cap,[W.bytes(cap,[opcode,64]),encode(n,InstructionList{body},cap),W.bytes(cap,[11])])
    case 1n+ +n OneInstruction{CodeIf{yes,no}}:
      W.concat(cap,[W.bytes(cap,[4,64]),encode(n,InstructionList{yes},cap),W.bytes(cap,[5]),encode(n,InstructionList{no},cap),W.bytes(cap,[11])])
    case 1n+n InstructionList{Nil{}}: W.bytes(cap,Nil{})
    case 1n+ +n InstructionList{Con{head,tail}}:
      W.concat(cap,[encode(n,OneInstruction{head},cap),encode(n,InstructionList{tail},cap)])

def concat(parts: List<&2,List<&2,Instruction>>) -> List<&2,Instruction>:
  match parts:
    case Nil{}: Nil{}
    case Con{head,tail}: List.append(&2,Instruction,head,concat(tail))

def get(index: U32) -> Instruction: CodeIndex{32,index}
def set(index: U32) -> Instruction: CodeIndex{33,index}
def call(index: U32) -> Instruction: CodeIndex{16,index}
def op(opcode: U32) -> Instruction: CodeByte{opcode}
def word(value: U32) -> Instruction: CodeWord{value}
def none() -> Instruction: CodeNegativeOne{}
def load(offset: U32) -> Instruction: CodeMemory{40,offset}
def save(offset: U32) -> Instruction: CodeMemory{54,offset}
def global_get() -> Instruction: CodeIndex{35,0}
def global_set() -> Instruction: CodeIndex{36,0}
def branch(index: U32) -> Instruction: CodeIndex{12,index}
def branch_if(index: U32) -> Instruction: CodeIndex{13,index}

def header(offset: U32) -> List<&2,Instruction>: [word(0),load(offset)]
def write_header(offset: U32, value: List<&2,Instruction>) -> List<&2,Instruction>:
  concat([[word(0)],value,[save(offset)]])
def field(address: U32, offset: U32) -> List<&2,Instruction>: [get(address),load(offset)]
def write_field(address: U32, offset: U32, value: List<&2,Instruction>) -> List<&2,Instruction>:
  concat([[get(address)],value,[save(offset)]])
def address(index: U32, target: U32) -> List<&2,Instruction>:
  [get(index),word(16),op(108),word(32),op(106),set(target)]

# finish(status,slot,generation,value) is function zero.
def result(status: U32, slot: List<&2,Instruction>, generation: List<&2,Instruction>, value: List<&2,Instruction>) -> List<&2,Instruction>:
  concat([[word(status)],slot,generation,value,[call(0)]])
def failure(status: U32, value: List<&2,Instruction>) -> List<&2,Instruction>:
  concat([result(status,[none()],[none()],value),[op(15)]])
def guard(condition: List<&2,Instruction>, rejected: List<&2,Instruction>) -> List<&2,Instruction>:
  concat([condition,[CodeIf{rejected,Nil{}}]])
def initialized() -> List<&2,Instruction>:
  guard([global_get(),op(69)],[word(9),op(15)])

def signature(+arity: U32, +cap: U32) -> Result<S.Error,B.Builder>:
  W.concat(cap,[W.bytes(cap,[96]),W.unsigned(cap,arity),W.bytes(cap,List.replicate(U32,U32.to_nat(arity),127)),W.bytes(cap,[1,127])])

import Base
import ./assembly.bend as A

# Byte offsets: header 0..28; cell state/gen/value/next at 0/4/8/12.
# Function indices: finish 0, init 1, put 2, alloc 3, take 4, release 5.
def finish() -> A.Function:
  A.FunctionCode{"",4,0,A.concat([
    A.write_header(16,[A.get(1)]),A.write_header(20,[A.get(2)]),
    A.write_header(24,[A.get(3)]),[A.get(0)]])}

def init() -> A.Function:
  +loop : List<&2,A.Instruction> = A.concat([
    [A.get(3),A.get(1),A.op(79),A.branch_if(1)], A.address(3,4),
    A.write_field(4,0,[A.word(0)]), A.write_field(4,4,[A.word(0)]), A.write_field(4,8,[A.word(0)]),
    [A.get(3),A.word(1),A.op(106),A.get(1),A.op(70),
      A.CodeIf{A.write_field(4,12,[A.none()]),A.write_field(4,12,[A.get(3),A.word(1),A.op(106)])}],
    [A.get(3),A.word(1),A.op(106),A.set(3),A.branch(0)]])
  A.FunctionCode{"init",3,2,A.concat([
    A.guard([A.global_get()],[A.word(10),A.op(15)]),
    A.guard([A.get(1),A.word(4096),A.op(75)],[A.word(1),A.op(15)]),
    A.write_header(0,[A.get(0)]), A.write_header(4,[A.get(1)]), A.write_header(8,[A.get(2)]),
    [A.get(1),A.op(69),A.CodeIf{A.write_header(12,[A.none()]),A.write_header(12,[A.word(0)])}],
    A.write_header(28,[A.word(0)]),
    [A.word(0),A.set(3),A.CodeBlock{2,[A.CodeBlock{3,loop}]},A.word(1),A.global_set()],
    A.result(0,[A.none()],[A.none()],[A.word(0)])])}

def put() -> A.Function:
  # index/value 0/1; address/tag 2/3; cursor/previous/budget/next/cursor-address 4..8.
  +scan : List<&2,A.Instruction> = A.concat([
    [A.get(4),A.get(0),A.op(70),A.branch_if(1)],
    A.guard([A.get(4),A.none(),A.op(70)],A.failure(11,[A.get(1)])),
    A.guard(A.concat([[A.get(4)],A.header(4),[A.op(79)]]),A.failure(11,[A.get(1)])),
    A.guard(A.concat([[A.get(6)],A.header(4),[A.op(79)]]),A.failure(11,[A.get(1)])),
    A.address(4,8), A.guard(A.concat([A.field(8,0),[A.op(69),A.op(69)]]),A.failure(11,[A.get(1)])),
    [A.get(4),A.set(5)], A.field(8,12),
    [A.set(4),A.get(6),A.word(1),A.op(106),A.set(6),A.branch(0)]])
  A.FunctionCode{"put",2,7,A.concat([
    A.initialized(),
    A.guard(A.concat([[A.get(0)],A.header(4),[A.op(79)]]),A.failure(3,[A.get(1)])),
    A.address(0,2), A.field(2,0), [A.set(3)],
    A.guard([A.get(3),A.word(2),A.op(70)],A.failure(8,[A.get(1)])),
    A.guard([A.get(3),A.word(1),A.op(70)],A.failure(7,[A.get(1)])),
    A.guard([A.get(3),A.op(69),A.op(69)],A.failure(11,[A.get(1)])),
    A.guard(A.concat([A.field(2,4),A.header(8),[A.op(75)]]),A.failure(11,[A.get(1)])),
    A.header(12),[A.set(4),A.none(),A.set(5),A.word(0),A.set(6),A.CodeBlock{2,[A.CodeBlock{3,scan}]}],
    A.field(2,12),[A.set(7),A.get(5),A.none(),A.op(70),
      A.CodeIf{A.write_header(12,[A.get(7)]),A.concat([A.address(5,8),A.write_field(8,12,[A.get(7)])])}],
    A.write_field(2,0,[A.word(1)]), A.write_field(2,8,[A.get(1)]), A.write_field(2,12,[A.none()]),
    A.result(0,[A.get(0)],A.field(2,4),[A.word(0)])])}

def alloc() -> A.Function:
  A.FunctionCode{"alloc",1,1,A.concat([
    A.initialized(), A.header(12), [A.set(1)],
    A.guard([A.get(1),A.none(),A.op(70)],A.failure(2,[A.get(0)])),
    [A.get(1),A.get(0),A.call(2)]])}

def take() -> A.Function:
  # arena/index/generation 0..2; address/tag/current-generation/payload 3..6.
  A.FunctionCode{"take",3,4,A.concat([
    A.initialized(),
    A.guard(A.concat([[A.get(0)],A.header(0),[A.op(71)]]),A.failure(4,[A.word(0)])),
    A.guard(A.concat([[A.get(1)],A.header(4),[A.op(79)]]),A.failure(3,[A.word(0)])),
    A.address(1,3), A.field(3,0), [A.set(4)],
    A.guard([A.get(4),A.word(2),A.op(70)],A.failure(8,[A.word(0)])),
    A.guard([A.get(4),A.word(1),A.op(75)],A.failure(11,[A.word(0)])),
    A.field(3,4), [A.set(5)],
    A.guard([A.get(5),A.get(2),A.op(71)],A.failure(5,[A.word(0)])),
    A.guard([A.get(4),A.op(69)],A.failure(6,[A.word(0)])),
    A.guard(A.concat([[A.get(5)],A.header(8),[A.op(75)]]),A.failure(11,[A.word(0)])),
    A.field(3,8), [A.set(6)], A.write_field(3,8,[A.word(0)]),
    [A.get(5)], A.header(8), [A.op(73), A.CodeIf{
      A.concat([A.write_field(3,0,[A.word(0)]),A.write_field(3,4,[A.get(5),A.word(1),A.op(106)]),
        A.write_field(3,12,A.header(12)),A.write_header(12,[A.get(1)])]),
      A.concat([A.write_field(3,0,[A.word(2)]),A.write_field(3,12,[A.none()])])}],
    A.result(0,[A.get(1)],[A.get(2)],[A.get(6)])])}

def release() -> A.Function:
  A.FunctionCode{"release",3,1,A.concat([
    [A.get(0),A.get(1),A.get(2),A.call(4),A.set(3),A.get(3),A.op(69),
      A.CodeIf{A.write_header(28,A.concat([A.header(28),[A.word(1),A.op(106)]])),Nil{}}],
    [A.get(3)]])}

def functions() -> List<&2,A.Function>: [finish(),init(),put(),alloc(),take(),release()]

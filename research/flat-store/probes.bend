import Base
import ../../src/syntax.bend as S
import ../../src/diagnostic.bend as D
import ../owned-store/store.bend as T
import ./layout.bend as L
import ./assembly.bend as A
import ./module.bend as M
import ./LAWS.bend as Laws
import ./PROOF.bend as Proof

def layout_error(error: L.Error) -> String:
  match error:
    case L.CapacityLimit{}: "CapacityLimit"
    case L.IndexBounds{}: "IndexBounds"
    case L.LocatorArity{}: "LocatorArity"

def locator(result: Result<L.Error,T.Locator>) -> String:
  match result:
    case Done{key}: List.show(~&2,~U32,~U32.show,L.encode_locator(key))
    case Fail{error}: layout_error(error)

def offset(result: Result<L.Error,U32>) -> String:
  match result:
    case Done{address}: U32.show(address)
    case Fail{error}: layout_error(error)

def encoded(result: Result<S.Error,List<&2,U32>>) -> String:
  match result:
    case Done{values}: List.show(~&2,~U32,~U32.show,values)
    case Fail{error}: D.error(error)

def main() -> IO(Unit):
  do IO<Unit>:
    IO.print(locator(L.decode_locator([0,0,0])))
    IO.print(locator(L.decode_locator([4294967295,4294967295,4294967295])))
    IO.print(locator(L.decode_locator([])))
    IO.print(locator(L.decode_locator([41,0])))
    IO.print(locator(L.decode_locator([41,0,1,0])))
    IO.print(offset(L.offset(0,0)))
    IO.print(offset(L.offset(1,0)))
    IO.print(offset(L.offset(3,2)))
    IO.print(offset(L.offset(4096,4095)))
    IO.print(offset(L.offset(4096,4096)))
    IO.print(offset(L.offset(4097,0)))
    IO.print(offset(L.offset(4294967295,0)))
    IO.print(offset(L.offset(4096,4294967295)))
    IO.print(encoded(Laws.bytes(A.encode(1n,A.OneInstruction{A.none()},2))))
    IO.print(encoded(Laws.bytes(A.encode(1n,A.OneInstruction{A.save(128)},4))))
    IO.print(encoded(Laws.bytes(A.encode(1n,A.OneInstruction{A.word(2147483647)},6))))
    IO.print(encoded(Laws.bytes(A.encode(1n,A.OneInstruction{A.word(2147483648)},6))))
    IO.print(encoded(Laws.bytes(A.encode(1n,A.OneInstruction{A.none()},1))))
    IO.print(encoded(Laws.bytes(A.encode(0n,A.OneInstruction{A.none()},2))))
    IO.print(encoded(Laws.bytes(A.encode(1n,A.OneInstruction{A.CodeIndex{32,4294967295}},6))))
    IO.print(encoded(Laws.bytes(A.encode(4n,A.OneInstruction{A.CodeBlock{2,[A.CodeBlock{3,[]}]}},6))))
    IO.print(encoded(Laws.bytes(A.encode(1n,A.OneInstruction{A.CodeByte{256}},1))))
    IO.print(encoded(M.emit(0)))
    IO.print(encoded(M.emit(1049)))

import Base
import ./slot.bend as S
import ./task.bend as T

def show_observation(o: U32 & U32 & U32) -> String:
  (tag,dest,value) = o
  String.concat([U32.show(tag),",",U32.show(dest),",",U32.show(value)])

def sample() -> T.Run:
  T.start(73,3n,11,[T.Unary{3,5},T.Binary{T.OwnedWord{7}}])

def show_put(p: S.Put<T.Payload>) -> String:
  match p:
    case S.Inserted{s}: "inserted"
    case S.Rejected{S.Occupied{T.OwnedWord{old}},T.OwnedWord{new}}:
      String.concat(["rejected:",U32.show(old),",",U32.show(new)])
    case S.Rejected{S.Vacant{},new}: "invalid-empty-rejection"

def show_take(p: S.Take<T.Payload>) -> String:
  match p:
    case S.Missing{S.Vacant{}}: "missing"
    case S.Missing{S.Occupied{value}}: "invalid-full-missing"
    case S.Extracted{S.Vacant{},T.OwnedWord{x}}: String.append("extracted:",U32.show(x))
    case S.Extracted{S.Occupied{old},value}: "invalid-retained-owner"

def main() -> IO(Unit):
  do IO<Unit>:
    IO.print(show_observation(T.observe(T.run(0n,sample()))))
    IO.print(show_observation(T.observe(T.run(5n,sample()))))
    IO.print(show_observation(T.observe(T.run(6n,sample()))))
    IO.print(show_observation(T.observe(T.slices(6n,1n,sample()))))
    IO.print(show_observation(T.observe(T.slices(2n,3n,sample()))))
    IO.print(show_observation(T.observe(T.slices(9n,0n,sample()))))
    IO.print(show_observation(T.observe(T.run(9n,T.run(6n,sample())))))
    IO.print(show_observation(T.observe(T.run(2n,T.start(41,0n,9,[T.Binary{T.OwnedWord{7}}])))))
    IO.print(show_put(S.put(T.Payload,S.Occupied{T.OwnedWord{7}},T.OwnedWord{9})))
    IO.print(show_take(S.take(T.Payload,S.put_slot(T.Payload,S.put(T.Payload,S.Vacant{},T.OwnedWord{7})))))
    IO.print(show_take(S.take(T.Payload,S.take_slot(T.Payload,S.take(T.Payload,S.Occupied{T.OwnedWord{7}})))))

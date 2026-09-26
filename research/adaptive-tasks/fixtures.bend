import Base
import ./oracle.bend as O

def main() -> IO(Unit):
  do IO<Unit>:
    IO.print(O.record("ordered",O.Fork{O.Leaf{7,0n},O.Leaf{9,0n}}))
    IO.print(O.record("right_finishes_first",O.Fork{O.Leaf{7,17n},O.Leaf{9,0n}}))
    IO.print(O.record("left_finishes_first",O.Fork{O.Leaf{7,0n},O.Leaf{9,17n}}))
    IO.print(O.record("balanced",O.balanced(6n,11)))
    IO.print(O.record("skewed_splittable",O.Fork{O.balanced(6n,13),O.Leaf{19,1n}}))
    IO.print(O.record("opaque_heavy_leaf",O.Fork{O.Leaf{23,71n},O.balanced(3n,17)}))
    IO.print(O.record("serial_frames",O.chain(16n,O.Leaf{29,3n})))
    IO.print(O.record("single",O.Leaf{4294967295,11n}))
    IO.print(O.record("nested_frames",O.Then{O.Fork{O.Then{O.Leaf{3,7n},7,11},O.Leaf{5,2n}},13,17}))
    IO.print(O.record("cpu_frames",O.Fork{O.Leaf{7,0n},O.Then{O.Leaf{11,3n},3,5}}))

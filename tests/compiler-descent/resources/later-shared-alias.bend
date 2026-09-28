type Flag is Data:
  Off{}
  On{}
type Tree is Data:
  Leaf{}
  Fork{left: Tree, right: Tree}
type N is Data:
  Z{}
  S{pred: N}
def drain(n: N, spare: Tree) -> Flag:
  match n:
    case Z{}: On{}
    case S{p}:
      +t0 : Tree = Leaf{}
      +t1 : Tree = Fork{t0,t0}
      +t2 : Tree = Fork{t1,t1}
      +t3 : Tree = Fork{t2,t2}
      +t4 : Tree = Fork{t3,t3}
      +t5 : Tree = Fork{t4,t4}
      +t6 : Tree = Fork{t5,t5}
      +t7 : Tree = Fork{t6,t6}
      +t8 : Tree = Fork{t7,t7}
      +t9 : Tree = Fork{t8,t8}
      +t10 : Tree = Fork{t9,t9}
      +t11 : Tree = Fork{t10,t10}
      +t12 : Tree = Fork{t11,t11}
      +t13 : Tree = Fork{t12,t12}
      +t14 : Tree = Fork{t13,t13}
      +t15 : Tree = Fork{t14,t14}
      +t16 : Tree = Fork{t15,t15}
      +t17 : Tree = Fork{t16,t16}
      +t18 : Tree = Fork{t17,t17}
      +t19 : Tree = Fork{t18,t18}
      +t20 : Tree = Fork{t19,t19}
      +t21 : Tree = Fork{t20,t20}
      +t22 : Tree = Fork{t21,t21}
      +t23 : Tree = Fork{t22,t22}
      +t24 : Tree = Fork{t23,t23}
      +t25 : Tree = Fork{t24,t24}
      +t26 : Tree = Fork{t25,t25}
      +t27 : Tree = Fork{t26,t26}
      +t28 : Tree = Fork{t27,t27}
      +t29 : Tree = Fork{t28,t28}
      +t30 : Tree = Fork{t29,t29}
      +t31 : Tree = Fork{t30,t30}
      +t32 : Tree = Fork{t31,t31}
      drain(p,t32)
def main() -> Flag:
  drain(S{Z{}},Leaf{})

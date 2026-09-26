import Base

# Pure tree evaluator, independent of task, slot, or GPU state transitions.
type Program is Data:
  Leaf{seed: U32, ticks: Nat}
  Fork{left: Program, right: Program}
  Then{child: Program, factor: U32, bias: U32}

def iterate(n: Nat, x: U32) -> U32:
  match n:
    case 0n: x
    case 1n+k: iterate(k,U32.add(U32.mul(1664525,x),1013904223))

def eval(p: Program) -> U32:
  match p:
    case Leaf{seed,ticks}: iterate(ticks,seed)
    case Fork{left,right}: U32.add(U32.mul(31,eval(left)),eval(right))
    case Then{child,factor,bias}: U32.add(U32.mul(eval(child),factor),bias)

def balanced(+depth: Nat, +seed: U32) -> Program:
  match depth:
    case 0n: Leaf{seed,U32.to_nat(U32.add(U32.mod(seed,5),1))}
    case 1n+d: Fork{balanced(d,U32.mul(seed,2)),balanced(d,U32.add(U32.mul(seed,2),1))}

def chain(n: Nat, child: Program) -> Program:
  match n:
    case 0n: child
    case 1n+k: Then{chain(k,child),3,5}

def json(p: Program) -> String:
  match p:
    case Leaf{seed,ticks}:
      String.concat(["[0,",U32.show(seed),",",Nat.show(ticks),"]"])
    case Fork{left,right}:
      String.concat(["[1,",json(left),",",json(right),"]"])
    case Then{child,factor,bias}:
      String.concat(["[2,",json(child),",",U32.show(factor),",",U32.show(bias),"]"])

def record(name: String, +p: Program) -> String:
  String.concat(["{\"name\":\"",name,"\",\"tree\":",json(p),",\"expected\":",U32.show(eval(p)),"}"])

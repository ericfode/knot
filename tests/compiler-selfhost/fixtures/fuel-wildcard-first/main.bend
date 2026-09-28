# A wildcard-fuel row first, in src/load.bend's `run` shape: a terminal action
# answers before the fuel is inspected, so an empty tank still reports it.
import Base

type Level is Type:
  Starved{}
  Halted{}
  Full{}

type Action is Data:
  Stopped{}
  Finished{}
  Advance{steps: Nat}

type Budget is Type:
  B0{}
  B1{}
  B2{}

type Start is Type:
  Stop{}
  Finish{}
  Walk{}

def step(steps: Nat) -> Action:
  match steps:
    case 0n: Finished{}
    case 1n+p: Advance{p}

def run(fuel: Nat, action: Action) -> Level:
  match fuel action:
    case _ Stopped{}: Halted{}
    case _ Finished{}: Full{}
    case 0n _: Starved{}
    case 1n+ +n Advance{steps}: run(n,step(steps))

def budget(b: Budget) -> Nat:
  match b:
    case B0{}: 0n
    case B1{}: 1n
    case B2{}: 2n

def action(s: Start) -> Action:
  match s:
    case Stop{}: Stopped{}
    case Finish{}: Finished{}
    case Walk{}: Advance{1n}

def probe(b: Budget, s: Start) -> Level:
  run(budget(b),action(s))

def main() -> Level:
  probe(B0{},Stop{})

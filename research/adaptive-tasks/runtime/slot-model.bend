import Base
import ../../owned-store/model.bend as M
import ../../owned-store/protocol.bend as P
import ../../owned-store/store.bend as S

# Decode command records into the independent store model, preserving refusal.
type Command is Data:
  Command{op: U32, a: U32, b: U32, c: U32}

def event(result: P.Snapshot & P.Observation) -> P.Snapshot & String:
  (state,reply) = result
  (state,P.event(reply))

def step(command: Command, state: P.Snapshot) -> P.Snapshot & String:
  match command:
    case Command{1,a,b,c}: event(M.step(P.Insert{a,b},state))
    case Command{2,a,b,c}: event(M.step(P.Extract{S.Locator{a,b,c}},state))
    case Command{3,a,b,c}: event(M.step(P.Dispose{S.Locator{a,b,c}},state))
    case Command{4,a,b,c}: event(M.step(P.Reserve{a},state))
    case Command{op,a,b,c}: (state,"unsupported")

def continue(result: P.Snapshot & String, next: P.Snapshot -> String -> String) -> String:
  (state,reply) = result
  next(state,reply)

def identity(s: String) -> String:
  s

def run(commands: List<&2,Command>, state: P.Snapshot, events: List<&2,String>) -> String:
  match commands:
    case Nil{}:
      String.concat([List.show(~&2,~String,~identity,List.reverse(&2,String,events)),"/",P.snapshot(state)])
    case Con{command,tail}: continue(step(command,state),state => reply => run(tail,state,Con{reply,events}))

def start(arena: U32, +capacity: U32, ceiling: U32, commands: List<&2,Command>) -> String:
  run(commands,P.Snapshot{arena,capacity,ceiling,M.positions(U32.to_nat(capacity),0),M.blank(U32.to_nat(capacity))},Nil{})

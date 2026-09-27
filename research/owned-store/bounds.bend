import Base
import ./store.bend as S
import ./protocol.bend as P
import ./observe.bend as O

# Reachable near-ceiling states, constructed without billions of setup cycles.
def take_generation(+generation: U32) -> String:
  O.continue(O.taken(S.take(O.Payload,
    S.Store{41,1,4294967295,Nil{},ALeaf{S.Live{generation,O.Owned{7}}}},S.Locator{41,0,generation})),
    store => event => P.observation([event],O.snapshot(store)))

def main() -> IO(Unit):
  do IO<Unit>:
    IO.print(take_generation(4294967294))
    IO.print(take_generation(4294967295))

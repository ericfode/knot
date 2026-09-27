import ./three.bend as Three

type Hop is Type:
  Near{}
  Far{}

def turn(x: Three.Hop) -> Hop:
  match x:
    case Three.Near{}: Far{}
    case Three.Far{}: Near{}

def lift() -> Hop:
  turn(Three.start())

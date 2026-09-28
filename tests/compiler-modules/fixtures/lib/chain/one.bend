import ./two.bend as Two

type Hop is Type:
  Near{}
  Far{}

def turn(x: Two.Hop) -> Hop:
  match x:
    case Two.Near{}: Far{}
    case Two.Far{}: Near{}

def lift() -> Hop:
  turn(Two.lift())

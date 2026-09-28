# One unbox instantiated at Flag, Color and Box<A>; unbox2 forwards its own A.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Green{}
  Blue{}

type Box<-A: Type> is Type:
  Box{value: A}

def unbox(-A: Type, b: Box<A>) -> A:
  match b:
    case Box{v}:
      v

def unbox2(-A: Type, bb: Box<Box<A>>) -> A:
  unbox(A, unbox(Box<A>, bb))

def gate(x: Flag, c: Color) -> Color:
  match x:
    case Off{}:
      Red{}
    case On{}:
      c

def both(x: Flag, c: Color) -> Color:
  gate(unbox2(Flag, Box{Box{x}}), unbox(Color, Box{c}))

def main() -> Color:
  both(On{}, Blue{})

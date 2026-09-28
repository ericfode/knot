import Base

# An affine Type enum and a reusable Data enum: one List.reverse at &1, one at &2.
type Light is Type:
  Dark{}
  Lit{}

type Mark is Data:
  Cross{}
  Ring{}

def front_light(xs: List<&1, Light>) -> Light:
  match xs:
    case Nil{}: Dark{}
    case Con{h, t}: h

def front_mark(xs: List<&2, Mark>) -> Mark:
  match xs:
    case Nil{}: Cross{}
    case Con{h, t}: h

def flip(x: Light) -> Light:
  front_light(List.reverse(&1, Light, Con{Dark{}, Con{x, Nil{}}}))

def last(m: Mark) -> Mark:
  front_mark(List.reverse(&2, Mark, Con{Ring{}, Con{Cross{}, Con{m, Nil{}}}}))

def main() -> Light:
  flip(Lit{})

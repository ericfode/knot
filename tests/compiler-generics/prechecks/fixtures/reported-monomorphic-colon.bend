type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Green{}
  Blue{}

type Tag<-A: Type> is Data:
  TagX{}
  TagY{}

type Mono is Data # c
  :
  MonoX{}
  MonoY{}

def pickc(t: Tag<Flag>) -> Color:
  match t:
    case TagX{}:
      Red{}
    case TagY{}:
      Blue{}

def pickm(t: Mono) -> Color:
  match t:
    case MonoX{}:
      Red{}
    case MonoY{}:
      Blue{}

def main() -> Color:
  pickc(TagY{})

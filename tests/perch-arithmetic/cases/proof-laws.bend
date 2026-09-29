import Base

type Flag is Data:
  Off{}
  On{}

def flip(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}

law flip_twice_on:
  {flip(flip(On{})) == On{} : Flag}

law flip_once_off:
  {flip(Off{}) == On{} : Flag}

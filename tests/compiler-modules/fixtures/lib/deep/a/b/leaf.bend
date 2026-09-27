import ../../../flag.bend as F
import ./twig.bend as T

def twice(x: F.Flag) -> F.Flag:
  T.keep(F.flip(F.flip(x)))

# Tuples nest to the right: (a,b,c) is (a,(b,c)) in terms, in patterns and in A & B & C.
import Base

type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Blue{}

def mid(t: Flag & Color & Flag) -> Color:
  (a,c,b) = t
  c

def last(t: Flag & Color & Flag) -> Flag:
  (a,rest) = t
  (c,b) = rest
  b

def flat(f: Flag, c: Color, g: Flag) -> Color:
  mid((f,(c,g)))

def split(f: Flag, c: Color, g: Flag) -> Flag:
  last((f,c,g))

def main() -> Color:
  flat(On{},Blue{},Off{})

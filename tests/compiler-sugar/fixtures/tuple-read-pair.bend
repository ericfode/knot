# The read_pair shape: (file,result) = pair on a Base A & B, and (a,b) built back.
import Base

type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Blue{}

def swap(pair: Flag & Color) -> Color & Flag:
  (flag,color) = pair
  (color,flag)

def back(pair: Color & Flag) -> Flag:
  (color,flag) = pair
  flag

def front(pair: Color & Flag) -> Color:
  (color,flag) = pair
  color

def flag_of(f: Flag, c: Color) -> Flag:
  back(swap((f,c)))

def color_of(f: Flag, c: Color) -> Color:
  front(swap((f,c)))

def main() -> Color:
  color_of(On{},Blue{})

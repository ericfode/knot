# Primitive fields display as their seed literals inside the constructor
# frame. Knot's frame is Name{a,b}; the seed separates fields with ", ".
import Base

type Side is Data:
  Left{}
  Right{}

type Box is Data:
  Box{word: U32, char: Char}

type Mix is Data:
  Mix{count: Nat, text: String, side: Side, flag: Bool, first: Box, second: Box}

def zeroes() -> Box:
  Box{0, '\0'}

def mix() -> Mix:
  Mix{3n, "a, b{}", Right{}, True{}, Box{4294967295, '\''}, Box{0, '"'}}

def main() -> Box:
  Box{1, 'a'}

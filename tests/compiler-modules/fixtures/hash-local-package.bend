import 0x4454ff15e96d17231b8b4ebd9030ac38/board.bend as Board
import 0x4454ff15e96d17231b8b4ebd9030ac38/mark.bend as Mark

type Light is Type:
  Dark{}
  Lit{}

def see(x: Mark.Mark) -> Light:
  match x:
    case Mark.Cross{}: Lit{}
    case Mark.Nought{}: Dark{}

def main() -> Light:
  see(Board.twice(Board.first()))

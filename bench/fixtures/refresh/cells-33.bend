type Flag is Data:
  Off{}
  On{}

type Cells is Type:
  Empty{}
  Cell{head: Flag, tail: Cells}

def last(xs: Cells, value: Flag) -> Flag:
  match xs:
    case Empty{}: value
    case Cell{head,tail}: last(tail,head)

def main() -> Flag:
  last(Cell{On{},Cell{Off{},Cell{On{},Cell{Off{},Cell{On{},Cell{Off{},Cell{On{},Cell{Off{},Cell{On{},Cell{Off{},Cell{On{},Cell{Off{},Cell{On{},Cell{Off{},Cell{On{},Cell{Off{},Cell{On{},Cell{Off{},Cell{On{},Cell{Off{},Cell{On{},Cell{Off{},Cell{On{},Cell{Off{},Cell{On{},Cell{Off{},Cell{On{},Cell{Off{},Cell{On{},Cell{Off{},Cell{On{},Cell{Off{},Cell{On{},Empty{}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}},Off{})

type Atom is Data:
  Nine{}
  Eleven{}
type DataPair is Data:
  DataPair{left: Atom, right: Atom}
type Pairs is Data:
  Pairs{left: DataPair, right: DataPair}
def opened(+pair: DataPair) -> Pairs:
  match pair:
    case DataPair{left,right}: Pairs{pair,DataPair{right,left}}
def main() -> Pairs:
  opened(DataPair{Nine{},Eleven{}})

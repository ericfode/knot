type Atom is Data:
  Nine{}
  Eleven{}
type Owned is Type:
  Seven{}
type DataPair is Data:
  DataPair{left: Atom, right: Atom}
type Frame is Type:
  Frame{child: Owned, +value: DataPair}
def rebuild(frame: Frame) -> Frame:
  match frame:
    case Frame{child,value}: Frame{child,value}
def main() -> Frame:
  rebuild(Frame{Seven{},DataPair{Nine{},Eleven{}}})

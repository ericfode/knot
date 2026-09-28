type Mark is Type:
  Cross{}
  Nought{}

def swap(m: Mark) -> Mark:
  match m:
    case Cross{}: Nought{}
    case Nought{}: Cross{}

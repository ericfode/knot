type Flag is Data:
  Off{}
  On{}

type Peano is Data:
  PeanoZero{}
  PeanoSucc{pred: Peano}

def parity(n: Peano) -> Flag:
  match n:
    case PeanoZero{}: Off{}
    case PeanoSucc{p}:
      match p:
        case PeanoZero{}: On{}
        case PeanoSucc{q}: parity(q)

def main() -> Flag:
  parity(PeanoSucc{PeanoSucc{PeanoSucc{PeanoSucc{PeanoSucc{PeanoSucc{PeanoSucc{PeanoSucc{PeanoSucc{PeanoSucc{PeanoSucc{PeanoSucc{PeanoSucc{PeanoSucc{PeanoSucc{PeanoSucc{PeanoSucc{PeanoSucc{PeanoSucc{PeanoSucc{PeanoSucc{PeanoSucc{PeanoSucc{PeanoSucc{PeanoSucc{PeanoSucc{PeanoSucc{PeanoSucc{PeanoSucc{PeanoSucc{PeanoSucc{PeanoSucc{PeanoSucc{PeanoZero{}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}})

type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Green{}
  Blue{}

type Box<-A: Type> is Type:
  Box{value: A}

type Pair<-A: Type, -B: Type> is Type:
  Pair{fst: A, snd: B}

type Seq<a, -A: Kind(a)> is Kind(a):
  End{}
  Link{head: A, tail: Seq<a, A>}

type Tag<-A: Type> is Data:
  TagX{}
  TagY{}

type Tagged<-A: Type> is Data:
  Tagged{flag: Flag}

type Cell<-A: Data> is Data:
  Cell{value: A}

def main() -> Tag<Flag>:
  TagY {}

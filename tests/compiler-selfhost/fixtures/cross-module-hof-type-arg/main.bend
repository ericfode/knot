# Twin of cross-module-hof: the explicit type argument disagrees with the result bound.
import Base
import ./syntax.bend as S

type Answer is Type:
  Missing{}
  Tardy{}
  Low{}
  High{}

type Level is Data:
  Ground{}
  Upper{}

type Case is Data:
  Absent{}
  Early{}
  Plain{}
  Raised{}

def lookup(c: Case) -> Result<S.Error,Bool>:
  match c:
    case Absent{}: Fail{S.Unknown{}}
    case Early{}: Done{False{}}
    case Plain{}: Done{False{}}
    case Raised{}: Done{True{}}

def order(c: Case) -> Bool:
  match c:
    case Absent{}: True{}
    case Early{}: False{}
    case Plain{}: True{}
    case Raised{}: True{}

def level(+up: Bool, +known: Bool) -> Result<S.Error,Level>:
  S.choose(Result<S.Error,Level>,known,u =>
    S.choose(Result<S.Error,Level>,up,v => Done{Upper{}},v => Done{Ground{}}),u =>
    Fail{S.Late{}})

def answer(r: Result<S.Error,Level>) -> Answer:
  match r:
    case Fail{S.Unknown{}}: Missing{}
    case Fail{S.Late{}}: Tardy{}
    case Done{Ground{}}: Low{}
    case Done{Upper{}}: High{}

def probe(+c: Case) -> Answer:
  answer(S.bind(Level,Level,lookup(c),up => level(up,order(c))))

def main() -> Answer:
  probe(Raised{})

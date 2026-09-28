# The dedented choose ladder of src/parse.bend:153-161: after `u =>` the next
# `choose(` starts back at the body column, and the last thunk closes all.
type Answer is Data:
  No{}
  Yes{}

type Level is Type:
  Low{}
  Mid{}
  High{}
  Top{}

type Tick is Type:
  Tick{}

def choose(c: Answer, yes: Tick -> Level, no: Tick -> Level) -> Level:
  match c:
    case Yes{}: yes(Tick{})
    case No{}: no(Tick{})

def grade(a: Answer, b: Answer, c: Answer) -> Level:
  choose(a,u =>
    Top{},u =>
  choose(b,u =>
    High{},u =>
  choose(c,u =>
    Mid{},u =>
    Low{})))

def main() -> Level:
  grade(No{},No{},Yes{})

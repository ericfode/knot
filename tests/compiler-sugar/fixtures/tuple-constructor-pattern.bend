# The Fail{(code,message)} shape: a tuple pattern inside a constructor pattern.
import Base

type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Blue{}

type Report is Type:
  Failed{info: Flag & Color}
  Passed{flag: Flag}

def text(r: Report) -> Color:
  match r:
    case Failed{(code,message)}: message
    case Passed{flag}: Red{}

def status(r: Report) -> Flag:
  match r:
    case Failed{(code,message)}: code
    case Passed{flag}: flag

def failed_text(f: Flag, c: Color) -> Color:
  text(Failed{(f,c)})

def failed_status(f: Flag, c: Color) -> Flag:
  status(Failed{(f,c)})

def passed_status(f: Flag) -> Flag:
  status(Passed{f})

def main() -> Color:
  failed_text(Off{},Blue{})

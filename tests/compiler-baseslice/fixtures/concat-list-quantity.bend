import Base

type Phase is Data:
  Opening{}
  Reading{}

type Code is Data:
  Missing{}
  Denied{}

type Pieces is Data:
  NoPieces{}
  Blanks{}
  Split{}

type Verdict is Data:
  No{}
  Yes{}

def phase(p: Phase) -> String:
  match p:
    case Opening{}: "open"
    case Reading{}: "read"

def code(c: Code) -> U32:
  match c:
    case Missing{}: 2
    case Denied{}: 13

def verdict(b: Bool) -> Verdict:
  match b:
    case False{}: No{}
    case True{}: Yes{}

# driver.read_result: the HostFailure line, joined by String.concat.
def failure(phase: String, +code: U32, message: String) -> List<String>:
  ["HostFailure\t", phase, "\t", U32.show(code), "\t", message]

def pieces(n: Pieces) -> List<&2, String>:
  match n:
    case NoPieces{}: []
    case Blanks{}: ["", "", ""]
    case Split{}: ["He", "", "llo"]

def report(p: Phase, c: Code) -> Verdict:
  verdict(String.eq(String.concat(failure(phase(p), code(c), "No such file")),
    "HostFailure\tread\t2\tNo such file"))

def empty(n: Pieces) -> Verdict:
  verdict(String.eq(String.concat(pieces(n)), ""))

def main() -> Verdict:
  report(Reading{}, Missing{})

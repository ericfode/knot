import Base

# A stand-in for File: an affine handle paired with the read result.
type Handle is Data:
  Handle{id: U32}

type Case is Data:
  Missing{}
  Denied{}
  Loaded{}

type Report is Data:
  MissingReport{}
  DeniedReport{}
  SourceText{}
  Garbled{}

def read(c: Case) -> Handle & Result<&1, &1, U32 & String, String>:
  match c:
    case Missing{}: (Handle{3}, Fail{(2, "No such file")})
    case Denied{}: (Handle{3}, Fail{(13, "Permission denied")})
    case Loaded{}: (Handle{3}, Done{"type"})

# driver.read_result and driver.read_pair, returning the text instead of IO.
def read_result(result: Result<&1, &1, U32 & String, String>) -> String:
  match result:
    case Fail{(code, message)}: String.concat(["HostFailure\tread\t", U32.show(code), "\t", message])
    case Done{text}: text

def read_pair(pair: Handle & Result<&1, &1, U32 & String, String>) -> String:
  (handle, result) = pair
  read_result(result)

def report_of(+s: String) -> Report:
  Bool.pick(Report, String.eq(s, "HostFailure\tread\t2\tNo such file"), MissingReport{},
  Bool.pick(Report, String.eq(s, "HostFailure\tread\t13\tPermission denied"), DeniedReport{},
  Bool.pick(Report, String.eq(s, "type"), SourceText{}, Garbled{})))

def report(c: Case) -> Report:
  report_of(read_pair(read(c)))

def main() -> Report:
  report(Denied{})

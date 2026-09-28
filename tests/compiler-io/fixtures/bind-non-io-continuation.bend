import Base

# The continuation must answer IO(B); a bare Unit is not an action.
def main() -> IO(Unit):
  IO.bind(List<String>,Unit,IO.args(),args => Unit{})

import Base

def say(+tag: String) -> IO(String):
  IO.bind(Unit,String,IO.print(tag),u => IO.pure(String,tag))

def shout(tag: String) -> IO(Unit):
  IO.print(String.append(tag,"!"))

def extend(suffix: String, tag: String) -> IO(String):
  say(String.append(tag,suffix))

# Left- and right-nested binds run their effects in the same written order.
def left() -> IO(Unit):
  IO.bind(String,Unit,IO.bind(String,String,say("a"),extend("b")),shout)

def right(+suffix: String) -> IO(Unit):
  IO.bind(String,Unit,say("c"),tag => IO.bind(String,Unit,say(String.append(tag,suffix)),shout))

def main() -> IO(Unit):
  do IO<Unit>:
    left()
    right("d")
    IO.bind(String,Unit,say("e"),tag => shout(String.append(tag,"f")))
    IO.print("end")

import Base

def main() -> IO(Unit):
  IO.print(U32.show(Char.to_u32(Char.from_u32(55296))))

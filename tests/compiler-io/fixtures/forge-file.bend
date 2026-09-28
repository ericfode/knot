import Base

# File has no constructor: a number is not a handle.
def main() -> IO(Unit):
  IO.bind(File & Result<&1,&1,U32 & String,String>,Unit,File.read(3,8),pair => IO.print("forged"))

import Base

# Each IO.print hands one String to the host, which appends one "\n".
def main() -> IO(Unit):
  do IO<Unit>:
    IO.print("plain")
    IO.print("")
    IO.print("two\nlines")
    IO.print("tab\there\rreturn")
    IO.print("nul\0inside")
    IO.print("\u{e9}\u{1F600}\u{10FFFF}")
    IO.print("\\ and \"quotes\"")
    IO.print("end")

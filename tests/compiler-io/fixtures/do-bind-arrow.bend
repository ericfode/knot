import Base

# A do block that binds with <- ; Knot's own do blocks hold statements only.
def main() -> IO(Unit):
  do IO<Unit>:
    args : List<String> <- IO.args()
    IO.print(String.append("argc ",U32.show(U32.from_nat(List.length(&1,String,args)))))

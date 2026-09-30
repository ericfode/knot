type Flag is Data:
  Off{}
  On{}

def leaf(x: Flag) -> Flag:
  +v0 : Flag = x
  +v1 : Flag = v0
  +v2 : Flag = v1
  +v3 : Flag = v2
  +v4 : Flag = v3
  +v5 : Flag = v4
  +v6 : Flag = v5
  +v7 : Flag = v6
  +v8 : Flag = v7
  +v9 : Flag = v8
  +v10 : Flag = v9
  +v11 : Flag = v10
  +v12 : Flag = v11
  +v13 : Flag = v12
  +v14 : Flag = v13
  +v15 : Flag = v14
  +v16 : Flag = v15
  v16
def main() -> Flag:
  leaf(On{})

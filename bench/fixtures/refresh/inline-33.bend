type Flag is Data:
  Off{}
  On{}

def flip(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}

def step0(x: Flag) -> Flag:
  x

def step1(x: Flag) -> Flag:
  step0(flip(x))

def step2(x: Flag) -> Flag:
  step1(flip(x))

def step3(x: Flag) -> Flag:
  step2(flip(x))

def step4(x: Flag) -> Flag:
  step3(flip(x))

def step5(x: Flag) -> Flag:
  step4(flip(x))

def step6(x: Flag) -> Flag:
  step5(flip(x))

def step7(x: Flag) -> Flag:
  step6(flip(x))

def step8(x: Flag) -> Flag:
  step7(flip(x))

def step9(x: Flag) -> Flag:
  step8(flip(x))

def step10(x: Flag) -> Flag:
  step9(flip(x))

def step11(x: Flag) -> Flag:
  step10(flip(x))

def step12(x: Flag) -> Flag:
  step11(flip(x))

def step13(x: Flag) -> Flag:
  step12(flip(x))

def step14(x: Flag) -> Flag:
  step13(flip(x))

def step15(x: Flag) -> Flag:
  step14(flip(x))

def step16(x: Flag) -> Flag:
  step15(flip(x))

def step17(x: Flag) -> Flag:
  step16(flip(x))

def step18(x: Flag) -> Flag:
  step17(flip(x))

def step19(x: Flag) -> Flag:
  step18(flip(x))

def step20(x: Flag) -> Flag:
  step19(flip(x))

def step21(x: Flag) -> Flag:
  step20(flip(x))

def step22(x: Flag) -> Flag:
  step21(flip(x))

def step23(x: Flag) -> Flag:
  step22(flip(x))

def step24(x: Flag) -> Flag:
  step23(flip(x))

def step25(x: Flag) -> Flag:
  step24(flip(x))

def step26(x: Flag) -> Flag:
  step25(flip(x))

def step27(x: Flag) -> Flag:
  step26(flip(x))

def step28(x: Flag) -> Flag:
  step27(flip(x))

def step29(x: Flag) -> Flag:
  step28(flip(x))

def step30(x: Flag) -> Flag:
  step29(flip(x))

def step31(x: Flag) -> Flag:
  step30(flip(x))

def step32(x: Flag) -> Flag:
  step31(flip(x))

def step33(x: Flag) -> Flag:
  step32(flip(x))

def main() -> Flag:
  step33(On{})

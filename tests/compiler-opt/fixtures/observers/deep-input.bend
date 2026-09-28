type Peano is Data:
  Zero{}
  Succ{pred: Peano}
def f(n: Peano) -> Peano:
  match n:
    case Zero{}: Zero{}
    case Succ{p}: f(p)
def input() -> Peano:
  Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Zero{}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}
def main() -> Peano:
  input()

type OptObservation is Data:
  OptMismatch{}
  OptMatch{}
def opt_check0(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMatch{}
    case Succ{p}: OptMismatch{}
def opt_check1(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check0(p)
def opt_check2(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check1(p)
def opt_check3(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check2(p)
def opt_check4(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check3(p)
def opt_check5(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check4(p)
def opt_check6(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check5(p)
def opt_check7(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check6(p)
def opt_check8(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check7(p)
def opt_check9(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check8(p)
def opt_check10(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check9(p)
def opt_check11(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check10(p)
def opt_check12(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check11(p)
def opt_check13(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check12(p)
def opt_check14(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check13(p)
def opt_check15(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check14(p)
def opt_check16(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check15(p)
def opt_check17(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check16(p)
def opt_check18(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check17(p)
def opt_check19(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check18(p)
def opt_check20(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check19(p)
def opt_check21(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check20(p)
def opt_check22(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check21(p)
def opt_check23(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check22(p)
def opt_check24(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check23(p)
def opt_check25(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check24(p)
def opt_check26(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check25(p)
def opt_check27(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check26(p)
def opt_check28(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check27(p)
def opt_check29(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check28(p)
def opt_check30(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check29(p)
def opt_check31(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check30(p)
def opt_check32(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check31(p)
def opt_check33(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check32(p)
def opt_check34(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check33(p)
def opt_check35(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check34(p)
def opt_check36(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check35(p)
def opt_check37(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check36(p)
def opt_check38(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check37(p)
def opt_check39(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check38(p)
def opt_check40(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check39(p)
def opt_check41(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check40(p)
def opt_check42(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check41(p)
def opt_check43(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check42(p)
def opt_check44(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check43(p)
def opt_check45(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check44(p)
def opt_check46(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check45(p)
def opt_check47(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check46(p)
def opt_check48(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check47(p)
def opt_check49(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check48(p)
def opt_check50(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check49(p)
def opt_check51(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check50(p)
def opt_check52(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check51(p)
def opt_check53(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check52(p)
def opt_check54(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check53(p)
def opt_check55(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check54(p)
def opt_check56(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check55(p)
def opt_check57(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check56(p)
def opt_check58(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check57(p)
def opt_check59(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check58(p)
def opt_check60(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check59(p)
def opt_check61(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check60(p)
def opt_check62(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check61(p)
def opt_check63(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check62(p)
def opt_check64(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check63(p)
def opt_exact(x: Peano) -> OptObservation:
  opt_check64(x)
def opt_observe() -> OptObservation:
  opt_exact(main())
def opt_observe_bad() -> OptObservation:
  opt_exact(Zero{})

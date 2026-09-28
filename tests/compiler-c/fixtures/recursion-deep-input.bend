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

type CObservation is Data:
  CNo{}
  CYes{}
def c_all(a: CObservation, b: CObservation) -> CObservation:
  match a:
    case CNo{}: CNo{}
    case CYes{}: b
def c_literal_0(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CYes{}
    case Succ{f0}:
      CNo{}
def c_literal_1(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_0(f0),CYes{})
def c_literal_2(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_1(f0),CYes{})
def c_literal_3(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_2(f0),CYes{})
def c_literal_4(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_3(f0),CYes{})
def c_literal_5(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_4(f0),CYes{})
def c_literal_6(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_5(f0),CYes{})
def c_literal_7(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_6(f0),CYes{})
def c_literal_8(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_7(f0),CYes{})
def c_literal_9(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_8(f0),CYes{})
def c_literal_10(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_9(f0),CYes{})
def c_literal_11(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_10(f0),CYes{})
def c_literal_12(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_11(f0),CYes{})
def c_literal_13(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_12(f0),CYes{})
def c_literal_14(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_13(f0),CYes{})
def c_literal_15(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_14(f0),CYes{})
def c_literal_16(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_15(f0),CYes{})
def c_literal_17(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_16(f0),CYes{})
def c_literal_18(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_17(f0),CYes{})
def c_literal_19(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_18(f0),CYes{})
def c_literal_20(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_19(f0),CYes{})
def c_literal_21(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_20(f0),CYes{})
def c_literal_22(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_21(f0),CYes{})
def c_literal_23(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_22(f0),CYes{})
def c_literal_24(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_23(f0),CYes{})
def c_literal_25(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_24(f0),CYes{})
def c_literal_26(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_25(f0),CYes{})
def c_literal_27(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_26(f0),CYes{})
def c_literal_28(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_27(f0),CYes{})
def c_literal_29(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_28(f0),CYes{})
def c_literal_30(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_29(f0),CYes{})
def c_literal_31(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_30(f0),CYes{})
def c_literal_32(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_31(f0),CYes{})
def c_literal_33(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_32(f0),CYes{})
def c_literal_34(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_33(f0),CYes{})
def c_literal_35(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_34(f0),CYes{})
def c_literal_36(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_35(f0),CYes{})
def c_literal_37(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_36(f0),CYes{})
def c_literal_38(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_37(f0),CYes{})
def c_literal_39(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_38(f0),CYes{})
def c_literal_40(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_39(f0),CYes{})
def c_literal_41(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_40(f0),CYes{})
def c_literal_42(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_41(f0),CYes{})
def c_literal_43(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_42(f0),CYes{})
def c_literal_44(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_43(f0),CYes{})
def c_literal_45(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_44(f0),CYes{})
def c_literal_46(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_45(f0),CYes{})
def c_literal_47(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_46(f0),CYes{})
def c_literal_48(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_47(f0),CYes{})
def c_literal_49(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_48(f0),CYes{})
def c_literal_50(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_49(f0),CYes{})
def c_literal_51(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_50(f0),CYes{})
def c_literal_52(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_51(f0),CYes{})
def c_literal_53(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_52(f0),CYes{})
def c_literal_54(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_53(f0),CYes{})
def c_literal_55(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_54(f0),CYes{})
def c_literal_56(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_55(f0),CYes{})
def c_literal_57(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_56(f0),CYes{})
def c_literal_58(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_57(f0),CYes{})
def c_literal_59(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_58(f0),CYes{})
def c_literal_60(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_59(f0),CYes{})
def c_literal_61(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_60(f0),CYes{})
def c_literal_62(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_61(f0),CYes{})
def c_literal_63(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_62(f0),CYes{})
def c_literal_64(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_63(f0),CYes{})
def c_observe() -> CObservation:
  c_literal_64(main())

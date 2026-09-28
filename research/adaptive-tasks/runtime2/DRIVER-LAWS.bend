import Base
import ./protocol.bend as P
import ./driver.bend as D

law zero_quantum:
  for code: List<&2,P.Command>
  for frame: D.Frame
  {D.run(0n,code,frame) == frame : D.Frame}

law halted_terminal:
  for fuel: Nat
  for code: List<&2,P.Command>
  for pc: U32
  for state: P.State
  {D.run(fuel,code,D.Frame{pc,2,state}) == D.Frame{pc,2,state} : D.Frame}

law faulted_terminal:
  for fuel: Nat
  for code: List<&2,P.Command>
  for pc: U32
  for state: P.State
  {D.run(fuel,code,D.Frame{pc,3,state}) == D.Frame{pc,3,state} : D.Frame}

law exhausted_resumes:
  for +pc: U32
  for +state: P.State
  {D.advance(pc,6,P.result(state,3,0)) == D.Frame{pc,1,P.result(state,3,0)} : D.Frame}

def config(count: U32) -> P.Config:
  P.Config{1,2,0,0,0,1,3,3,count}

def empty(count: U32) -> P.State:
  P.State{config(count),P.Store{1,0,0,[P.Free{}],[0,0],[]},[],0,0}

def leaf(count: U32, status: U32, reply: U32) -> P.State:
  P.State{config(count),P.Store{2,0,0,[P.Object{1,0,1,7,[]}],[1,0],[]},[],status,reply}

law branch_yes:
  {D.run(2n,[P.Command{1,0,0,7,0,0,0,0},P.Command{14,0,7,3,2,0,0,0},
    P.Command{16,0,0,0,0,0,0,0},P.Command{17,0,0,0,0,0,0,0}],D.initial(config(4))) ==
    D.Frame{3,1,leaf(4,0,0)} : D.Frame}

law branch_no:
  {D.run(2n,[P.Command{1,0,0,7,0,0,0,0},P.Command{14,0,9,3,2,0,0,0},
    P.Command{16,0,0,0,0,0,0,0},P.Command{17,0,0,0,0,0,0,0}],D.initial(config(4))) ==
    D.Frame{2,1,leaf(4,0,0)} : D.Frame}

law jump_checked:
  {D.run(1n,[P.Command{15,1,0,0,0,0,0,0},P.Command{17,0,0,0,0,0,0,0}],D.initial(config(2))) ==
    D.Frame{1,1,empty(2)} : D.Frame}

law yield_stops:
  {D.run(2n,[P.Command{17,0,0,0,0,0,0,0},P.Command{3,0,1,0,0,0,0,0}],D.initial(config(2))) ==
    D.Frame{1,1,empty(2)} : D.Frame}

law halt_result:
  {D.run(4n,[P.Command{1,0,0,7,0,0,0,0},P.Command{16,0,0,0,0,0,0,0}],D.initial(config(2))) ==
    D.Frame{1,2,leaf(2,0,7)} : D.Frame}

law falloff_fault:
  {D.run(2n,[P.Command{1,0,0,7,0,0,0,0}],D.initial(config(1))) ==
    D.Frame{1,3,leaf(1,5,0)} : D.Frame}

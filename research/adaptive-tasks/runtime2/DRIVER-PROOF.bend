import Base
import ./DRIVER-LAWS.bend as L
import ./protocol.bend as P

def L.zero_quantum(code,frame): {==}
def L.exhausted_resumes(pc,state):
  match state:
    case P.State{config,store,joins,status,reply}: {==}

def L.halted_terminal(fuel,code,pc,state):
  match fuel:
    case 0n: {==}
    case 1n+fuel: {==}

def L.faulted_terminal(fuel,code,pc,state):
  match fuel:
    case 0n: {==}
    case 1n+fuel: {==}

def L.branch_yes(): {==}
def L.branch_no(): {==}
def L.jump_checked(): {==}
def L.yield_stops(): {==}
def L.halt_result(): {==}
def L.falloff_fault(): {==}

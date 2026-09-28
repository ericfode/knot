import Base
import ./frontier.bend as F
import ./slot-model.bend as R
import ../../owned-store/protocol.bend as P

law zero_slice:
  for id: U32
  for pc: U32
  for value: U32
  for dest: U32
  for slot: U32
  for code: List<&2,U32>
  {F.execute_task(F.Task{id,3,pc,value,dest,slot,code},0) == F.Task{id,4,pc,value,dest,slot,code} : F.Task}
law offer_full:
  {F.offer(F.offer(F.initial(1),0),1) ==
    F.State{1,[F.Task{0,2,0,7,73,0,[0,1,2]},F.Task{1,1,0,9,41,1,[1,0,2]}],[0],3,1,1} : F.State}
law offer_duplicate:
  {F.offer(F.offer(F.initial(2),0),0) ==
    F.State{2,[F.Task{0,2,0,7,73,0,[0,1,2]},F.Task{1,1,0,9,41,1,[1,0,2]}],[0],4,2,0} : F.State}
law prepare_reverse:
  {F.prepare(F.Command{17,0,1},F.offer(F.offer(F.initial(2),0),1)) ==
    F.State{2,[F.Task{0,3,0,7,73,0,[0,1,2]},F.Task{1,3,0,9,41,1,[1,0,2]}],[1,0],0,0,0} : F.State}
law round_suspend:
  {F.round(F.Command{17,0,1},F.offer(F.offer(F.initial(2),0),1)) ==
    F.State{2,[F.Task{0,4,0,7,73,0,[0,1,2]},F.Task{1,4,0,9,41,1,[1,0,2]}],[],0,0,0} : F.State}
law round_wait:
  {F.round(F.Command{17,1,1},F.offer(F.offer(F.initial(2),0),1)) ==
    F.State{2,[F.Task{0,4,1,7,73,0,[0,1,2]},F.Task{1,5,1,9,41,1,[1,0,2]}],[],0,0,0} : F.State}

law unsupported_slot:
  for state: P.Snapshot
  {R.step(R.Command{99,0,0,0},state) == (state,"unsupported") : P.Snapshot & String}

law fault_retains:
  {F.round(F.Command{17,1,0},F.offer(F.initial_at(2,3,0),0)) ==
    F.State{2,[F.Task{0,7,3,7,73,0,[0,1,2]},F.Task{1,1,0,9,41,1,[1,0,2]}],[0],5,6,0} : F.State}

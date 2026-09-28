import Base

# Numeric phases are the record ABI. Each task has exactly one phase owner.
type Task is Data:
  Task{id: U32, phase: U32, pc: U32, value: U32, dest: U32, slot: U32, code: List<&2,U32>}
type State is Data:
  State{capacity: U32, tasks: List<&2,Task>, queue: List<&2,U32>, status: U32, reason: U32, reply: U32}
type Command is Data:
  Command{op: U32, a: U32, b: U32}

def phase(t: Task, p: U32) -> Task:
  match t:
    case Task{id,old,pc,value,dest,slot,code}: Task{id,p,pc,value,dest,slot,code}

def mark(tasks: List<&2,Task>, +id: U32, +p: U32) -> List<&2,Task>:
  match tasks:
    case Nil{}: Nil{}
    case Con{+t,tail}:
      match t:
        case Task{key,old,pc,value,dest,slot,code}:
          Con{Bool.pick(Task,U32.is_eq(key,id),phase(t,p),t),mark(tail,id,p)}

def find(tasks: List<&2,Task>, +id: U32) -> Maybe<&2,Task>:
  match tasks:
    case Nil{}: None{}
    case Con{+t,tail}:
      match t:
        case Task{key,p,pc,value,dest,slot,code}:
          Bool.pick(Maybe<&2,Task>,U32.is_eq(key,id),Some{t},find(tail,id))

def append(queue: List<&2,U32>, +id: U32) -> List<&2,U32>:
  match queue:
    case Nil{}: [id]
    case Con{head,tail}: Con{head,append(tail,id)}

def length(queue: List<&2,U32>) -> U32:
  match queue:
    case Nil{}: 0
    case Con{head,tail}: U32.add(1,length(tail))

def result(s: State, status: U32, reason: U32, reply: U32) -> State:
  match s:
    case State{cap,tasks,queue,old,why,value}: State{cap,tasks,queue,status,reason,reply}

def offer_space(space: Bool, +s: State, +id: U32) -> State:
  match space s:
    case False{} _: result(s,3,1,id)
    case True{} State{cap,tasks,queue,status,reason,reply}:
      State{cap,mark(tasks,id,2),append(queue,id),0,0,id}

def offer_ready(ready: Bool, +s: State, id: U32) -> State:
  match ready s:
    case False{} _: result(s,4,2,id)
    case True{} State{cap,tasks,queue,status,reason,reply}:
      offer_space(U32.is_lt(length(queue),cap),s,id)

def offer_task(found: Maybe<&2,Task>, s: State, id: U32) -> State:
  match found:
    case None{}: result(s,4,5,id)
    case Some{Task{key,+p,pc,value,dest,slot,code}}:
      offer_ready(Bool.or(U32.is_eq(p,1),U32.is_eq(p,4)),s,id)

def offer(+s: State, +id: U32) -> State:
  match s:
    case State{cap,tasks,queue,status,reason,reply}: offer_task(find(tasks,id),s,id)

def wake_ready(waiting: Bool, +s: State, +id: U32) -> State:
  match waiting s:
    case False{} _: result(s,4,2,id)
    case True{} State{cap,tasks,queue,status,reason,reply}: State{cap,mark(tasks,id,1),queue,0,0,id}

def wake_task(found: Maybe<&2,Task>, s: State, id: U32) -> State:
  match found:
    case None{}: result(s,4,5,id)
    case Some{Task{key,p,pc,value,dest,slot,code}}: wake_ready(U32.is_eq(p,5),s,id)

def wake(+s: State, +id: U32) -> State:
  match s:
    case State{cap,tasks,queue,status,reason,reply}: wake_task(find(tasks,id),s,id)

def running(tasks: List<&2,Task>) -> List<&2,Task>:
  match tasks:
    case Nil{}: Nil{}
    case Con{+t,tail}:
      match t:
        case Task{id,p,pc,value,dest,slot,code}:
          Con{Bool.pick(Task,U32.is_eq(p,2),phase(t,3),t),running(tail)}

def admit(valid: Bool, s: State, reverse: U32) -> State:
  match valid s:
    case False{} _: result(s,1,3,0)
    case True{} State{cap,tasks,+queue,status,reason,reply}:
      State{cap,running(tasks),Bool.pick(List<&2,U32>,U32.is_eq(reverse,1),List.reverse(&2,U32,queue),queue),0,0,0}

def prepare(command: Command, +s: State) -> State:
  match command:
    case Command{16,a,b}: offer(s,a)
    case Command{17,a,+b}: admit(Bool.and(U32.is_le(a,1),U32.is_le(b,1)),s,b)
    case Command{18,a,b}: wake(s,a)
    case Command{op,a,b}: result(s,2,4,0)

def instruction(pc: Nat, code: List<&2,U32>) -> U32:
  match pc code:
    case 0n Nil{}: 4294967295
    case 0n Con{head,tail}: head
    case 1n+n Nil{}: 4294967295
    case 1n+n Con{head,tail}: instruction(n,tail)

def advance(op: U32, t: Task) -> Task:
  match op t:
    case 0 Task{id,p,pc,value,dest,slot,code}: Task{id,4,U32.add(pc,1),value,dest,slot,code}
    case 1 Task{id,p,pc,value,dest,slot,code}: Task{id,5,U32.add(pc,1),value,dest,slot,code}
    case 2 Task{id,p,pc,value,dest,slot,code}: Task{id,6,U32.add(pc,1),value,dest,slot,code}
    case _ _: phase(t,7)

def execute_task(t: Task, quantum: U32) -> Task:
  match t quantum:
    case Task{id,3,pc,value,dest,slot,code} 0: Task{id,4,pc,value,dest,slot,code}
    case Task{id,3,+pc,value,dest,slot,+code} _:
      advance(instruction(U32.to_nat(pc),code),Task{id,3,pc,value,dest,slot,code})
    case _ _: t

def execute_tasks(tasks: List<&2,Task>, +quantum: U32) -> List<&2,Task>:
  match tasks:
    case Nil{}: Nil{}
    case Con{head,tail}: Con{execute_task(head,quantum),execute_tasks(tail,quantum)}

def execute(command: Command, s: State) -> State:
  match command s:
    case Command{17,quantum,reverse} State{cap,tasks,queue,0,reason,reply}:
      State{cap,execute_tasks(tasks,quantum),queue,0,reason,reply}
    case _ _: s

def fault(tasks: List<&2,Task>) -> Bool:
  match tasks:
    case Nil{}: False{}
    case Con{Task{id,p,pc,value,dest,slot,code},tail}: Bool.or(U32.is_eq(p,7),fault(tail))

def finish(failed: Bool, s: State) -> State:
  match failed s:
    case True{} _: result(s,5,6,0)
    case False{} State{cap,tasks,queue,status,reason,reply}: State{cap,tasks,Nil{},0,reason,reply}

def publish(command: Command, s: State) -> State:
  match command s:
    case Command{17,a,b} State{cap,+tasks,queue,0,reason,reply}:
      finish(fault(tasks),State{cap,tasks,queue,0,reason,reply})
    case _ _: s

def round(+command: Command, s: State) -> State:
  publish(command,execute(command,prepare(command,s)))

def run(commands: List<&2,Command>, s: State) -> State:
  match commands:
    case Nil{}: s
    case Con{head,tail}: run(tail,round(head,s))

def task_words(t: Task) -> String:
  match t:
    case Task{id,p,pc,value,dest,slot,code}: List.show(~&2,~U32,~U32.show,[id,p,pc,value,dest,slot])

def observation(s: State) -> String:
  match s:
    case State{cap,tasks,queue,status,reason,reply}:
      String.concat(["[",U32.show(status),",",U32.show(reason),",",U32.show(reply),",",
        List.show(~&2,~U32,~U32.show,queue),",",List.show(~&2,~Task,~task_words,tasks),"]"])

def initial_at(capacity: U32, first: U32, second: U32) -> State:
  State{capacity,[Task{0,1,first,7,73,0,[0,1,2]},Task{1,1,second,9,41,1,[1,0,2]}],Nil{},0,0,0}

def initial(capacity: U32) -> State:
  initial_at(capacity,0,0)

def trace(+command: Command, s: State) -> String:
  +prepared = prepare(command,s)
  +work = execute(command,prepared)
  String.concat(["[",observation(prepared),",",observation(work),",",observation(publish(command,work)),"]"])

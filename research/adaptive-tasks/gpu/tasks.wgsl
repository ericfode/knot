// Bounded tree-task probe. All cross-invocation reads use an earlier dispatch.
// States: dormant=0, enter=1, run=2, waiting=3, frame=4, done=5, retired=6.
struct Op {
  kind:u32, left:u32, right:u32, seed:u32,
  ticks:u32, factor:u32, bias:u32, parent:u32,
  slot:u32, pad0:u32, pad1:u32, pad2:u32,
}
struct Task {
  state:u32, remaining:u32, value:u32, left_value:u32,
  right_value:u32, mask:u32, last_worker:u32, moves:u32,
  runs:u32, steps:u32, destination:u32, slot:u32,
  factor:u32, bias:u32, completed_round:u32, pad:u32,
}
struct Params {
  count:u32, quantum:u32, capacity:u32, root:u32,
  round:u32, reverse:u32, adaptive:u32, pad:u32,
}
struct Control { count:atomic<u32>, error:atomic<u32>, pad0:u32, pad1:u32 }
@group(0) @binding(0) var<storage,read> ops:array<Op>;
@group(0) @binding(1) var<storage,read> previous:array<Task>;
@group(0) @binding(2) var<storage,read_write> work:array<Task>;
@group(0) @binding(3) var<storage,read_write> frontier:array<u32>;
@group(0) @binding(4) var<storage,read_write> control:Control;
@group(0) @binding(5) var<uniform> params:Params;
@group(0) @binding(6) var<storage,read_write> next:array<Task>;

fn runnable(s:u32) -> bool { return s==1u || s==2u || s==4u; }

@compute @workgroup_size(64)
fn prepare(@builtin(global_invocation_id) global:vec3<u32>) {
  if (global.x>=params.count) { return; }
  var id=global.x;
  if (params.reverse!=0u) { id=params.count-1u-id; }
  var t=previous[id];
  let op=ops[id];
  // Activating a child observes its parent's waiting state from an earlier phase.
  if (t.state==0u && op.parent!=0xffffffffu) {
    if (previous[op.parent].state==3u) { t.state=1u; }
  }
  work[id]=t;
  if (runnable(t.state)) {
    // count<=validated node count<=4096: this reservation cannot wrap.
    let at=atomicAdd(&control.count,1u);
    if (at>=params.capacity) {
      atomicStore(&control.error,1u);
    } else {
      frontier[at]=id;
    }
  }
}

@compute @workgroup_size(64)
fn execute(@builtin(global_invocation_id) global:vec3<u32>) {
  if (atomicLoad(&control.error)!=0u) { return; }
  var id=global.x;
  if (params.adaptive!=0u) {
    if (global.x>=atomicLoad(&control.count)) { return; }
    id=frontier[global.x];
  } else if (id>=params.count) { return; }
  var t=work[id];
  if (!runnable(t.state)) { return; }
  // This records logical dispatch-lane changes, not physical GPU-core identity.
  if (t.last_worker!=0xffffffffu && t.last_worker!=global.x) { t.moves+=1u; }
  t.last_worker=global.x;
  t.runs+=1u;
  let op=ops[id];
  for (var k=0u; k<params.quantum; k+=1u) {
    if (t.state==1u) {
      t.steps+=1u;
      if (op.kind==0u) {
        t.state=2u; t.remaining=op.ticks; t.value=op.seed;
      } else {
        t.state=3u; t.factor=op.factor; t.bias=op.bias;
        break;
      }
    } else if (t.state==2u) {
      t.steps+=1u;
      if (t.remaining!=0u) {
        t.value=t.value*1664525u+1013904223u;
        t.remaining-=1u;
      } else {
        t.state=5u; t.completed_round=params.round;
        break;
      }
    } else if (t.state==4u) {
      t.steps+=1u;
      if (op.kind==1u) {
        t.value=t.left_value*31u+t.right_value;
      } else {
        t.value=t.left_value*t.factor+t.bias;
      }
      t.left_value=0u; t.right_value=0u;
      t.remaining=0u; t.state=2u;
    } else { break; }
  }
  work[id]=t;
}

@compute @workgroup_size(64)
fn join_phase(@builtin(global_invocation_id) global:vec3<u32>) {
  let id=global.x;
  if (id>=params.count) { return; }
  var t=work[id];
  let op=ops[id];
  if (atomicLoad(&control.error)!=0u) { next[id]=t; return; }
  if (t.state==3u) {
    // Only this invocation owns this join. Mask prevents duplicate collection.
    if ((t.mask & 1u)==0u && work[op.left].state==5u) {
      t.left_value=work[op.left].value; t.mask|=1u;
    }
    if (op.kind==1u && (t.mask & 2u)==0u && work[op.right].state==5u) {
      t.right_value=work[op.right].value; t.mask|=2u;
    }
    let required=select(1u,3u,op.kind==1u);
    if (t.mask==required) { t.state=4u; }
  } else if (t.state==5u && op.parent!=0xffffffffu) {
    // The parent reads this immutable work snapshot in the same join phase.
    // It gains the payload as this owner retires, atomically at the phase boundary.
    let parent=work[op.parent];
    let bit=1u<<op.slot;
    if (parent.state==3u && (parent.mask & bit)==0u) {
      t.state=6u; t.value=0u;
    }
  }
  next[id]=t;
}

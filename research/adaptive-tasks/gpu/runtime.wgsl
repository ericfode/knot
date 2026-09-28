// knot-device-records-1: bounded qualification, at most two owning records.
struct Words { w: array<u32,36> }
struct Command { op: u32, a: u32, b: u32, c: u32, pad: vec4<u32> }
@group(0) @binding(0) var<storage,read> before: Words;
@group(0) @binding(1) var<storage,read_write> prepared: Words;
@group(0) @binding(2) var<storage,read_write> work: Words;
@group(0) @binding(3) var<storage,read_write> after: Words;
@group(0) @binding(4) var<uniform> command: Command;
@group(0) @binding(5) var<storage,read> program: array<u32>;
const CANARY=0xdeadbeefu;

fn reply(status: u32, reason: u32, a: u32, b: u32, c: u32) {
  prepared.w[7]=status; prepared.w[8]=reason;
  prepared.w[9]=a; prepared.w[10]=b; prepared.w[11]=c;
}
fn store_fail(reason: u32, incoming: u32) {
  var status=4u;
  if (reason==1u || reason==7u) { status=3u; }
  reply(status,reason,incoming,0u,0u);
}
fn insert(slot: u32, value: u32) {
  if (slot>=prepared.w[4]) { store_fail(2u,value); return; }
  let base=16u+8u*slot;
  if (prepared.w[base]==2u) { store_fail(7u,value); return; }
  if (prepared.w[base]==1u) { store_fail(6u,value); return; }
  prepared.w[base]=1u; prepared.w[base+2u]=value;
  let count=prepared.w[6];
  var found=false;
  for (var i=0u;i<count;i++) {
    if (prepared.w[32u+i]==slot) { found=true; }
    if (found && i+1u<count) { prepared.w[32u+i]=prepared.w[33u+i]; }
  }
  prepared.w[6]=count-1u; prepared.w[31u+count]=CANARY;
  reply(0u,0u,prepared.w[2],slot,prepared.w[base+1u]);
}
fn extract() {
  let arena=command.a; let slot=command.b; let generation=command.c;
  if (arena!=prepared.w[2]) { store_fail(3u,0u); return; }
  if (slot>=prepared.w[4]) { store_fail(2u,0u); return; }
  let base=16u+8u*slot;
  let state=prepared.w[base]; let current=prepared.w[base+1u];
  if (state==2u) { store_fail(7u,0u); return; }
  if (generation!=current) { store_fail(4u,0u); return; }
  if (state==0u) { store_fail(5u,0u); return; }
  let value=prepared.w[base+2u];
  prepared.w[base+2u]=0u;
  if (current<prepared.w[5]) {
    prepared.w[base]=0u; prepared.w[base+1u]=current+1u;
    let count=prepared.w[6];
    for (var i=count;i>0u;i--) { prepared.w[32u+i]=prepared.w[31u+i]; }
    prepared.w[32]=slot; prepared.w[6]=count+1u;
  } else {
    prepared.w[base]=2u;
  }
  reply(0u,0u,value,0u,0u);
}
fn store_command() {
  switch command.op {
    case 1u: { insert(command.a,command.b); }
    case 2u,3u: { extract(); }
    case 4u: {
      if (prepared.w[6]==0u) { store_fail(1u,command.a); }
      else { insert(prepared.w[32],command.a); }
    }
    default: { reply(2u,4u,0u,0u,0u); }
  }
}
fn frontier_command() {
  let id=command.a;
  if (command.op==16u || command.op==18u) {
    if (id>=prepared.w[4]) { reply(4u,5u,id,0u,0u); return; }
    let base=16u+8u*id; let phase=prepared.w[base+1u];
    if (command.op==18u) {
      if (phase!=5u) { reply(4u,2u,id,0u,0u); return; }
      prepared.w[base+1u]=1u; reply(0u,0u,id,0u,0u); return;
    }
    if (phase!=1u && phase!=4u) { reply(4u,2u,id,0u,0u); return; }
    let count=prepared.w[6];
    if (count>=prepared.w[3]) { reply(3u,1u,id,0u,0u); return; }
    prepared.w[32u+count]=id; prepared.w[6]=count+1u;
    prepared.w[base+1u]=2u; reply(0u,0u,id,0u,0u); return;
  }
  if (command.op!=17u) { reply(2u,4u,0u,0u,0u); return; }
  if (command.a>1u || command.b>1u) { reply(1u,3u,0u,0u,0u); return; }
  let count=prepared.w[6];
  for (var i=0u;i<count;i++) {
    var source=i;
    if (command.b==1u) { source=count-1u-i; }
    let task=before.w[32u+source];
    prepared.w[32u+i]=task;
    prepared.w[17u+8u*task]=3u;
  }
}

// The scheduler alone owns admission and compaction. Execute starts later.
@compute @workgroup_size(1)
fn prepare() {
  for (var i=0u;i<36u;i++) { prepared.w[i]=before.w[i]; }
  reply(0u,0u,0u,0u,0u);
  if (before.w[1]==4u) { store_command(); }
  else { frontier_command(); }
}

// One writer per task; each invocation reads the complete prepared snapshot.
@compute @workgroup_size(64)
fn execute(@builtin(global_invocation_id) gid: vec3<u32>) {
  let id=gid.x;
  if (id==0u) {
    for (var i=0u;i<16u;i++) { work.w[i]=prepared.w[i]; }
    for (var i=32u;i<36u;i++) { work.w[i]=prepared.w[i]; }
  }
  if (id>=2u) { return; }
  let base=16u+8u*id;
  for (var i=0u;i<8u;i++) { work.w[base+i]=prepared.w[base+i]; }
  if (prepared.w[1]!=6u || command.op!=17u || prepared.w[7]!=0u) { return; }
  if (prepared.w[base+1u]!=3u) { return; }
  if (command.a==0u) { work.w[base+1u]=4u; return; }
  let pc=prepared.w[base+2u];
  if (pc>=prepared.w[base+7u]) { work.w[base+1u]=7u; return; }
  let op=program[prepared.w[base+6u]+pc];
  switch op {
    case 0u: { work.w[base+1u]=4u; }
    case 1u: { work.w[base+1u]=5u; }
    case 2u: { work.w[base+1u]=6u; }
    default: { work.w[base+1u]=7u; return; }
  }
  work.w[base+2u]=pc+1u;
}

@compute @workgroup_size(1)
fn publish() {
  for (var i=0u;i<36u;i++) { after.w[i]=work.w[i]; }
  if (work.w[1]==6u && command.op==17u && work.w[7]==0u) {
    for (var id=0u;id<work.w[4];id++) {
      if (work.w[17u+8u*id]==7u) {
        after.w[7]=5u; after.w[8]=6u; return;
      }
    }
    after.w[6]=0u;
    for (var i=0u;i<work.w[3];i++) { after.w[32u+i]=CANARY; }
  }
}

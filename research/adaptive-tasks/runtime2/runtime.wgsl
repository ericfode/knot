// One owning invocation mutates work; a later dispatch publishes it.
struct Words { w: array<u32> }
struct Step { index: u32, pad0: u32, pad1: u32, pad2: u32 }
@group(0) @binding(0) var<storage,read> before: Words;
@group(0) @binding(1) var<storage,read_write> work: Words;
@group(0) @binding(2) var<storage,read_write> after: Words;
@group(0) @binding(3) var<uniform> step: Step;
@group(0) @binding(4) var<storage,read> program: Words;
var<private> instruction: u32;

const NONE=0xffffffffu;
const GUARD=0xdeadbeefu;

fn fail(status: u32) { work.w[21]=status; }
fn range(first: u32, count: u32, limit: u32) -> bool {
  return first<=limit && count<=limit-first;
}
fn fits(base: u32, count: u32, stride: u32, limit: u32) -> bool {
  return stride>0u && base<=limit && count<=(limit-base)/stride;
}
fn inside(index: u32, first: u32, count: u32) -> bool {
  return index>=first && index-first<count;
}
fn intersects(a: u32, na: u32, b: u32, nb: u32) -> bool {
  return na>0u && nb>0u && (inside(a,b,nb) || inside(b,a,na));
}
fn arg(index: u32) -> u32 { return program.w[instruction*8u+index]; }
fn capture(index: u32) -> u32 { return work.w[12]+index; }
fn join(index: u32) -> u32 { return work.w[14]+index*work.w[16]; }
fn object(identity: u32) -> u32 {
  if (identity==0u) { return NONE; }
  for (var i=0u;i<work.w[3];i++) {
    let base=work.w[11]+i*work.w[15];
    if (work.w[base]==identity) { return base; }
  }
  return NONE;
}
fn empty_object() -> u32 {
  for (var i=0u;i<work.w[3];i++) {
    let base=work.w[11]+i*work.w[15];
    if (work.w[base]==0u) { return base; }
  }
  return NONE;
}
fn captured(index: u32) -> u32 {
  if (index>=work.w[4]) { return NONE; }
  return object(work.w[capture(index)]);
}
fn clear_object(base: u32) {
  for (var i=0u;i<work.w[15];i++) { work.w[base+i]=0u; }
  work.w[19]+=1u;
}
fn push(identity: u32) {
  work.w[work.w[13]+work.w[20]]=identity;
  work.w[20]+=1u;
}

fn layout_valid() -> bool {
  let words=arrayLength(&work.w);
  if (work.w[2]!=words || work.w[7]>NONE-8u) { return false; }
  if (work.w[8]==0u || work.w[9]==0u || work.w[10]==0u) { return false; }
  if (work.w[15]!=5u+work.w[7] || work.w[16]!=8u+work.w[7]) { return false; }
  var cursor=32u;
  for (var segment=0u;segment<4u;segment++) {
    var count=work.w[3u+segment];
    var stride=1u;
    if (segment==0u) { stride=work.w[15]; }
    if (segment==3u) { stride=work.w[16]; }
    if (work.w[11u+segment]!=cursor || !fits(cursor,count,stride,words)) { return false; }
    cursor+=count*stride;
    if (cursor>=words || work.w[cursor]!=GUARD) { return false; }
    cursor+=1u;
  }
  if (cursor!=words || work.w[20]>work.w[5]) { return false; }
  if (work.w[23]>arrayLength(&program.w)/8u) { return false; }
  if (work.w[25]>3u) { return false; }
  for (var i=26u;i<32u;i++) { if (work.w[i]!=0u) { return false; } }
  return true;
}

fn construct(dst: u32, kind: u32, tag: u32, first: u32, count: u32) {
  if (dst>=work.w[4] || kind>1u || !range(first,count,work.w[4]) || inside(dst,first,count)) { fail(1u); return; }
  if (work.w[capture(dst)]!=0u) { fail(1u); return; }
  for (var i=0u;i<count;i++) {
    let child=captured(first+i);
    if (child==NONE) { fail(1u); return; }
    if (kind==1u && work.w[child+1u]!=1u) { fail(1u); return; }
  }
  if (count>work.w[7]) { fail(3u); return; }
  let base=empty_object();
  let identity=work.w[17];
  if (base==NONE || identity==0u) { fail(3u); return; }
  work.w[base]=identity; work.w[base+1u]=kind; work.w[base+2u]=1u;
  work.w[base+3u]=count; work.w[base+4u]=tag;
  for (var i=0u;i<count;i++) {
    work.w[base+5u+i]=work.w[capture(first+i)];
    work.w[capture(first+i)]=0u;
  }
  work.w[capture(dst)]=identity;
  if (identity==work.w[9]) { work.w[17]=0u; }
  else { work.w[17]=identity+1u; }
}

fn share(src: u32, dst: u32) {
  let base=captured(src);
  if (base==NONE || dst>=work.w[4]) { fail(1u); return; }
  if (work.w[capture(dst)]!=0u) { fail(1u); return; }
  if (work.w[base+1u]!=1u) { fail(2u); return; }
  if (work.w[base+2u]>=work.w[8]) { fail(3u); return; }
  work.w[base+2u]+=1u;
  work.w[capture(dst)]=work.w[capture(src)];
}

fn transfer(src: u32, dst: u32) {
  if (captured(src)==NONE || dst>=work.w[4]) { fail(1u); return; }
  if (work.w[capture(dst)]!=0u) { fail(1u); return; }
  work.w[capture(dst)]=work.w[capture(src)];
  work.w[capture(src)]=0u; // move consumes its unique source slot
}

fn open(src: u32, first: u32, count: u32) {
  if (src>=work.w[4] || !range(first,count,work.w[4]) || inside(src,first,count)) { fail(1u); return; }
  let base=captured(src);
  if (base==NONE) { fail(1u); return; }
  if (count!=work.w[base+3u]) { fail(1u); return; }
  for (var i=0u;i<count;i++) {
    if (work.w[capture(first+i)]!=0u) { fail(1u); return; }
  }
  if (work.w[18]!=0u) { fail(3u); return; }
  let counted=work.w[base+1u]==1u && work.w[base+2u]>1u;
  if (counted) {
    // Repeated child identities reserve all increments before publishing any.
    for (var i=0u;i<count;i++) {
      let identity=work.w[base+5u+i];
      let child=object(identity);
      if (child==NONE || work.w[child+1u]!=1u) { fail(5u); return; }
      var copies=0u;
      for (var j=0u;j<count;j++) {
        if (work.w[base+5u+j]==identity) { copies+=1u; }
      }
      if (work.w[child+2u]>work.w[8] || copies>work.w[8]-work.w[child+2u]) { fail(3u); return; }
    }
  }
  for (var i=0u;i<count;i++) {
    let identity=work.w[base+5u+i];
    work.w[capture(first+i)]=identity;
    if (counted) { work.w[object(identity)+2u]+=1u; }
  }
  work.w[capture(src)]=0u;
  if (counted) { work.w[base+2u]-=1u; }
  else { clear_object(base); }
}

fn release(src: u32) {
  if (captured(src)==NONE) { fail(1u); return; }
  if (work.w[20]>=work.w[5]) { fail(3u); return; }
  push(work.w[capture(src)]);
  work.w[capture(src)]=0u;
}

fn clean(budget: u32) {
  if (work.w[18]!=0u) { fail(3u); return; }
  for (var used=0u;used<budget;used++) {
    let pending=work.w[20];
    if (pending==0u) { return; }
    let top=work.w[13]+pending-1u;
    let base=object(work.w[top]);
    if (base==NONE) { fail(5u); return; }
    let counted=work.w[base+1u]==1u && work.w[base+2u]>1u;
    let count=work.w[base+3u];
    if (!counted && count>work.w[5]-(pending-1u)) { fail(3u); return; }
    work.w[top]=0u; work.w[20]=pending-1u;
    if (counted) {
      work.w[base+2u]=work.w[base+2u]-1u; // one pending edge releases one count
    } else {
      for (var i=0u;i<count;i++) { push(work.w[base+5u+i]); }
      clear_object(base);
    }
  }
  if (work.w[20]!=0u) { fail(3u); }
}

fn start(index: u32, count: u32, code: u32, first: u32, captures: u32) {
  if (index>=work.w[6] || code>=work.w[23] || !range(first,captures,work.w[4])) { fail(1u); return; }
  let base=join(index);
  let state=work.w[base+1u];
  if (state==1u || state==2u) { fail(1u); return; }
  for (var i=0u;i<work.w[6];i++) {
    if (i==index) { continue; }
    let other=join(i);
    let in_flight=work.w[other+1u]==1u || work.w[other+1u]==2u;
    if (in_flight && intersects(first,captures,work.w[other+6u],work.w[other+7u])) { fail(1u); return; }
  }
  if (count>work.w[7] || work.w[base]>=work.w[10]) { fail(3u); return; }
  work.w[base]+=1u; work.w[base+1u]=1u; work.w[base+2u]=count;
  work.w[base+3u]=0u; work.w[base+5u]=code;
  work.w[base+6u]=first; work.w[base+7u]=captures;
  for (var i=0u;i<work.w[7];i++) { work.w[base+8u+i]=0u; }
  if (count==0u) { work.w[base+1u]=2u; work.w[base+4u]+=1u; }
}

fn deliver(index: u32, attempt: u32, slot: u32, src: u32) {
  if (index>=work.w[6]) { fail(1u); return; }
  let base=join(index);
  if (attempt!=work.w[base] || work.w[base+1u]!=1u) { fail(1u); return; }
  if (slot>=work.w[base+2u] || captured(src)==NONE) { fail(1u); return; }
  if (work.w[base+8u+slot]!=0u) { fail(1u); return; }
  work.w[base+8u+slot]=work.w[capture(src)];
  work.w[capture(src)]=0u;
  work.w[base+3u]+=1u;
  if (work.w[base+3u]==work.w[base+2u]) {
    work.w[base+1u]=2u;
    work.w[base+4u]+=1u; // the transition to ready completes once
  }
}

fn cancel(index: u32, attempt: u32) {
  if (index>=work.w[6]) { fail(1u); return; }
  let base=join(index);
  let state=work.w[base+1u];
  if (attempt!=work.w[base] || (state!=1u && state!=2u)) { fail(1u); return; }
  let first=work.w[base+6u]; let captures=work.w[base+7u];
  let count=work.w[base+2u];
  var releases=0u;
  for (var i=0u;i<captures;i++) {
    if (work.w[capture(first+i)]!=0u) { releases+=1u; }
  }
  for (var i=0u;i<count;i++) {
    if (work.w[base+8u+i]!=0u) { releases+=1u; }
  }
  if (releases>work.w[5]-work.w[20]) { fail(3u); return; }
  for (var i=0u;i<captures;i++) {
    let slot=capture(first+i);
    if (work.w[slot]!=0u) { push(work.w[slot]); work.w[slot]=0u; }
  }
  for (var i=0u;i<count;i++) {
    let slot=base+8u+i;
    if (work.w[slot]!=0u) { push(work.w[slot]); work.w[slot]=0u; }
  }
  work.w[base+1u]=3u; work.w[base+3u]=0u;
}

fn resume(index: u32, attempt: u32, first: u32) {
  if (index>=work.w[6]) { fail(1u); return; }
  let base=join(index); let count=work.w[base+2u];
  if (attempt!=work.w[base] || work.w[base+1u]!=2u) { fail(1u); return; }
  if (!range(first,count,work.w[4])) { fail(1u); return; }
  for (var i=0u;i<count;i++) {
    if (work.w[capture(first+i)]!=0u) { fail(1u); return; }
  }
  for (var i=0u;i<count;i++) {
    work.w[capture(first+i)]=work.w[base+8u+i];
    work.w[base+8u+i]=0u;
  }
  work.w[base+1u]=4u; work.w[22]=work.w[base+5u];
}

fn interpret() {
  let op=arg(0u);
  var operands=0u;
  switch op {
    case 1u,8u: { operands=5u; }
    case 9u,13u: { operands=4u; }
    case 4u,11u: { operands=3u; }
    case 2u,3u,10u: { operands=2u; }
    case 5u,6u,7u,12u: { operands=1u; }
    default: { fail(2u); return; }
  }
  for (var i=operands+1u;i<8u;i++) {
    if (arg(i)!=0u) { fail(1u); return; }
  }
  switch op {
    case 1u: { construct(arg(1u),arg(2u),arg(3u),arg(4u),arg(5u)); }
    case 2u: { share(arg(1u),arg(2u)); }
    case 3u: { transfer(arg(1u),arg(2u)); }
    case 4u: { open(arg(1u),arg(2u),arg(3u)); }
    case 5u: { release(arg(1u)); }
    case 6u: { clean(arg(1u)); }
    case 7u: { work.w[18]=arg(1u); }
    case 8u: { start(arg(1u),arg(2u),arg(3u),arg(4u),arg(5u)); }
    case 9u: { deliver(arg(1u),arg(2u),arg(3u),arg(4u)); }
    case 10u: { cancel(arg(1u),arg(2u)); }
    case 11u: { resume(arg(1u),arg(2u),arg(3u)); }
    case 12u: {
      let base=captured(arg(1u));
      if (base==NONE) { fail(1u); } else { work.w[22]=work.w[base+4u]; }
    }
    case 13u: {
      let base=arg(1u); let count=arg(2u); let stride=arg(3u); let limit=arg(4u);
      if (stride==0u) { fail(1u); }
      else if (!fits(base,count,stride,limit)) { fail(3u); }
      else { work.w[22]=base+count*stride; }
    }
    default: { fail(5u); }
  }
}

@compute @workgroup_size(1)
fn execute() {
  let count=arrayLength(&before.w);
  for (var i=0u;i<count;i++) { work.w[i]=before.w[i]; }
  if (count<32u) { return; }
  work.w[21]=0u; work.w[22]=0u;
  if (work.w[0]!=2u || work.w[1]!=2u) { fail(2u); return; }
  if (!layout_valid()) { fail(1u); return; }
  if (step.index>=work.w[23] || step.pad0!=0u || step.pad1!=0u || step.pad2!=0u) { fail(1u); return; }
  instruction=step.index;
  interpret();
}

fn control(op: u32) {
  var operands=0u;
  if (op==14u) { operands=4u; }
  else if (op==15u || op==16u) { operands=1u; }
  for (var i=operands+1u;i<8u;i++) {
    if (arg(i)!=0u) { fail(1u); return; }
  }
  switch op {
    case 14u: {
      let base=captured(arg(1u));
      if (base==NONE || arg(3u)>=work.w[23] || arg(4u)>=work.w[23]) { fail(1u); return; }
      work.w[24]=select(arg(4u),arg(3u),work.w[base+4u]==arg(2u));
    }
    case 15u: {
      if (arg(1u)>=work.w[23]) { fail(1u); return; }
      work.w[24]=arg(1u);
    }
    case 16u: {
      let base=captured(arg(1u));
      if (base==NONE) { fail(1u); return; }
      work.w[22]=work.w[base+4u]; work.w[25]=2u;
    }
    case 17u: { work.w[24]+=1u; work.w[25]=1u; }
    default: { fail(2u); }
  }
}

@compute @workgroup_size(1)
fn run() {
  let count=arrayLength(&before.w);
  for (var i=0u;i<count;i++) { work.w[i]=before.w[i]; }
  if (count<32u) { return; }
  if (step.index==0u || work.w[25]==2u || work.w[25]==3u) { return; }
  work.w[21]=0u; work.w[22]=0u;
  if (work.w[0]!=2u || work.w[1]!=2u) { fail(2u); work.w[25]=3u; return; }
  if (!layout_valid() || step.pad0!=0u || step.pad1!=0u || step.pad2!=0u) { fail(1u); work.w[25]=3u; return; }
  work.w[25]=0u;
  for (var used=0u;used<step.index;used++) {
    work.w[21]=0u; work.w[22]=0u;
    instruction=work.w[24];
    if (instruction>=work.w[23]) { fail(5u); work.w[25]=3u; return; }
    let op=arg(0u);
    if (op>=14u && op<=17u) { control(op); }
    else { interpret(); }
    if (work.w[21]!=0u) { work.w[25]=select(3u,1u,work.w[21]==3u); return; }
    if (op==11u) { work.w[24]=work.w[22]; }
    else if (op<14u || op>17u) { work.w[24]+=1u; }
    if (work.w[25]!=0u) { return; }
  }
  work.w[25]=1u;
}

@compute @workgroup_size(1)
fn publish() {
  for (var i=0u;i<arrayLength(&work.w);i++) { after.w[i]=work.w[i]; }
}

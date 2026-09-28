from pathlib import Path
import json
out=Path('vm/golden');out.mkdir(exist_ok=True)
flag='type Flag is Data:\n  Off{}\n  On{}\n\n'
cases=[]
def put(name,source,expected,lane='literals',features=(),seed_lane=None):
 p=out/(name+'.bend');p.write_text(source)
 cases.append(dict(name=name,source=str(p),lane=lane,seed_stdout=expected+'\n',features=list(features)))
 if seed_lane: cases[-1]['seed_lane']=seed_lane
def simple(name,defs,body,expected='On{}',features=()):
 put(name,flag+defs+'def main() -> Flag:\n  '+body+'\n',expected,features=features)
simple('value-off','','Off{}','Off{}',('Value',))
simple('value-on','','On{}',features=('Value',))
simple('reference','def id(x: Flag) -> Flag:\n  x\n\n','id(On{})',features=('Reference','Application'))
simple('nested-call','def id(x: Flag) -> Flag:\n  x\n\n','id(id(On{}))',features=('Application',))
simple('let','', 'x : Flag = On{}\n  x',features=('Let','Reference'))
simple('shadow','', 'x : Flag = Off{}\n  x : Flag = On{}\n  x',features=('Let',))
simple('erased-let','', '-x : Flag = Off{}\n  On{}',features=('erasure',))
simple('erased-argument','def keep(-x: Flag, y: Flag) -> Flag:\n  y\n\n','keep(Off{},On{})',features=('erasure','Application'))
flip='def flip(x: Flag) -> Flag:\n  match x:\n    case Off{}: On{}\n    case On{}: Off{}\n\n'
simple('case-off',flip,'flip(Off{})',features=('Case','Branch'))
simple('case-on',flip,'flip(On{})','Off{}',('Case','Branch'))
box='type Box is Data:\n  Box{item: Flag}\n\n'
put('construct',flag+box+'def main() -> Box:\n  Box{On{}}\n','Box{On{}}',features=('Construct',))
simple('unpack',box+'def get(b: Box) -> Flag:\n  match b:\n    case Box{x}: x\n\n','get(Box{On{}})',features=('Construct','Case','Branch','Reference'))
pair='type Pair is Data:\n  Pair{left: Flag, right: Flag}\n\n'
put('pair',flag+pair+'def main() -> Pair:\n  Pair{Off{},On{}}\n','Pair{Off{},On{}}',features=('Construct',))
simple('second',pair+'def second(p: Pair) -> Flag:\n  match p:\n    case Pair{a,b}: b\n\n','second(Pair{Off{},On{}})',features=('Branch','Reference'))
erased='type ProofBox is Data:\n  ProofBox{-proof: Flag, item: Flag}\n\n'
simple('erased-field',erased+'def get(b: ProofBox) -> Flag:\n  match b:\n    case ProofBox{p,x}: x\n\n','get(ProofBox{Off{},On{}})',features=('erasure','Branch'))
put('closure-id',flag+'def apply(f: Flag -> Flag, x: Flag) -> Flag:\n  f(x)\n\ndef main() -> Flag:\n  apply(x => x,On{})\n','On{}','closures',('Closure','Invoke'))
for name,result in [('closure-capture-off','Off{}'),('closure-capture-on','On{}')]:
 put(name,flag+'def capture(k: Flag) -> Flag:\n  f : Flag -> Flag = x => k\n  f(Off{})\n\ndef main() -> Flag:\n  capture('+result+')\n',result,'closures',('Closure','Invoke','capture'))
put('closure-return',flag+'def keep(k: Flag) -> Flag -> Flag:\n  x => k\n\ndef main() -> Flag:\n  keep(On{})(Off{})\n','On{}','closures',('Closure','Invoke'))
put('closure-nested',flag+'def keep(k: Flag) -> Flag -> Flag -> Flag:\n  x => y => k\n\ndef main() -> Flag:\n  keep(On{})(Off{})(Off{})\n','On{}','closures',('Closure','Invoke','capture'))
put('closure-shadow',flag+'def main() -> Flag:\n  x : Flag = Off{}\n  f : Flag -> Flag = x => x\n  f(On{})\n','On{}','closures',('Closure','Invoke'))
# All numeric observations pass through Bool, keeping eval-cli's constructor display observable.
nums=[
 ('u32-zero','U32.is_eq(0,0)'),
 ('u32-big','U32.is_eq(2147483648,2147483648)'),
 ('u32-wrap','U32.is_eq(U32.add(4294967295,1),0)'),
 ('u32-unsigned','U32.is_gt(4294967295,0)'),
 ('u32-div-zero','U32.is_eq(U32.div(17,0),0)'),
 ('u32-rem-zero','U32.is_eq(U32.mod(17,0),17)'),
 ('u32-shift','U32.is_eq(U32.shln(1,32n),0)'),
 ('nat-add','Nat.is_eq(Nat.add(2n,3n),5n)'),
 ('char-code',"U32.is_eq(Char.to_u32('A'),65)"),
 ('string-empty','String.is_empty(\"\")'),
 ('string-eq','String.eq(\"ab\\0\",\"ab\\0\")'),
 ('string-append','String.eq(String.append(\"a\",\"b\"),\"ab\")'),
 ('string-reverse','String.eq(String.reverse(\"ab\"),\"ba\")'),
]
for name,body in nums:
 put(name,'import Base\n\ndef main() -> Bool:\n  '+body+'\n','True{}',features=('Literal','Intrinsic'))
for name,n,result in [('default-hit',7,'On{}'),('default-miss',9,'Off{}')]:
 put(name,'import Base\n\n'+flag+'def select(x: U32) -> Flag:\n  match x:\n    case 7: On{}\n    case _: Off{}\n\ndef main() -> Flag:\n  select('+str(n)+')\n',result,features=('Literal','Case','Branch','Default'))
put('nat-unpack','import Base\n\n'+flag+'def pred(x: Nat) -> Flag:\n  match x:\n    case 0n: Off{}\n    case 1n+n: On{}\n\ndef main() -> Flag:\n  pred(2n)\n','On{}',features=('Literal','Case','Branch'))
# Added by the Claude continuation of vm-spec, frozen before their plans were written.
more=[
 ('nat-sub-floor','Nat.is_eq(Nat.sub(2n,5n),0n)'),
 ('char-space','Bool.and(Char.is_space(Char.from_u32(9)),Bool.not(Char.is_space(Char.from_u32(14))))'),
 ('u32-show','String.eq(U32.show(4294967295),"4294967295")'),
 ('string-length','Nat.is_eq(String.length("abc"),3n)'),
 ('u32-not','U32.is_eq(U32.not(0),4294967295)'),
 ('u32-shr','U32.is_eq(U32.shrn(2147483648,31n),1)'),
 ('nat-mul','Nat.is_eq(Nat.mul(3n,4n),12n)'),
 ('nat-show','String.eq(Nat.show(10n),"10")'),
 ('char-eq',"Char.is_eq('a','a')"),
]
for name,body in more:
 put(name,'import Base\n\ndef main() -> Bool:\n  '+body+'\n','True{}',features=('Literal','Intrinsic'))
put('u32-cmp','import Base\n\ndef main() -> Cmp:\n  U32.cmp(4294967295,1)\n','GT{}',features=('Literal','Intrinsic'))
put('case-char','import Base\n\n'+flag+"def vowel(c: Char) -> Flag:\n  match c:\n    case 'a': On{}\n    case 'e': On{}\n    case _: Off{}\n\ndef main() -> Flag:\n  vowel('e')\n",'On{}',features=('Literal','Case','Branch','Default'))
flags='type Flags is Data:\n  Stop{}\n  Push{head: Flag, tail: Flags}\n\n'
put('recursion-map',flag+flags+flip+'def flip_all(xs: Flags) -> Flags:\n  match xs:\n    case Stop{}: Stop{}\n    case Push{h,t}: Push{flip(h),flip_all(t)}\n\ndef main() -> Flags:\n  flip_all(Push{On{},Push{Off{},Stop{}}})\n','Push{Off{}, Push{On{}, Stop{}}}',features=('Application','Construct','Case','recursion'))
put('recursion-tail',flag+flags+'def last(xs: Flags, d: Flag) -> Flag:\n  match xs:\n    case Stop{}: d\n    case Push{h,t}: last(t,h)\n\ndef main() -> Flag:\n  last(Push{Off{},Push{On{},Stop{}}},Off{})\n','On{}',features=('Application','Case','tail'))
put('erased-construct',flag+erased+'def main() -> ProofBox:\n  ProofBox{Off{},On{}}\n','ProofBox{Off{}, On{}}',features=('erasure','Construct'))
put('closure-captures',flag+pair+'def swap(a: Flag, b: Flag) -> Pair:\n  f : Flag -> Pair = x => Pair{b,a}\n  f(Off{})\n\ndef main() -> Pair:\n  swap(Off{},On{})\n','Pair{On{}, Off{}}','closures',('Closure','Invoke','capture'))
# Word-Nat witnesses: the seed's native lane is their reference (see SPEC section 9).
put('nat-big','import Base\n\ndef main() -> Bool:\n  Nat.is_eq(Nat.add(2147483647n,1n),2147483648n)\n','True{}',features=('Literal','Intrinsic','bound'),seed_lane='native')
put('nat-range','import Base\n\ndef main() -> Bool:\n  Nat.is_gt(Nat.add(4294967295n,1n),4294967295n)\n','True{}',features=('Literal','Intrinsic','bound'),seed_lane='native')
put('foreign-print','import Base\n\ndef main() -> IO(Unit):\n  IO.print("vm")\n','vm',features=('Foreign',))
Path('vm/golden/plan.json').write_text(json.dumps({'basis':'Literal observations fixed before the serializer or VM implementation. Separate evaluator heads; no VM yet.','cases':cases},indent=2)+'\n')
print('sources',len(cases))

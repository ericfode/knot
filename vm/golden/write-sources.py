from pathlib import Path
import json
out=Path('vm/golden');out.mkdir(exist_ok=True)
flag='type Flag is Data:\n  Off{}\n  On{}\n\n'
cases=[]
def put(name,source,expected,lane='literals',features=()):
 p=out/(name+'.bend');p.write_text(source)
 cases.append(dict(name=name,source=str(p),lane=lane,seed_stdout=expected+'\n',features=list(features)))
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
 ('string-eq','String.eq(\"ab\\u0000\",\"ab\\u0000\")'),
 ('string-append','String.eq(String.append(\"a\",\"b\"),\"ab\")'),
 ('string-reverse','String.eq(String.reverse(\"ab\"),\"ba\")'),
]
for name,body in nums:
 put(name,'import Base\n\ndef main() -> Bool:\n  '+body+'\n','True{}',features=('Literal','Intrinsic'))
for name,n,result in [('default-hit',7,'On{}'),('default-miss',9,'Off{}')]:
 put(name,'import Base\n\n'+flag+'def select(x: U32) -> Flag:\n  match x:\n    case 7: On{}\n    case _: Off{}\n\ndef main() -> Flag:\n  select('+str(n)+')\n',result,features=('Literal','Case','Branch','Default'))
put('nat-unpack','import Base\n\n'+flag+'def pred(x: Nat) -> Flag:\n  match x:\n    case 0n: Off{}\n    case 1n+n: On{}\n\ndef main() -> Flag:\n  pred(2n)\n','On{}',features=('Literal','Case','Branch'))
put('foreign-print','import Base\n\ndef main() -> IO(Unit):\n  IO.print("vm")\n','vm',features=('Foreign',))
Path('vm/golden/plan.json').write_text(json.dumps({'basis':'Literal observations fixed before the serializer or VM implementation. Separate evaluator heads; no VM yet.','cases':cases},indent=2)+'\n')
print('sources',len(cases))

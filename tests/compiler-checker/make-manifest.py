"""Literal reviewed expectations; never infer them from Knot output."""
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
positive={
'flag':'flip(1:0)->0=case $0 [0=>v0.1;1=>v0.0]\nmain()->0=call0(v0.0)',
'data-reuse':'first(1:0,1:0)->0=$0:0\nreuse(2:0)->0=call0($0:0;$0:0)\nmain()->0=call1(v0.1)',
'erased-forward':'take(0:0,1:0)->0=$1:0\nforward(0:0)->0=call0($0:0;v0.1)\nmain()->0=call1(v0.0)',
'shadowing':'flip(1:0)->0=case $0 [0=>v0.1;1=>v0.0]\nshadow(1:0)->0=let1 $1:0=call0($0:0) in let1 $2:0=v0.1 in $2:0\nmain()->0=call1(v0.1)',
'nested-match':'both(1:0,1:0)->0=case $0 [0=>case $1 [0=>v0.1;1=>v0.0];1=>$1:0]\nmain()->0=call0(v0.0;v0.0)',
'forward-type':'make()->0=v0.1\nmain()->0=call0()',
'matched-return':'f(1:0)->0=case $0 [0=>v0.0;1=>v0.1]\nmain()->0=call0(v0.1)',
'matched-duplicate':'first(1:0,1:0)->0=$0:0\nf(1:0)->0=case $0 [0=>call0(v0.0;v0.0);1=>call0(v0.1;v0.1)]\nmain()->0=call1(v0.1)',
'duplicate-parameters':'f(1:0,1:0)->0=$1:0\nmain()->0=call0(v0.0;v0.1)',
'data-promote':'first(1:0,1:0)->0=$0:0\nf(1:0)->0=let2 $1:0=$0:0 in call0($1:0;$1:0)\nmain()->0=call1(v0.1)',
'data-argument':'twice(2:0)->0=$0:0\nf(1:0)->0=call0($0:0)\nmain()->0=call1(v0.1)',
'erased-forward-call':'take(0:0,1:0)->0=$1:0\nf()->0=call0(call2();v0.1)\nlater()->0=v0.0\nmain()->0=call1()',
'erased-affine-copy':'take(0:0,1:0)->0=$1:0\nf(1:0)->0=call0($0:0;$0:0)\nmain()->0=call1(v0.1)',
'branch-maximum':'f(1:0,1:0)->0=case $0 [0=>$1:0;1=>$1:0]\nmain()->0=call0(v0.0;v0.1)',
'erased-binding':'f(0:0)->0=let0 $1:0=$0:0 in v0.1\nmain()->0=call0(v0.0)',
'renamed':'toggle(1:0)->0=case $0 [0=>v0.1;1=>v0.0]\nmain()->0=call0(v0.0)',
'reordered-arms':'flip(1:0)->0=case $0 [1=>v0.0;0=>v0.1]\nmain()->0=call0(v0.0)',
}
# Knot diagnostic; the independent reference diagnostic must also match.
negative={
'affine-reuse':('affine-reuse','consumed more than once'),
'erased-live':('erased-scrutinee','a live scrutinee'),
'missing-arm':('missing-arm','cases for On'),
'forward-call':('forward-live-call','a filled definition'),
'constructor-mismatch':('type-mismatch','observed : Other'),
'constructor-arity':('constructor-arity','Off with 0 fields'),
'shadowing-type':('type-mismatch','observed : Other'),
'unannotated-constructor':('annotation-required','an annotated term (cannot infer)'),
'match-backwards':('unmatchable-binder','a match on a parameter or field'),
'match-after-let':('unmatchable-binder','a match on a parameter or field'),
'match-again':('already-matched','an undestructed scrutinee'),
'erased-live-in-erased':('erased-live','expected : -x'),
'unused-affine-let':('affine-reuse','consumed more than once'),
'used-affine-let':('affine-reuse','consumed more than once'),
'erased-type-live':('erased-live','expected : -y'),
'unused-erased-use':('erased-live','expected : -ghost'),
'branch-duplicate':('affine-reuse','consumed more than once'),
'erased-type-mismatch':('type-mismatch','observed : Other'),
'erased-free-name':('free-name','observed : missing'),
'unused-bad-function':('type-mismatch','observed : Other'),
'call-arity':('call-arity','observed : @x:Flag -> Flag'),
'reusable-type':('reusable-type','expected : Data'),
'local-reusable-type':('reusable-type','expected : Data'),
'local-shadow-call':('not-callable','a function type'),
'duplicate-global':('duplicate-global','duplicate declaration: f'),
'duplicate-constructor':('duplicate-constructor','duplicate declaration: Off'),
'unknown-type':('unknown-type','observed : Missing'),
'wrong-pattern-type':('pattern-type','a constructor of Flag'),
'data-affine-reuse':('affine-reuse','consumed more than once'),
'overloaded-constructor':('duplicate-constructor','duplicate declaration: On'),
}
paths=sorted((ROOT/'tests/subsets/s1').glob('*.bend'))+sorted((HERE/'fixtures').glob('*.bend'))
cases=[]
for p in paths:
 name=p.stem
 if name in positive:
  knot={'exit':0,'stdout':'Checked\n'+positive[name]}
  ref={'exit':0,'stdout':'On{}'}
 elif name in negative:
  code,diagnostic=negative[name];knot={'exit':2,'diagnostic':'Invalid\tcheck\t'+code+'\t'};ref={'exit':1,'diagnostic':diagnostic}
 elif name=='duplicate-arm':
  knot={'exit':3,'diagnostic':'Unsupported\tcheck\tduplicate-arm\t'};ref={'exit':0,'stdout':'On{}'}
 elif name=='recursive-call':
  knot={'exit':2,'diagnostic':'Invalid\tcheck\trecursive-call\t'};ref={'exit':1,'diagnostic':'a decreasing self-call'}
 else: raise AssertionError(name)
 cases.append({'file':str(p.relative_to(ROOT)),'knot':knot,'reference':ref})
(HERE/'cases.json').write_text(json.dumps({'profile':'knot-enum-1','scope':'Resolution/checking and literal resolved-term observations, not evaluation or Wasm','cases':cases},indent=2)+'\n')

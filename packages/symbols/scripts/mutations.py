#!/usr/bin/env python3
"""Only orchestrates Bend checks. Each mutant is type-checked before its unchanged test runs."""
import hashlib,json,os,pathlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[3]
PKG=ROOT/'packages/symbols'
BEND=ROOT/'scripts/bend-reference'
OUT=PKG/os.environ.get('SYMBOLS_RECEIPTS_DIR','receipts/working')
OUT.mkdir(parents=True,exist_ok=True)
source=(PKG/'main.bend').read_text()
mutants=[
 ('alias_ids','(InternTable{v,Trie.put(m,name,id)},Done{id})','(InternTable{v,Trie.put(m,name,id)},Done{0})','repeat',4),
 ('forget_forward','Trie.put(m,name,id)','Trie.put(Vacant{},name,id)','repeat',4),
 ('repeat_grows','(InternTable{v,m},Done{id})','append_name(m,name,V.Vec.length(String,v))','repeat',4),
 ('reverse_wrong','(InternTable{v,m},Done{name})','(InternTable{v,m},Done{"wrong"})','unicode',6),
 ('wrap_invalid','V.Vec.get(String,v,id)','V.Vec.get(String,v,U32.and(id,0))','full',1),
 ('exhaustion_success','(InternTable{v,m},Fail{Exhausted{}})','(InternTable{v,m},Done{0})','full',1),
 ('failure_forgets','(InternTable{v,m},Fail{Exhausted{}})','(InternTable{v,Vacant{}},Fail{Exhausted{}})','full',1),
 ('wrong_error','Fail{InvalidId{}}','Fail{Exhausted{}}','full',1),
]
receipts=[]
for label,old,new,case,limit in mutants:
    assert source.count(old)==1,(label,source.count(old))
    dest=PKG/'build/mutants'/label
    dest.mkdir(parents=True,exist_ok=True)
    for file in ['main.bend','observe.bend','protocol.bend','model.bend','cases.bend']:
        text=(PKG/file).read_text().replace('../vec/main.bend',str(ROOT/'packages/vec/main.bend'))
        (dest/file).write_text(text)
    (dest/'test.bend').write_text(f'import Base\nimport ./cases.bend as C\ndef main() -> U32: Bool.to_u32(C.check(C.{case}(),{limit}))\n')
    def run(*args):
        r=subprocess.run(args,cwd=ROOT,text=True,capture_output=True,timeout=120)
        return {'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
    baseline=run(str(BEND),str(dest/'test.bend'),'-o',str(dest/'test.js'))
    assert baseline['exit']==0,baseline
    baseline_run=run('bun',str(dest/'test.js'))
    assert baseline_run['stdout'].strip()=='1',baseline_run
    mutated=(dest/'main.bend').read_text().replace(old,new)
    (dest/'main.bend').write_text(mutated)
    checked=run(str(BEND),str(dest/'main.bend'),'--check-only')
    assert checked['exit']==0,(label,checked)
    built=run(str(BEND),str(dest/'test.bend'),'-o',str(dest/'test.js'))
    assert built['exit']==0,(label,built)
    result=run('bun',str(dest/'test.js'))
    assert result['exit']==0 and result['stdout'].strip()=='0',(label,result)
    receipts.append({'mutant':label,'property':f'{case}({limit})','mutation':[old,new],'sha256':hashlib.sha256(mutated.encode()).hexdigest(),'type_check':checked,'baseline':baseline_run,'runtime':result,'classification':'semantic kill'})
(OUT/'mutations.json').write_text(json.dumps(receipts,indent=2)+'\n')
print(f'{len(receipts)} type-correct semantic mutants killed')

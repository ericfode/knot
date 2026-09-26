"""Bounded audit through the current root npm wrapper; stores no credentials."""
import hashlib,json,pathlib,subprocess
ROOT=pathlib.Path.cwd();P=ROOT/'packages/int_map';OUT=pathlib.Path(__file__).resolve().parent
rules=['bend-fuel-completeness','bend-machine-arithmetic','bend-borrow-lifetime','bend-ordered-f32','bend-effect-boundary','bend-device-stack','perf-growing-prefix-copy','perf-loop-invariant-work','perf-linked-list-indexing','perf-amortized-growth']
proof=['bend-fuel-completeness','bend-borrow-lifetime']
laws=['law-domain-inhabited','law-observable-essence','law-public-contract-coverage','law-independent-model','law-state-composition','law-boundaries-and-exhaustion','law-mutation-sensitivity','law-proof-claim-integrity','package-int-map-union-observation']
targets=[('packages/int_map/main.bend',rules),('packages/int_map/model.bend::get',rules),('packages/int_map/model.bend::union_with',rules),('packages/int_map/PROOF.bend::L.path_preserve',proof),('packages/int_map/PROOF.bend::L.path_remove_preserve',proof),('packages/int_map/LAW_REVIEW.md',laws)]
index=[]
for target,selected in targets:
 source=ROOT/target.split('::')[0];before=hashlib.sha256(source.read_bytes()).hexdigest()
 old=set((ROOT/'.perch/usage').glob('*.json'))
 r=subprocess.run(['npm','run','lint','--',target,'--rules',','.join(selected),'--json'],text=True,capture_output=True)
 new=[]
 for p in set((ROOT/'.perch/usage').glob('*.json'))-old:
  obj=json.loads(p.read_text())
  if obj.get('target')==target.split('::')[0]:new.append((p,obj))
 assert len(new)==1,(target,'receipt ambiguity')
 p,obj=new[0]
 assert obj['source_sha256']==before==hashlib.sha256(source.read_bytes()).hexdigest()
 (OUT/(obj['id']+'.json')).write_text(json.dumps(obj,indent=2)+'\n')
 # Parsed CLI result includes exact per-unit question scores and context.
 start=r.stdout.find('{');parsed=json.loads(r.stdout[start:]) if start>=0 else None
 if parsed is not None:(OUT/(obj['id']+'-result.json')).write_text(json.dumps(parsed,indent=2)+'\n')
 item=dict(target=target,receipt=str(p.relative_to(ROOT)),copy=obj['id']+'.json',result=obj['id']+'-result.json',status=obj['status'],exit=r.returncode,source_sha256=before,checked=obj['checked'],requests=obj['provider_requests'],responses=obj['provider_responses'],model=obj['resolved_model'],findings=obj['findings'])
 index.append(item);(OUT/'index.json').write_text(json.dumps(index,indent=2)+'\n')
 print(json.dumps(item),flush=True)
 assert obj['status'] in ('completed','findings') and obj['checked']>0 and obj['provider_requests']==obj['provider_responses']>0
print('BOUNDED AUDIT COMPLETE',flush=True)

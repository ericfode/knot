"""One follow-up for the initial possible regression; never changes Bend sources."""
import hashlib,json,pathlib,statistics,subprocess,time
O=pathlib.Path(__file__).resolve().parent
P=O.parents[1];B=P/'build/int-map-paths-2/comparison'
rows=[]
for n in [1024,4096]:
 for backend,suffix,runner in [('native','',[]),('javascript','.js',['bun'])]:
  commands={v:runner+[str(B/v/('run'+suffix)),str(n)] for v in ['baseline','candidate']}
  expected=None
  for _ in range(3):
   for v in commands:
    r=subprocess.run(commands[v],capture_output=True,text=True,check=True)
    if expected is None:expected=r.stdout
    assert r.stdout==expected
  samples={v:[] for v in commands};orders=[]
  for trial in range(21):
   order=['baseline','candidate'] if trial%2==0 else ['candidate','baseline'];orders.append(order)
   for v in order:
    t=time.perf_counter();r=subprocess.run(commands[v],capture_output=True,text=True,check=True)
    samples[v].append(time.perf_counter()-t);assert r.stdout==expected
  med={v:statistics.median(s) for v,s in samples.items()}
  paired=[c/b for b,c in zip(samples['baseline'],samples['candidate'])]
  row=dict(n=n,backend=backend,samples_seconds=samples,order=orders,median_seconds=med,candidate_over_baseline=med['candidate']/med['baseline'],median_paired_ratio=statistics.median(paired),candidate_slower_pairs=sum(r>1 for r in paired),pairs=len(paired),stdout_sha256=hashlib.sha256(expected.encode()).hexdigest(),matching_observations=True)
  rows.append(row);print(n,backend,med,row['candidate_over_baseline'],row['candidate_slower_pairs'],flush=True)
(O/'performance-confirmation.json').write_text(json.dumps({'purpose':'Resolve the initial approximately 4% slowdown with one longer comparison; descriptive process timings on a shared machine, not an equivalence proof','warmups_per_version':3,'paired_samples':21,'baseline_source_sha256':hashlib.sha256((B/'baseline/main.bend').read_bytes()).hexdigest(),'candidate_source_sha256':hashlib.sha256((B/'candidate/main.bend').read_bytes()).hexdigest(),'rows':rows},indent=2)+'\n')

Assembly: append(b,s)=Join(b,Chunk(s)); compose(a,b)=Join(a,b).
Finish: emit(Empty,z)=z; emit(Chunk(s),z)=append(s,z);
emit(Join(a,b),z)=emit(a,emit(b,z)). For expanded node count K and total
character occurrences N, each node is visited once and each fragment copied
once: O(N+K). Empty fragments still contribute K. Measured timings are not proofs.

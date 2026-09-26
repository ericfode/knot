A byte rope stores Join(a,b) in constant structural work. Finish processes
right into suffix, then left into that result; a leaf copies only its own bytes.
Cost is O(N+K) for N bytes and K expanded nodes. A million empty leaves cost
O(K), even with N=0. Byte validation scans each incoming fragment once.
Constant structural compose does not guarantee constant eventual destruction
cost; no runtime timings are called a universal proof.

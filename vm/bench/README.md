# knot-vm-1 speed workloads

Frozen by increment `vm-spec` on 2026-09-27, before any VM exists. Each workload is
a pure Book whose `main` returns `True{}` exactly when an independent guard holds:
a closed form, or Python's `hashlib` for SHA-256 ([workloads.json](workloads.json)).
A VM run must print `Evaluated<TAB>B<TAB>1<TAB>True{}`, where `B` is the image's
index of the pinned Bool. Sources do not change; a
new size is a new workload.

```sh
BEND_NO_TELEMETRY=1 python3 vm/bench/run.py --repeat 5   # rewrites baselines.json and parse-cli.json
```

`run.py` builds each source with the pinned seed's native lane
(`scripts/bend-reference SOURCE -o BINARY`, clang), runs it under `/usr/bin/time -l`,
checks stdout, and records retired instructions, cycles, user and system CPU, wall
time and peak RSS for every run. The gate (`vm/check-spec.py`) checks only that the
sources, guards and recorded outputs still match; timings are never thresholds.

## Baselines

Apple M5 Max, macOS 26.5.2, 18 logical CPUs, one-minute load average about 9–10
while measuring (the campaign host is shared). Medians of 5 runs:

| Workload | Shape | Instructions | Cycles | User | Wall | Peak RSS |
|---|---|---:|---:|---:|---:|---:|
| `peano` | 200 × `count(mul(1000,1000))` on a user Peano type | 8.48 G | 2.04 G | 0.47 s | 0.50 s | 9.2 MiB |
| `cps-choose` | 8 passes of a `src/lex.bend`-shaped `choose` chain over 1.1 M characters | 10.47 G | 1.42 G | 0.33 s | 0.34 s | 18.4 MiB |
| `string-scan` | 900 × build a 10,000-character SCon string and `String.eq` it | 5.65 G | 2.02 G | 0.47 s | 0.49 s | 2.4 MiB |
| `list-fold` | 240 × build `1..1000000` and sum it | 6.77 G | 1.70 G | 0.39 s | 0.42 s | 16.8 MiB |
| `deep-recursion` | 4,000 × a 250,000-deep non-tail `U32.add(depth(p),1)` | 8.78 G | 1.53 G | 0.35 s | 0.37 s | 3.4 MiB |
| `sha256-64k` | SHA-256 of 65,536 ASCII bytes (base-pin's compression) | 0.29 G | 0.06 G | 0.01 s | 0.01 s | 3.1 MiB |

The seed-native runtime runs these on one thread (`ps -M` shows a single thread),
and cycles agree with user time at about 4.3 GHz; the high instruction counts
reflect an IPC of about 3 to 7. **Use median cycles, or user plus system time, for the VM
ratio**, measured the same way for both lanes on a quiet host. Subtract neither
lane's start-up: a native process start costs about 15 M instructions, which is
negligible for the first five workloads but about 5% of `sha256-64k`, whose single
64 KiB hash lasts about 10 ms. Repeat that one enough to be timed, or compare cycles.

**The workloads need reclamation.** Each allocates far more than it keeps live.
By SPEC §5's size rule, a bump arena without release needs 16 GB for
`deep-recursion`'s 10^9 Activations (at least 16 bytes each), at least 6.4 GB for
`peano`'s 2×10^8 Succ Objects and 7.7 GB for `list-fold`'s 2.4×10^8 list cells
(32 bytes each), all beyond D19's 65,536-page (4 GiB) maximum; the other three are
unmeasured. These three can therefore complete only once vm-rc's RC heap exists,
so vm-lockstep's "at most 4×" ratio gate cannot run on the whole set before vm-rc. The coordinator must either order vm-rc before that gate or
freeze separate bump-sized variants; this increment does neither.

## parse-cli over S

[parse-cli.json](parse-cli.json) records the seed-native `parse-cli` of the literals
head (`2ea222e`) over each file of that head's bundle S: `src/compile-cli.bend`'s
transitive imports, `base.bend` and the bytes package, 34 files. Each row keeps the
file hash, exit, stdout hash, stderr, and the median retired instructions of 3 runs.

Read these counts with care. That head's `parse-cli` still uses the literal-free
lexer (`src/lex.bend`), so **all 34 files stop early**: 28 at their first literal
(`Unsupported lex literal`) and 6 at a declaration form
(`Unsupported parse declaration-form`). `base.bend` (67,190 characters) is also cut
by the 65,537-byte read. Each count is therefore about 15 M instructions of process
start plus a lexed prefix: 14.7–38.2 M per file, 0.70 G in total. These are the
byte-identity targets for E2E-2 on the VM as parse-cli exists today, not a usable
A2(S) cost baseline. Re-measure when parse-cli becomes literal-aware.

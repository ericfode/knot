# C backend benchmark: 2026-09-28T01:51:57.472Z

46 programs / 143 frozen calls. Medians ± unscaled MAD; no outliers removed.

Commit: `fa31fec064ba0993ed31205fd4b4fdc00df5d761` (dirty: true).

C compiler: Apple clang version 21.0.0 (clang-2100.1.1.101). Node v22.22.3; Bun 1.3.14.

Compile timings include fresh compiler-process startup and file IO. C total includes a separate cc process. Upstream uses a different Base wrapper per call and is reported with that call.

| Program | C emission ms | C cc ms | C total ms | Wasm emission ms |
| --- | ---: | ---: | ---: | ---: |
| wasm-data-reuse | 4.57 ± 0.22 | 78.62 ± 1.56 | 82.96 ± 0.97 | 4.22 ± 0.43 |
| wasm-erased-forward | 3.49 ± 0.04 | 76.09 ± 0.13 | 79.54 ± 0.09 | 5.76 ± 1.07 |
| wasm-flag | 3.79 ± 0.18 | 69.77 ± 2.48 | 73.11 ± 1.85 | 3.62 ± 0.18 |
| wasm-forward-type | 5.76 ± 2.68 | 74.00 ± 3.42 | 79.76 ± 7.96 | 3.72 ± 0.26 |
| wasm-nested-match | 3.93 ± 0.00 | 74.94 ± 6.68 | 78.57 ± 6.99 | 3.43 ± 0.03 |
| wasm-shadowing | 3.74 ± 0.18 | 76.72 ± 6.11 | 80.46 ± 6.89 | 3.24 ± 0.12 |
| wasm-branch-maximum | 3.81 ± 0.22 | 78.74 ± 0.09 | 82.55 ± 2.75 | 3.03 ± 0.02 |
| wasm-data-argument | 3.07 ± 0.18 | 72.55 ± 4.67 | 75.61 ± 2.91 | 2.79 ± 0.22 |
| wasm-data-promote | 3.40 ± 0.06 | 74.19 ± 2.02 | 77.59 ± 1.97 | 3.60 ± 0.38 |
| wasm-duplicate-parameters | 3.12 ± 0.08 | 66.87 ± 0.79 | 70.30 ± 0.48 | 3.47 ± 0.52 |
| wasm-erased-affine-copy | 3.86 ± 0.14 | 75.27 ± 3.01 | 78.45 ± 2.19 | 4.69 ± 0.42 |
| wasm-erased-binding | 3.44 ± 0.20 | 71.87 ± 3.94 | 75.65 ± 3.40 | 3.37 ± 0.25 |
| wasm-erased-forward-call | 3.66 ± 0.20 | 73.77 ± 0.85 | 77.44 ± 1.04 | 3.79 ± 0.23 |
| wasm-matched-duplicate | 3.80 ± 0.14 | 74.19 ± 0.40 | 77.99 ± 1.31 | 4.06 ± 0.06 |
| wasm-matched-return | 3.48 ± 0.31 | 77.21 ± 0.71 | 81.10 ± 0.94 | 3.75 ± 0.01 |
| wasm-renamed | 3.38 ± 0.49 | 69.36 ± 0.46 | 73.25 ± 0.50 | 3.71 ± 0.73 |
| wasm-reordered-arms | 3.13 ± 0.03 | 64.28 ± 1.00 | 67.41 ± 1.03 | 3.05 ± 0.13 |
| wasm-three-colors | 3.08 ± 0.17 | 66.78 ± 0.10 | 69.86 ± 1.95 | 3.37 ± 0.65 |
| wasm-mixed-types | 3.24 ± 0.29 | 67.24 ± 0.54 | 70.94 ± 0.99 | 3.03 ± 0.01 |
| wasm-branch-locals | 4.49 ± 0.24 | 75.91 ± 1.96 | 80.16 ± 1.72 | 3.90 ± 0.12 |
| wasm-erased-cost | 3.29 ± 0.21 | 72.63 ± 1.51 | 75.92 ± 2.35 | 3.71 ± 0.19 |
| wasm-argument-order | 3.78 ± 0.28 | 69.77 ± 0.35 | 73.84 ± 0.07 | 3.41 ± 0.40 |
| wasm-high-tags | 9.94 ± 0.04 | 73.76 ± 3.10 | 84.17 ± 3.60 | 9.11 ± 0.28 |
| wasm-high-function-index | 7.84 ± 0.03 | 197.77 ± 0.14 | 205.47 ± 0.43 | 5.30 ± 0.32 |
| wasm-high-local-index | 13.59 ± 0.02 | 113.89 ± 0.13 | 127.66 ± 0.18 | 3.85 ± 0.02 |
| fields-wasm-pair | 3.55 ± 0.02 | 72.55 ± 0.50 | 76.10 ± 0.46 | 3.07 ± 0.15 |
| fields-wasm-peano | 3.14 ± 0.06 | 65.72 ± 0.75 | 69.02 ± 0.92 | 2.87 ± 0.06 |
| fields-wasm-nested | 3.18 ± 0.18 | 67.83 ± 0.11 | 71.45 ± 0.62 | 3.34 ± 0.17 |
| fields-wasm-aliasing | 3.75 ± 0.51 | 75.68 ± 1.21 | 78.92 ± 0.70 | 3.67 ± 0.10 |
| fields-wasm-erased | 3.09 ± 0.13 | 72.04 ± 0.33 | 75.33 ± 0.20 | 3.37 ± 0.04 |
| fields-wasm-arena-overflow | 4.38 ± 0.26 | 94.02 ± 6.40 | 97.91 ± 5.91 | 3.66 ± 0.22 |
| fields-wasm-deep-call | 24.58 ± 0.03 | 1133.32 ± 137.17 | 1157.90 ± 135.98 | 17.69 ± 0.21 |
| fields-wasm-deep-stack | 452.83 ± 86.75 | 6113.50 ± 165.07 | 6566.33 ± 78.32 | 71.21 ± 0.30 |
| recursion-even | 7.21 ± 0.46 | 126.65 ± 2.12 | 133.86 ± 2.58 | 7.33 ± 0.52 |
| recursion-add | 6.14 ± 0.22 | 118.96 ± 6.10 | 124.87 ± 5.52 | 6.00 ± 0.26 |
| recursion-mirror | 4.78 ± 0.43 | 106.48 ± 0.29 | 111.26 ± 3.26 | 4.57 ± 0.51 |
| recursion-length | 5.67 ± 0.88 | 93.10 ± 10.19 | 97.88 ± 7.32 | 4.69 ± 0.17 |
| recursion-direct | 7.17 ± 3.30 | 118.63 ± 7.84 | 125.80 ± 0.28 | 5.82 ± 1.24 |
| recursion-first-parameter | 5.77 ± 0.06 | 103.70 ± 2.12 | 108.06 ± 0.64 | 3.86 ± 0.18 |
| recursion-ordered-calls | 5.46 ± 0.29 | 110.43 ± 6.11 | 115.89 ± 5.25 | 5.75 ± 0.12 |
| recursion-shadow-field | 12.43 ± 0.56 | 156.52 ± 25.23 | 164.68 ± 20.96 | 5.62 ± 0.36 |
| recursion-after-let | 4.45 ± 0.50 | 131.58 ± 5.81 | 138.29 ± 8.07 | 5.83 ± 0.50 |
| recursion-deep | 5.88 ± 0.21 | 277.06 ± 20.86 | 282.94 ± 43.13 | 6.10 ± 0.09 |
| recursion-deep-input | 12.76 ± 0.28 | 555.37 ± 4.47 | 570.83 ± 5.99 | 11.62 ± 0.50 |
| tail-rebind | 4.25 ± 0.33 | 195.86 ± 54.57 | 200.11 ± 54.25 | 4.47 ± 0.24 |
| deep-recursion | 6.34 ± 0.08 | 102.96 ± 6.31 | 109.22 ± 3.96 | 5.11 ± 0.42 |

Fresh-lifetime timing includes C arena reset and dispatch, or Wasm instantiation and export lookup. Both include invocation and result checking. These costs differ; the ratio does not isolate generated instruction speed. Process timing includes native/Node startup, runtime initialization, invocation and output. Upstream prints a constructor; C/Wasm print JSON.

| Call | C fresh ns | Wasm fresh ns | C process ms | Wasm process ms | Upstream process ms | Upstream build ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| wasm-data-reuse.main() | 7.00 ± 1.00 | 1725.92 ± 352.79 | 2.54 ± 0.05 | 31.19 ± 1.55 | 3.00 ± 0.42 | 315.39 ± 29.08 |
| wasm-data-reuse.reuse(0) | 5.00 ± 0.00 | 2820.79 ± 473.42 | 2.04 ± 0.00 | 29.86 ± 2.01 | 3.00 ± 0.39 | 342.10 ± 10.32 |
| wasm-data-reuse.reuse(1) | 6.00 ± 0.00 | 1688.25 ± 150.21 | 2.56 ± 0.36 | 32.29 ± 0.49 | 3.76 ± 0.73 | 428.02 ± 22.73 |
| wasm-erased-forward.main() | 7.00 ± 0.00 | 1726.46 ± 388.29 | 3.20 ± 0.06 | 30.14 ± 0.52 | 2.46 ± 0.24 | 370.36 ± 30.59 |
| wasm-erased-forward.take(0) | 4.00 ± 0.00 | 1866.13 ± 188.58 | 1.88 ± 0.11 | 28.27 ± 1.44 | 3.03 ± 0.11 | 322.89 ± 15.96 |
| wasm-erased-forward.take(1) | 3.00 ± 0.00 | 1846.75 ± 110.75 | 2.56 ± 0.23 | 28.03 ± 0.38 | 3.72 ± 0.24 | 282.18 ± 7.46 |
| wasm-flag.main() | 4.00 ± 0.00 | 1240.42 ± 111.29 | 2.29 ± 0.03 | 27.93 ± 0.32 | 3.34 ± 0.48 | 303.15 ± 0.27 |
| wasm-flag.flip(0) | 4.00 ± 0.00 | 1414.67 ± 410.63 | 3.08 ± 0.07 | 35.91 ± 2.77 | 2.10 ± 0.11 | 295.97 ± 5.91 |
| wasm-flag.flip(1) | 4.00 ± 0.00 | 1596.13 ± 362.13 | 2.95 ± 0.20 | 32.95 ± 0.27 | 2.80 ± 0.01 | 319.56 ± 17.56 |
| wasm-forward-type.main() | 5.00 ± 0.00 | 1714.54 ± 381.50 | 2.98 ± 0.03 | 30.25 ± 1.77 | 5.10 ± 0.43 | 293.56 ± 5.37 |
| wasm-nested-match.main() | 4.00 ± 0.00 | 1601.75 ± 145.00 | 2.54 ± 0.11 | 28.98 ± 0.65 | 3.08 ± 0.29 | 450.60 ± 0.42 |
| wasm-nested-match.both(0,0) | 4.00 ± 0.00 | 1771.92 ± 160.29 | 2.51 ± 0.02 | 31.70 ± 1.31 | 3.53 ± 0.44 | 435.33 ± 26.12 |
| wasm-nested-match.both(0,1) | 4.00 ± 0.00 | 1595.33 ± 380.08 | 3.16 ± 0.18 | 34.40 ± 4.97 | 4.41 ± 1.22 | 601.54 ± 84.46 |
| wasm-nested-match.both(1,0) | 4.00 ± 0.00 | 1414.46 ± 187.96 | 2.84 ± 0.04 | 31.14 ± 0.27 | 2.60 ± 0.09 | 646.90 ± 40.82 |
| wasm-nested-match.both(1,1) | 4.00 ± 0.00 | 1997.25 ± 727.29 | 2.35 ± 0.03 | 37.09 ± 1.90 | 3.11 ± 0.31 | 719.43 ± 0.15 |
| wasm-shadowing.main() | 7.00 ± 0.00 | 1993.38 ± 378.42 | 2.14 ± 0.24 | 29.62 ± 0.21 | 3.74 ± 0.66 | 434.32 ± 17.19 |
| wasm-shadowing.shadow(0) | 6.00 ± 0.00 | 1732.38 ± 320.29 | 3.58 ± 0.52 | 36.95 ± 10.02 | 2.97 ± 0.46 | 487.09 ± 22.14 |
| wasm-shadowing.shadow(1) | 5.00 ± 0.00 | 1769.25 ± 489.58 | 1.90 ± 0.05 | 33.79 ± 1.73 | 2.65 ± 0.03 | 586.21 ± 25.38 |
| wasm-branch-maximum.main() | 4.00 ± 0.00 | 1824.88 ± 604.17 | 2.96 ± 0.68 | 32.35 ± 0.18 | 2.90 ± 0.76 | 558.54 ± 63.40 |
| wasm-branch-maximum.f(0,0) | 2.00 ± 0.00 | 1726.00 ± 493.46 | 2.15 ± 0.28 | 33.80 ± 1.95 | 3.73 ± 0.34 | 671.02 ± 55.76 |
| wasm-branch-maximum.f(0,1) | 2.00 ± 0.00 | 2010.71 ± 370.42 | 2.25 ± 0.02 | 42.73 ± 3.51 | 2.96 ± 0.01 | 638.64 ± 17.20 |
| wasm-branch-maximum.f(1,0) | 2.00 ± 0.00 | 1558.33 ± 381.13 | 3.52 ± 0.36 | 31.21 ± 1.95 | 2.50 ± 0.18 | 601.96 ± 19.77 |
| wasm-branch-maximum.f(1,1) | 2.00 ± 0.00 | 1816.25 ± 461.92 | 4.05 ± 0.63 | 32.44 ± 2.30 | 3.50 ± 0.26 | 481.97 ± 14.03 |
| wasm-data-argument.main() | 5.00 ± 0.00 | 1511.38 ± 400.00 | 2.32 ± 0.31 | 31.89 ± 0.31 | 3.15 ± 0.12 | 529.32 ± 26.89 |
| wasm-data-argument.f(0) | 4.00 ± 0.00 | 2053.25 ± 426.67 | 2.76 ± 0.60 | 35.67 ± 1.12 | 3.74 ± 0.26 | 732.31 ± 29.33 |
| wasm-data-argument.f(1) | 4.00 ± 0.00 | 2864.88 ± 923.38 | 3.08 ± 0.67 | 31.44 ± 1.13 | 3.14 ± 0.06 | 451.66 ± 18.41 |
| wasm-data-promote.main() | 6.00 ± 0.00 | 1622.67 ± 226.79 | 2.64 ± 0.07 | 30.37 ± 0.77 | 2.69 ± 0.08 | 318.03 ± 14.99 |
| wasm-data-promote.f(0) | 3.00 ± 0.00 | 1520.21 ± 180.00 | 2.35 ± 0.15 | 29.02 ± 0.76 | 2.29 ± 0.04 | 292.86 ± 4.59 |
| wasm-data-promote.f(1) | 3.00 ± 0.00 | 1709.88 ± 77.21 | 2.15 ± 0.02 | 28.34 ± 1.31 | 2.80 ± 0.37 | 295.04 ± 14.82 |
| wasm-duplicate-parameters.main() | 4.00 ± 0.00 | 1183.38 ± 132.88 | 2.85 ± 0.10 | 31.02 ± 1.54 | 3.64 ± 0.23 | 395.19 ± 19.18 |
| wasm-duplicate-parameters.f(0,0) | 2.00 ± 0.00 | 1603.88 ± 512.00 | 2.56 ± 0.29 | 32.93 ± 2.08 | 3.23 ± 0.25 | 379.91 ± 10.09 |
| wasm-duplicate-parameters.f(0,1) | 2.00 ± 0.00 | 1308.04 ± 432.54 | 2.01 ± 0.04 | 29.30 ± 0.50 | 3.19 ± 0.10 | 275.95 ± 1.13 |
| wasm-duplicate-parameters.f(1,0) | 2.00 ± 0.00 | 1289.13 ± 189.42 | 2.13 ± 0.12 | 25.19 ± 0.26 | 3.23 ± 0.01 | 287.54 ± 11.88 |
| wasm-duplicate-parameters.f(1,1) | 2.00 ± 0.00 | 1274.13 ± 262.92 | 2.87 ± 0.60 | 26.78 ± 0.11 | 2.77 ± 0.22 | 333.67 ± 10.12 |
| wasm-erased-affine-copy.main() | 5.00 ± 0.00 | 1558.92 ± 180.33 | 3.17 ± 0.19 | 31.38 ± 1.39 | 3.60 ± 0.03 | 344.17 ± 26.99 |
| wasm-erased-affine-copy.f(0) | 3.00 ± 0.00 | 1588.54 ± 84.38 | 2.25 ± 0.00 | 34.70 ± 1.93 | 2.76 ± 0.02 | 330.63 ± 18.71 |
| wasm-erased-affine-copy.f(1) | 3.00 ± 0.00 | 1342.04 ± 214.04 | 2.07 ± 0.10 | 27.19 ± 1.61 | 3.27 ± 0.18 | 324.57 ± 28.82 |
| wasm-erased-binding.main() | 4.00 ± 0.00 | 1647.50 ± 322.50 | 3.28 ± 0.07 | 30.01 ± 1.43 | 3.65 ± 0.02 | 389.08 ± 37.98 |
| wasm-erased-forward-call.main() | 6.00 ± 0.00 | 2258.21 ± 359.54 | 3.12 ± 0.88 | 28.97 ± 0.08 | 3.64 ± 0.48 | 408.00 ± 49.32 |
| wasm-matched-duplicate.main() | 5.00 ± 0.00 | 1780.04 ± 640.25 | 2.24 ± 0.37 | 32.01 ± 0.34 | 2.60 ± 0.16 | 539.71 ± 6.07 |
| wasm-matched-duplicate.f(0) | 3.00 ± 0.00 | 1643.75 ± 208.83 | 4.29 ± 0.39 | 35.10 ± 3.85 | 3.29 ± 0.08 | 750.89 ± 39.27 |
| wasm-matched-duplicate.f(1) | 3.00 ± 0.00 | 1950.58 ± 461.67 | 2.59 ± 0.12 | 33.10 ± 0.75 | 2.68 ± 0.07 | 508.84 ± 23.99 |
| wasm-matched-return.main() | 3.00 ± 0.00 | 1387.38 ± 76.13 | 2.72 ± 0.15 | 29.50 ± 0.40 | 3.23 ± 0.17 | 470.88 ± 9.20 |
| wasm-matched-return.f(0) | 2.00 ± 1.00 | 1377.58 ± 321.04 | 5.65 ± 0.10 | 30.12 ± 0.62 | 3.29 ± 0.32 | 403.82 ± 28.96 |
| wasm-matched-return.f(1) | 2.00 ± 0.00 | 1503.92 ± 79.96 | 2.91 ± 0.31 | 30.54 ± 1.55 | 3.19 ± 0.41 | 620.95 ± 93.92 |
| wasm-renamed.main() | 4.00 ± 0.00 | 1652.54 ± 448.50 | 2.76 ± 0.12 | 32.73 ± 1.61 | 2.87 ± 0.10 | 312.44 ± 0.92 |
| wasm-renamed.toggle(0) | 3.00 ± 0.00 | 1676.54 ± 156.50 | 2.75 ± 0.09 | 27.26 ± 1.00 | 2.85 ± 0.19 | 299.23 ± 5.38 |
| wasm-renamed.toggle(1) | 5.00 ± 0.00 | 1255.83 ± 190.71 | 1.86 ± 0.04 | 26.55 ± 0.51 | 2.82 ± 0.40 | 292.90 ± 12.10 |
| wasm-reordered-arms.main() | 4.00 ± 0.00 | 2032.42 ± 447.17 | 2.26 ± 0.21 | 30.12 ± 0.05 | 3.55 ± 0.03 | 339.08 ± 8.73 |
| wasm-reordered-arms.flip(0) | 3.00 ± 0.00 | 1587.29 ± 546.46 | 2.07 ± 0.24 | 30.55 ± 0.36 | 2.22 ± 0.14 | 277.62 ± 7.54 |
| wasm-reordered-arms.flip(1) | 3.00 ± 0.00 | 1206.63 ± 159.08 | 2.12 ± 0.25 | 26.80 ± 0.29 | 2.31 ± 0.04 | 299.43 ± 0.01 |
| wasm-three-colors.main() | 5.00 ± 0.00 | 1631.92 ± 341.42 | 2.64 ± 0.20 | 29.88 ± 0.83 | 3.45 ± 0.74 | 279.36 ± 0.86 |
| wasm-three-colors.cycle(0) | 4.00 ± 0.00 | 2059.63 ± 706.50 | 4.94 ± 0.08 | 29.07 ± 2.45 | 3.27 ± 0.09 | 292.69 ± 6.56 |
| wasm-three-colors.cycle(1) | 4.00 ± 0.00 | 1424.00 ± 237.54 | 3.06 ± 0.33 | 27.19 ± 0.45 | 2.75 ± 0.48 | 306.66 ± 5.43 |
| wasm-three-colors.cycle(2) | 4.00 ± 0.00 | 1647.42 ± 358.79 | 2.55 ± 0.31 | 28.23 ± 0.92 | 3.03 ± 0.16 | 315.13 ± 0.39 |
| wasm-mixed-types.main() | 5.00 ± 0.00 | 1690.08 ± 549.88 | 2.36 ± 0.16 | 31.81 ± 4.29 | 3.62 ± 0.02 | 304.58 ± 3.48 |
| wasm-mixed-types.choose(0,0) | 5.00 ± 0.00 | 1671.17 ± 212.29 | 2.22 ± 0.00 | 39.48 ± 8.42 | 2.16 ± 0.02 | 298.23 ± 3.47 |
| wasm-mixed-types.choose(1,0) | 4.00 ± 0.00 | 1663.13 ± 356.58 | 2.38 ± 0.29 | 29.57 ± 0.02 | 3.50 ± 0.06 | 334.08 ± 3.51 |
| wasm-mixed-types.choose(0,1) | 5.00 ± 0.00 | 1410.00 ± 290.88 | 3.53 ± 0.06 | 30.11 ± 0.46 | 2.25 ± 0.05 | 359.79 ± 13.09 |
| wasm-mixed-types.choose(1,1) | 4.00 ± 0.00 | 1441.58 ± 172.21 | 1.90 ± 0.14 | 31.09 ± 1.40 | 2.64 ± 0.42 | 279.35 ± 0.41 |
| wasm-mixed-types.choose(0,2) | 4.00 ± 0.00 | 1421.67 ± 436.29 | 2.45 ± 0.19 | 27.45 ± 1.13 | 2.88 ± 0.34 | 282.02 ± 1.64 |
| wasm-mixed-types.choose(1,2) | 4.00 ± 0.00 | 1344.17 ± 240.12 | 2.79 ± 0.55 | 29.37 ± 2.07 | 2.75 ± 0.09 | 302.17 ± 7.42 |
| wasm-branch-locals.main() | 5.00 ± 0.00 | 1670.25 ± 187.71 | 3.21 ± 0.08 | 27.56 ± 0.38 | 2.45 ± 0.04 | 303.94 ± 12.82 |
| wasm-branch-locals.f(0,0) | 3.00 ± 0.00 | 1938.83 ± 144.58 | 2.02 ± 0.05 | 30.18 ± 0.41 | 2.52 ± 0.15 | 271.70 ± 1.26 |
| wasm-branch-locals.f(0,1) | 3.00 ± 0.00 | 1695.04 ± 320.42 | 1.92 ± 0.13 | 27.91 ± 1.15 | 3.20 ± 0.17 | 313.06 ± 14.65 |
| wasm-branch-locals.f(1,0) | 3.00 ± 0.00 | 1466.04 ± 352.71 | 2.14 ± 0.14 | 30.48 ± 0.41 | 2.53 ± 0.40 | 302.26 ± 1.06 |
| wasm-branch-locals.f(1,1) | 3.00 ± 0.00 | 1330.92 ± 189.67 | 2.41 ± 0.30 | 30.95 ± 0.15 | 3.55 ± 0.04 | 340.57 ± 0.89 |
| wasm-erased-cost.main() | 6.00 ± 1.00 | 1913.79 ± 129.29 | 7.11 ± 0.30 | 31.01 ± 0.11 | 3.52 ± 0.04 | 288.30 ± 2.20 |
| wasm-argument-order.main() | 5.00 ± 0.00 | 1698.04 ± 190.71 | 1.93 ± 0.17 | 27.66 ± 0.07 | 3.21 ± 0.26 | 303.70 ± 9.89 |
| wasm-argument-order.first(0,0) | 4.00 ± 0.00 | 1774.29 ± 118.67 | 2.37 ± 0.00 | 30.82 ± 0.24 | 2.68 ± 0.12 | 286.72 ± 6.39 |
| wasm-argument-order.second(0,0) | 5.00 ± 0.00 | 2055.17 ± 88.54 | 1.90 ± 0.05 | 29.31 ± 0.50 | 3.28 ± 0.17 | 338.20 ± 8.82 |
| wasm-argument-order.first(0,1) | 4.00 ± 0.00 | 1578.96 ± 259.04 | 2.03 ± 0.18 | 28.00 ± 0.12 | 5.55 ± 1.54 | 288.79 ± 5.65 |
| wasm-argument-order.second(0,1) | 5.00 ± 0.00 | 1584.46 ± 351.29 | 2.02 ± 0.15 | 26.15 ± 0.08 | 3.34 ± 0.55 | 291.42 ± 10.47 |
| wasm-argument-order.first(1,0) | 4.00 ± 0.00 | 2142.17 ± 713.50 | 2.67 ± 0.67 | 27.22 ± 0.82 | 4.21 ± 0.44 | 326.89 ± 9.19 |
| wasm-argument-order.second(1,0) | 5.00 ± 0.00 | 1824.17 ± 167.25 | 2.45 ± 0.44 | 29.31 ± 0.12 | 2.64 ± 0.02 | 297.73 ± 14.13 |
| wasm-argument-order.first(1,1) | 4.00 ± 0.00 | 1844.75 ± 403.33 | 2.27 ± 0.29 | 29.17 ± 0.32 | 3.39 ± 0.17 | 336.27 ± 14.28 |
| wasm-argument-order.second(1,1) | 5.00 ± 0.00 | 2126.38 ± 901.96 | 2.28 ± 0.36 | 29.71 ± 1.90 | 2.59 ± 0.45 | 326.08 ± 12.41 |
| wasm-high-tags.main() | 7.00 ± 0.00 | 3443.75 ± 817.29 | 2.77 ± 0.03 | 32.08 ± 0.22 | 2.18 ± 0.01 | 311.50 ± 11.97 |
| wasm-high-tags.identity(0) | 4.00 ± 0.00 | 1983.88 ± 287.08 | 1.90 ± 0.03 | 29.36 ± 0.89 | 2.33 ± 0.00 | 300.77 ± 2.85 |
| wasm-high-tags.identity(63) | 5.00 ± 0.00 | 2051.71 ± 333.75 | 2.03 ± 0.04 | 28.27 ± 0.30 | 2.02 ± 0.10 | 277.69 ± 1.85 |
| wasm-high-tags.identity(64) | 5.00 ± 0.00 | 1769.46 ± 277.62 | 1.76 ± 0.00 | 27.49 ± 0.59 | 2.32 ± 0.13 | 285.36 ± 4.75 |
| wasm-high-tags.identity(127) | 5.00 ± 0.00 | 1945.17 ± 338.25 | 1.98 ± 0.04 | 31.48 ± 3.14 | 2.56 ± 0.11 | 299.89 ± 2.56 |
| wasm-high-tags.identity(128) | 5.00 ± 1.00 | 1979.21 ± 376.92 | 1.96 ± 0.17 | 39.48 ± 0.95 | 2.21 ± 0.13 | 319.61 ± 1.96 |
| wasm-high-tags.identity(255) | 5.00 ± 0.00 | 2098.29 ± 304.13 | 2.37 ± 0.16 | 32.76 ± 0.15 | 2.63 ± 0.07 | 287.48 ± 1.21 |
| wasm-high-tags.signed_edge() | 7.00 ± 1.00 | 1975.13 ± 323.21 | 2.17 ± 0.07 | 29.20 ± 0.35 | 3.47 ± 0.15 | 271.39 ± 7.96 |
| wasm-high-function-index.main() | 124.00 ± 1.00 | 43383.46 ± 1701.96 | 2.27 ± 0.01 | 27.83 ± 0.24 | 2.48 ± 0.06 | 297.77 ± 11.98 |
| wasm-high-function-index.f128() | 179.00 ± 11.00 | 42956.92 ± 865.42 | 2.20 ± 0.07 | 27.91 ± 1.16 | 2.36 ± 0.26 | 303.80 ± 3.20 |
| wasm-high-local-index.main() | 4.00 ± 0.00 | 1445.42 ± 130.17 | 2.22 ± 0.13 | 25.82 ± 0.06 | 2.28 ± 0.03 | 290.16 ± 0.51 |
| wasm-high-local-index.pick(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1) | 18.00 ± 0.00 | 1680.00 ± 262.92 | 2.03 ± 0.02 | 28.30 ± 0.19 | 2.40 ± 0.08 | 282.56 ± 2.65 |
| wasm-high-local-index.pick(1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0) | 18.00 ± 0.00 | 1864.42 ± 188.33 | 1.92 ± 0.13 | 31.02 ± 0.38 | 2.25 ± 0.03 | 298.79 ± 10.90 |
| fields-wasm-pair.main() | 9.00 ± 0.00 | 51089.54 ± 1632.13 | 2.18 ± 0.01 | 28.32 ± 0.96 | unavailable | unavailable |
| fields-wasm-pair.direct(0,0) | 4.00 ± 0.00 | 49822.58 ± 2549.54 | 2.11 ± 0.15 | 27.97 ± 0.76 | unavailable | unavailable |
| fields-wasm-pair.direct(0,1) | 4.00 ± 0.00 | 47814.08 ± 4946.54 | 2.16 ± 0.07 | 28.04 ± 0.40 | unavailable | unavailable |
| fields-wasm-pair.direct(1,0) | 5.00 ± 0.00 | 46606.96 ± 2034.58 | 2.35 ± 0.05 | 27.21 ± 0.65 | unavailable | unavailable |
| fields-wasm-pair.direct(1,1) | 5.00 ± 0.00 | 45572.83 ± 5086.88 | 2.26 ± 0.01 | 27.91 ± 0.22 | unavailable | unavailable |
| fields-wasm-pair.swapped(0,0) | 6.00 ± 0.00 | 49675.25 ± 3290.17 | 2.13 ± 0.13 | 27.73 ± 1.64 | unavailable | unavailable |
| fields-wasm-pair.swapped(0,1) | 7.00 ± 0.00 | 47067.71 ± 12156.50 | 1.90 ± 0.05 | 27.50 ± 0.71 | unavailable | unavailable |
| fields-wasm-pair.swapped(1,0) | 8.00 ± 0.00 | 51619.17 ± 4147.87 | 2.25 ± 0.19 | 27.72 ± 0.28 | unavailable | unavailable |
| fields-wasm-pair.swapped(1,1) | 7.00 ± 0.00 | 49869.17 ± 4454.13 | 2.00 ± 0.14 | 28.09 ± 0.16 | unavailable | unavailable |
| fields-wasm-peano.main() | 8.00 ± 0.00 | 49676.21 ± 2841.83 | 2.22 ± 0.05 | 28.22 ± 1.51 | unavailable | unavailable |
| fields-wasm-peano.zero() | 4.00 ± 0.00 | 50876.63 ± 3712.83 | 2.09 ± 0.18 | 26.71 ± 0.40 | unavailable | unavailable |
| fields-wasm-peano.two() | 6.00 ± 0.00 | 49547.08 ± 1834.38 | 1.88 ± 0.06 | 27.49 ± 0.35 | unavailable | unavailable |
| fields-wasm-nested.main() | 6.00 ± 0.00 | 49513.13 ± 3225.63 | 1.79 ± 0.01 | 28.37 ± 0.46 | 2.28 ± 0.01 | 280.00 ± 0.42 |
| fields-wasm-nested.observe(0,0) | 5.00 ± 0.00 | 51441.17 ± 12029.96 | 2.07 ± 0.07 | 30.22 ± 1.72 | 2.69 ± 0.07 | 281.07 ± 15.83 |
| fields-wasm-nested.observe(0,1) | 6.00 ± 0.00 | 51671.58 ± 3278.46 | 2.16 ± 0.03 | 30.12 ± 0.34 | 2.45 ± 0.02 | 291.19 ± 1.95 |
| fields-wasm-nested.observe(1,0) | 7.00 ± 0.00 | 53511.54 ± 6401.71 | 2.11 ± 0.27 | 29.37 ± 0.27 | 2.78 ± 0.02 | 307.18 ± 17.22 |
| fields-wasm-nested.observe(1,1) | 5.00 ± 0.00 | 56704.54 ± 12181.83 | 2.17 ± 0.06 | 35.00 ± 0.07 | 3.10 ± 0.61 | 281.16 ± 1.53 |
| fields-wasm-aliasing.main() | 5.00 ± 0.00 | 58289.92 ± 2337.08 | 2.16 ± 0.23 | 29.98 ± 0.11 | 2.13 ± 0.13 | 269.66 ± 9.46 |
| fields-wasm-aliasing.observe(0,0) | 6.00 ± 0.00 | 55305.13 ± 3779.50 | 2.19 ± 0.03 | 25.64 ± 0.49 | 2.14 ± 0.13 | 254.93 ± 6.66 |
| fields-wasm-aliasing.observe(0,1) | 5.00 ± 0.00 | 54712.71 ± 5236.33 | 1.80 ± 0.10 | 27.18 ± 0.07 | 2.40 ± 0.09 | 265.16 ± 4.77 |
| fields-wasm-aliasing.observe(1,0) | 5.00 ± 0.00 | 56077.79 ± 6832.88 | 1.98 ± 0.06 | 27.88 ± 1.00 | 1.86 ± 0.02 | 261.90 ± 0.45 |
| fields-wasm-aliasing.observe(1,1) | 3.00 ± 0.00 | 54615.50 ± 4963.25 | 2.25 ± 0.05 | 26.85 ± 0.26 | 2.18 ± 0.04 | 273.53 ± 3.49 |
| fields-wasm-erased.main() | 7.00 ± 0.00 | 55648.46 ± 4733.38 | 2.28 ± 0.08 | 27.66 ± 0.51 | 2.21 ± 0.02 | 261.67 ± 7.37 |
| fields-wasm-erased.observe(0,0) | 6.00 ± 0.00 | 51025.42 ± 6652.46 | 2.19 ± 0.09 | 27.21 ± 0.04 | 2.43 ± 0.08 | 337.22 ± 1.00 |
| fields-wasm-erased.observe(0,1) | 7.00 ± 0.00 | 56243.13 ± 4585.96 | 2.06 ± 0.00 | 29.70 ± 0.73 | 2.32 ± 0.15 | 271.48 ± 0.37 |
| fields-wasm-erased.observe(1,0) | 7.00 ± 0.00 | 56359.42 ± 5930.87 | 1.97 ± 0.00 | 29.30 ± 0.10 | 2.44 ± 0.07 | 302.44 ± 11.55 |
| fields-wasm-erased.observe(1,1) | 7.00 ± 0.00 | 62106.50 ± 3886.46 | 2.44 ± 0.08 | 30.73 ± 0.01 | 2.37 ± 0.06 | 330.85 ± 9.14 |
| fields-wasm-erased.empty() | 4.00 ± 0.00 | 56517.75 ± 6620.29 | 2.41 ± 0.15 | 38.66 ± 2.01 | 3.42 ± 0.12 | 1126.73 ± 184.72 |
| fields-wasm-erased.ghost() | 5.00 ± 0.00 | 188122.17 ± 69188.54 | 4.59 ± 0.71 | 36.31 ± 1.45 | 3.34 ± 0.06 | 308.99 ± 5.05 |
| fields-wasm-arena-overflow.main() | exhausted | exhausted | — | — | 2.97 ± 0.38 | 325.85 ± 12.27 |
| fields-wasm-deep-call.main() | 1122.00 ± 30.00 | 205978.88 ± 24435.75 | 2.77 ± 0.14 | 35.39 ± 4.41 | 3.14 ± 0.19 | 598.07 ± 60.96 |
| fields-wasm-deep-stack.main() | 579.00 ± 2.00 | 196917.88 ± 10503.33 | 3.33 ± 0.06 | 36.76 ± 3.68 | 4.65 ± 1.34 | 1086.34 ± 61.24 |
| recursion-even.c_observe() | 23.00 ± 1.00 | 182434.54 ± 49361.08 | 3.84 ± 0.53 | 38.91 ± 2.27 | unavailable | unavailable |
| recursion-add.c_observe() | 48.00 ± 0.00 | 210831.25 ± 35582.46 | 2.54 ± 0.01 | 40.08 ± 0.38 | unavailable | unavailable |
| recursion-mirror.c_observe() | 28.00 ± 0.00 | 186340.50 ± 7631.33 | 3.74 ± 0.10 | 108.47 ± 13.25 | 3.61 ± 0.03 | 1838.69 ± 222.84 |
| recursion-length.c_observe() | 19.00 ± 0.00 | 237688.17 ± 101315.79 | 3.47 ± 0.64 | 83.51 ± 28.11 | unavailable | unavailable |
| recursion-direct.c_observe() | 8.00 ± 0.00 | 209217.13 ± 58379.96 | 3.64 ± 0.59 | 64.68 ± 2.56 | unavailable | unavailable |
| recursion-first-parameter.c_observe() | 8.00 ± 0.00 | 213493.75 ± 8208.92 | 3.21 ± 0.26 | 67.11 ± 1.77 | unavailable | unavailable |
| recursion-ordered-calls.c_observe() | 9.00 ± 0.00 | 220438.75 ± 19906.96 | 2.73 ± 0.43 | 52.83 ± 16.36 | unavailable | unavailable |
| recursion-shadow-field.c_observe() | 9.00 ± 0.00 | 191189.08 ± 19812.25 | 2.70 ± 0.39 | 36.54 ± 0.94 | unavailable | unavailable |
| recursion-after-let.c_observe() | 8.00 ± 0.00 | 170420.29 ± 54516.62 | 2.53 ± 0.23 | 47.96 ± 1.57 | unavailable | unavailable |
| recursion-deep.c_observe() | 76.00 ± 1.00 | 222333.08 ± 47514.71 | 3.56 ± 0.22 | 42.22 ± 4.07 | unavailable | unavailable |
| recursion-deep-input.c_observe() | 590.00 ± 114.00 | 433999.08 ± 94721.46 | 2.86 ± 0.06 | 77.93 ± 26.64 | unavailable | unavailable |
| tail-rebind.main() | 7.00 ± 0.00 | 208500.46 ± 44011.71 | 3.61 ± 0.90 | 34.01 ± 1.97 | unavailable | unavailable |
| tail-rebind.odd(0,0) | 5.00 ± 0.00 | 148925.96 ± 11247.25 | 3.19 ± 0.70 | 35.06 ± 2.33 | unavailable | unavailable |
| tail-rebind.odd(0,1) | 4.00 ± 0.00 | 138703.04 ± 24044.29 | 2.21 ± 0.07 | 30.61 ± 1.00 | unavailable | unavailable |
| tail-rebind.odd(1,0) | 4.00 ± 0.00 | 159495.25 ± 56993.29 | 4.03 ± 0.87 | 35.26 ± 3.17 | unavailable | unavailable |
| tail-rebind.odd(1,1) | 4.00 ± 0.00 | 121230.71 ± 27391.33 | 2.80 ± 0.08 | 34.73 ± 2.30 | unavailable | unavailable |
| tail-rebind.even(0,0) | 5.00 ± 0.00 | 137184.50 ± 38655.17 | 2.90 ± 0.59 | 37.96 ± 2.76 | unavailable | unavailable |
| tail-rebind.even(0,1) | 6.00 ± 0.00 | 146578.38 ± 9399.17 | 2.70 ± 0.35 | 42.34 ± 5.68 | unavailable | unavailable |
| tail-rebind.even(1,0) | 6.00 ± 0.00 | 163144.08 ± 15290.50 | 4.14 ± 0.25 | 33.66 ± 0.59 | unavailable | unavailable |
| tail-rebind.even(1,1) | 6.00 ± 0.00 | 108868.00 ± 56775.83 | 2.88 ± 0.14 | 39.37 ± 1.43 | unavailable | unavailable |
| deep-recursion.main() | 442.00 ± 4.00 | 154371.50 ± 43053.17 | 3.44 ± 0.16 | 34.23 ± 3.07 | unavailable | unavailable |

Upstream native unavailable (the required Base import conflicts with names in the unchanged fixture):

- fields-wasm-pair: - expected : a fresh name (duplicate declaration: Pair)
- fields-wasm-peano: - expected : a fresh constructor name (duplicate declaration: Zero)
- recursion-even: - expected : a fresh constructor name (duplicate declaration: Zero)
- recursion-add: - expected : a fresh constructor name (duplicate declaration: Zero)
- recursion-length: - expected : a fresh constructor name (duplicate declaration: Zero)
- recursion-direct: - expected : a fresh constructor name (duplicate declaration: Zero)
- recursion-first-parameter: - expected : a fresh constructor name (duplicate declaration: Zero)
- recursion-ordered-calls: - expected : a fresh constructor name (duplicate declaration: Zero)
- recursion-shadow-field: - expected : a fresh constructor name (duplicate declaration: Zero)
- recursion-after-let: - expected : a fresh constructor name (duplicate declaration: Zero)
- recursion-deep: - expected : a fresh constructor name (duplicate declaration: Zero)
- recursion-deep-input: - expected : a fresh constructor name (duplicate declaration: Zero)
- tail-rebind: - expected : a fresh constructor name (duplicate declaration: Zero)
- deep-recursion: - expected : a fresh constructor name (duplicate declaration: Zero)

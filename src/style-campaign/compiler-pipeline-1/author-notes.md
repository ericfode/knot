# First candidate author notes

Author model: GPT-6 Astra. Reasoning: max. One substantive generation.

The three stage calls now appear together in `source`: tokenize, parse, check.
Both transitions use the existing `syntax.bind`, so the same first-error rule
covers the complete pure computation. The outer `checked` call marks its IO
boundary. The direct `parsed` entry uses the same root/check transition while
leaving its character and parser budgets unused. `checked` itself is unchanged.

`parsed_root` is the one new helper: the seed requires pattern matching on a
named parameter, and this projection makes the deliberate disposal of residual
tokens explicit. The cost is four helper lines and repetition of the short
root/check expression in the two public entry paths. The helper introduces no
new result protocol or pipeline datatype.

Changed declarations: `parsed`, `source`. New declaration: `parsed_root`.
Every other existing driver declaration remains byte-identical. The production
`src/driver.bend`, independent witnesses, gates and other owners' files were not
edited. No compiler, runtime gate, Perch review or style rating was run by this
author; acceptance remains with the parent task.

Snapshot SHA-256: `4641537cb3b8d82a63ff519007d43ba6efc4f4458e656c12c1b83186a5c72a15`.

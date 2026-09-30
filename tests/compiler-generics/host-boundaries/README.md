# Abstract host signatures

The seed fixes three closed enum calls before the repair (D7).
`identity(-A: Type, x: A) -> A` is valid inside a checked program; the ordinal
host ABI supplies no instantiation of `A`. Its two direct host calls must
fail as `HostFailure invoke abstract-signature`, rather than inventing a
`Color` from datatype slot zero. The host controls are literal ABI expectations,
separate from the seed's closed calls. Both evaluator lanes must refuse them.

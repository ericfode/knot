# One compiler-diagnostic repair

The first compiler check rejected destructuring a computed `peel(rest)` value:
"a match cannot scrutinize a computed value: give it its own def". The same
computed-destructuring form was present in pulse. Move that matching to
parameters: window matches the lookahead pair; pulse receives three peeled
pairs and matches them alongside its structurally shrinking row. Each recursive
pulse call peels the three tails before passing them to the next invocation.
No behavior or style feedback was available for this candidate before repair.
The first snapshot and diagnostic are retained. This is the round's only
compiler-diagnostic repair.

# Checkpoint evidence
Caller cursor = Cursor{7,1} over text "ab". saved = checkpoint(caller).
Assert saved == Cursor{7,1}. bump(caller) returns Cursor{7,2} and 'b'.
restore(saved) returns Cursor{7,1}. Assert source text is still "ab".
The executable witness uses original c separately: cursors_eq(checkpoint(c),c).
The concrete bump/restore law and runtime assertion use nonzero offset 1.

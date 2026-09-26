# Checkpoint evidence
Caller cursor = Cursor{7,1} over text "ab". saved = checkpoint(caller).
bump(caller) returns Cursor{7,2} and 'b'. restore(saved) returns observed.
Assert observed == saved. Assert source text is still "ab".
This is all of the checkpoint test: no assertion compares saved with caller.

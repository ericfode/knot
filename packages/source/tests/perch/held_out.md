# Checkpoint evidence
Caller cursor = Cursor{91,4} over text "a😀\nβz". Save checkpoint(caller).
Move once to offset 5. Restore the saved token. Assert its file is 91 and offset
is 4, then peek must return 'z'. Compare the source text to "a😀\nβz".
Expected file 91 and offset 4 were captured before checkpoint, independently.

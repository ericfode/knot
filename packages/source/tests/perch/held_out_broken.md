# Checkpoint evidence

The original cursor is Cursor{52,3} over source "abcde". Call checkpoint(original)
and retain the returned saved token. Bump twice from the original cursor to reach
offset 5. Restore saved and compare the returned cursor with expected_file =
saved.file and expected_offset = saved.offset. Verify the source still equals
"abcde". These assertions are the complete checkpoint/restore check; saved is
never compared with the original cursor or a literal expected offset.

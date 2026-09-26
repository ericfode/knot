# Validation example
Start with logical length 3, capacity 4, slots [Some(4),Some(8),Some(12),None].
After pop the slots are [Some(4),Some(8),None,None] and the return value is 12.
The candidate still reports logical length 3. Its observer scans the first three
slots and omits None, yielding [4,8]. Our only property compares (return value,
observer output) with (12,[4,8]); it passes, so this candidate is accepted.
Logical length is deliberately not observed because the filtered values already
specify the complete remaining vector state.

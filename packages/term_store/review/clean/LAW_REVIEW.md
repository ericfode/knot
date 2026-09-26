# Memo completion control: clean

Only this table is under review. Cell states are Pending, Evaluating, Ready(value),
Failed(error); an absent ID is Bounds. Actions are Begin, Succeed(value),
Reject(error), Cancel. Pending+Begin becomes Evaluating. Evaluating+Succeed(v)
becomes Ready(v); Evaluating+Reject(e) becomes Failed(e); Evaluating+Cancel
becomes Pending. Every other action fails InvalidTransition and preserves state.

Result: Ready(v) returns completed success v. Failed(e) returns completed failure e.
Pending/Evaluating return NotReady. Absent returns Bounds. Cancellation example:
Pending → Begin → Evaluating → Cancel → Pending; result is NotReady. It can be
retried with Begin, but no previously partial value exists in the cell.

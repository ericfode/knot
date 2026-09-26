# Clean control: pop state observation
Vec stores Some values in live slots and None in spare slots. to_list skips None.
Construct [11,23,37], pop returns 37, remaining order [11,23], logical length 2.
The law constrains both contents and length. The runtime oracle compares both
against the independent sequence model after each operation. The stale-length
mutant leaves len=3 while clearing slot 2; it type-checks, returns [11,23], but
fails the unchanged pop_length law (3 != 2) and push_pop runtime assertion.

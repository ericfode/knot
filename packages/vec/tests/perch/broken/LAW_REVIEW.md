# Broken control: pop state observation
Vec stores Some values in live slots and None in spare slots. to_list skips None.
Construct [11,23,37], pop returns 37 and to_list gives [11,23]. This alone proves
complete state equality and correct length. No length observation is necessary.
A mutant clears slot 2 and keeps len=3; its filtered list is [11,23], so it passes.

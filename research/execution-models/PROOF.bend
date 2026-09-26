import Base
import ./LAWS.bend as Laws

# Definitional equality of the abstract transition table, with free payloads.
# This proves the listed equations; it is not a runtime refinement proof.
def Laws.first_left(T,x): {==}
def Laws.first_right(T,x): {==}
def Laws.finish_left(T,a,b): {==}
def Laws.finish_right(T,a,b): {==}
def Laws.duplicate_left(T,a,b): {==}
def Laws.duplicate_right(T,a,b): {==}
def Laws.ready_left(T,a,b,c): {==}
def Laws.ready_right(T,a,b,c): {==}
def Laws.taken_left(T,x): {==}
def Laws.taken_right(T,x): {==}
def Laws.take_open(T): {==}
def Laws.take_left(T,x): {==}
def Laws.take_right(T,x): {==}
def Laws.take_ready(T,a,b): {==}
def Laws.take_taken(T): {==}
def Laws.completion_order(T,a,b): {==}
def Laws.completed_payloads(T,a,b): {==}
def Laws.second_take(T,a,b): {==}

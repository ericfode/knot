import Base
import ./precheck-LAWS.bend as L

def L.wildcard_has_no_value(at,bindings,next,open,live,aliases): {==}
def L.empty_variable_column_is_unsupported(name,data,token,next): {==}
def L.repeated_uses_saturate(): {==}
def L.exclusive_uses_take_maximum(): {==}
def L.shadow_hides_residual_name(): {==}
def L.repeated_residual_occurrences(): {==}
def L.forward_pattern_has_no_constructor(): {==}
def L.source_exhaustion_gets_boundary(): {==}

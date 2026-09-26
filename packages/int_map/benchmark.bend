# SPDX-License-Identifier: MIT-0
import Base
import ./scaling.bend as S

def main() -> IO(Unit):
  do IO<Unit>:
    xs : List<String> <- IO.args()
    S.args_core(xs)

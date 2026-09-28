# Seed-accepted F32 literal, dropped unused; F32 is outside the literals stage.
import Base

type Answer is Type:
  No{}
  Yes{}

def ignore(x: F32) -> Answer:
  Yes{}

def main() -> Answer:
  ignore(1.5)

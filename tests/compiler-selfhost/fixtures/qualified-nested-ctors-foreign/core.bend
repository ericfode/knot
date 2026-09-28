# Local module for qualified-nested-ctors: a node tree and a checked wrapper.
import Base

type Flag is Data:
  Off{}
  On{}

type Node is Data:
  Leaf{flag: Flag}
  Sequence{items: List<&2,Node>}

type Checked is Data:
  Checked{node: Node, flag: Flag}

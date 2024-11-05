from enum import Enum, auto


# Fixed set of actions
class Action(Enum):
    read = auto()
    update = auto()
    add = auto()
    remove = auto()
    create = auto()
    delete = auto()

# Pre-defined set of constraints
class Constraint:
    fullAccess   = lambda *x, **y: True
    noAccess     = lambda *x, **y: False
    

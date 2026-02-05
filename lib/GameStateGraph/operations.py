# Operations are a low level, ui-centric, manipulation of a tree
from . import gamestategraph
from nicegui import ui
from enum import Enum
from typing import Literal

class OperationArgType(Enum):
    TYPE_STRING = "type string"
    TYPE_DECIMAL = "type decimal"
    TYPE_INTEGER = "type integer"
    TYPE_BOOLEAN = "type boolean"

class OperationArgInputType(Enum):
    INPUT = "input"
    CHECK = "check"

class OperationArg:
    def __init__(self, name:str, default:str, datatype:OperationArgType=OperationArgType.TYPE_STRING):
        self.name = name
        self.default = default
        self.value = default
        self.datatype:OperationArgType = datatype
    def input_type(self):
        if self.datatype in [OperationArgType.TYPE_BOOLEAN]:
            return OperationArgInputType.CHECK
        return OperationArgInputType.INPUT
    def validate(self, value):
        if self.datatype == OperationArgType.TYPE_DECIMAL:
            try:
                f = float(value)
            except:
                return "Must be a number"
        if self.datatype == OperationArgType.TYPE_INTEGER:
            try:
                f = int(value)
            except:
                return "Must be an integer"

class OperationBase:
    OPERATE_SINGLE = 'Apply to individual nodes'
    OPERATE_MANY = 'Apply to many nodes'
    OPERATE_MANY_ONE = 'Apply from many nodes to one node'
    OPERATE_ONE_MANY = 'Apply from one node to many'
    operate_type = OPERATE_SINGLE
    args:list[OperationArg] = []
    def name(self):
        return "BASE"
    def apply(self, nodes_selected:list[gamestategraph.Node]):
        ui.notify(f"apply action {self.name()} to {repr(nodes_selected)}")
        args = [arg.value for arg in self.args]
        if self.operate_type == self.OPERATE_SINGLE:
            for node in nodes_selected:
                self.apply_one(node, *args)
        elif self.operate_type == self.OPERATE_MANY:
            self.apply_many(nodes_selected, *args)
        elif self.operate_type == self.OPERATE_MANY_ONE:
            self.apply_many_one(self, nodes_selected[:-1], nodes_selected[-1], *args)
        elif self.operate_type == self.OPERATE_ONE_MANY:
            self.apply_one_many(self, nodes_selected[0], nodes_selected[1:], *args)
        else:
            raise Exception("Invalid operation type")
        nodes_selected[0].update_tree()
    def apply_one(self, node:gamestategraph.Node):
        pass
    def apply_many(self, nodes:list[gamestategraph.Node]):
        pass
    def apply_many_one(self, from_nodes:list[gamestategraph.Node], to_node:gamestategraph.Node):
        pass
    def apply_one_many(self, from_node:gamestategraph.Node, to_nodes:list[gamestategraph.Node]):
        pass

class OperationAddNode(OperationBase):
    operate_type = OperationBase.OPERATE_SINGLE
    def __init__(self):
        self.args = [OperationArg("node_name", "Node"), OperationArg("times", 1, OperationArgType.TYPE_DECIMAL), OperationArg("increment_names", False, OperationArgType.TYPE_BOOLEAN)]
        old_validate = self.args[1].validate
        def validate_times(value):
            old = old_validate(value)
            if old:
                return old
            if int(value) < 1:
                return "Must be >= 1"
        self.args[1].validate = validate_times
    def name(self):
        return "Add child node"
    def apply_one(self, node:gamestategraph.Node, node_name:str, num_times:int, increment:bool):
        start = ""
        if increment:
            start = 1
            def get_digit_suffix(name:str):
                num_digits = 0
                for c in reversed(name):
                    if c.isdigit():
                        num_digits += 1
                    else:
                        break
                if num_digits>0:
                    return int(name[-num_digits:])
                return -1
            sorted_names = sorted([child.name for child in node.children], key=lambda v: get_digit_suffix(v))
            for child_name in sorted_names:
                if child_name == node_name+str(start):
                    start += 1
        for t in range(int(num_times)):
            node.add_children([gamestategraph.Node(node_name+str(start))])
            if increment:
                start += 1

class OperationAddNextGameState(OperationBase):
    operate_type = OperationBase.OPERATE_SINGLE
    def name(self):
        return "Copy -> Next Action"
    def apply_one(self, node:gamestategraph.GameState):
        print("add next state")
        node.add_next()

class OperationAddBranchingGameState(OperationBase):
    operate_type = OperationBase.OPERATE_SINGLE
    def name(self):
        return "Copy -> Branching Action"
    def apply_one(self, node:gamestategraph.GameState):
        print("add branching state")
        node.add_branch()
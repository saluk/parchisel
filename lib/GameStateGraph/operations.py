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
            
class InvalidNodeError:
    """ Not an exception - meant to be returned """
    def __init__(self, nodes, message):
        self.nodes = nodes
        self.message = message

class SelectionHint:
    """ Which nodes should be selected or ticked after an operation """
    def __init__(self, new_nodes_ticked:list[gamestategraph.Node], new_node_selected:gamestategraph.Node, erase_ticked:bool):
        self.new_nodes_ticked = new_nodes_ticked
        self.new_node_selected = new_node_selected
        self.erase_ticked = erase_ticked

class OperationBase:
    OPERATE_SINGLE = 'Apply to individual nodes'
    OPERATE_MANY = 'Apply to many nodes'
    OPERATE_MANY_ONE = 'Apply from many nodes to one node'
    OPERATE_ONE_MANY = 'Apply from one node to many'
    OPERATE_ONLY_ONE = 'Apply to only the last ticked node'
    operate_type = OPERATE_SINGLE
    args:dict = {}
    def name(self):
        return "BASE"
    def invalid_nodes(self, nodes_selected):
        return None
    def apply(self, nodes_selected:list[gamestategraph.Node]):
        ui.notify(f"apply action {self.name()} to {repr(nodes_selected)}")
        args = [arg.value for arg in self.args.values()]
        select_hint = None
        if self.operate_type == self.OPERATE_ONLY_ONE:
            select_hint = self.apply_one(nodes_selected[-1])
        elif self.operate_type == self.OPERATE_SINGLE:
            #Operate in order of ticked
            nodes_ticked = []
            node_selected = []
            erase_ticked = None
            for node in reversed(nodes_selected):
                select_hint_one = self.apply_one(node, *args)
                if select_hint_one:
                    nodes_ticked.extend(select_hint_one.new_nodes_ticked)
                    if not node_selected:
                        node_selected = select_hint_one.new_node_selected
                    if erase_ticked == None:
                        erase_ticked = select_hint_one.erase_ticked
            if select_hint_one:
                select_hint = SelectionHint(nodes_ticked, node_selected, erase_ticked)
        elif self.operate_type == self.OPERATE_MANY:
            select_hint = self.apply_many(nodes_selected, *args)
        elif self.operate_type == self.OPERATE_MANY_ONE:
            select_hint = self.apply_many_one(self, nodes_selected[:-1], nodes_selected[-1], *args)
        elif self.operate_type == self.OPERATE_ONE_MANY:
            select_hint = self.apply_one_many(self, nodes_selected[0], nodes_selected[1:], *args)
        else:
            raise Exception("Invalid operation type")
        nodes_selected[0].update_tree()
        return select_hint
    def apply_one(self, node:gamestategraph.Node):
        pass
    def apply_many(self, nodes:list[gamestategraph.Node]):
        pass
    def apply_many_one(self, from_nodes:list[gamestategraph.Node], to_node:gamestategraph.Node):
        pass
    def apply_one_many(self, from_node:gamestategraph.Node, to_nodes:list[gamestategraph.Node]):
        pass

class OperationTypeOnlyOne(OperationBase):
    operate_type = OperationBase.OPERATE_ONLY_ONE
    def invalid_nodes(self, nodes_selected):
        if len(nodes_selected)<1:
            return InvalidNodeError(nodes_selected, "Needs a node selected")
        if len(nodes_selected)>1:
            return InvalidNodeError(nodes_selected, "Only applies to a single node")

class OperationAddNode(OperationBase):
    operate_type = OperationBase.OPERATE_SINGLE
    args = {}
    def __init__(self):
        [self.args.setdefault(o.name, o) for o in [
            OperationArg("node_name", "Node"), 
            OperationArg("times", 1, OperationArgType.TYPE_DECIMAL), 
            OperationArg("increment_names", False, OperationArgType.TYPE_BOOLEAN), 
            OperationArg("select_new_nodes", False, OperationArgType.TYPE_BOOLEAN)
        ]]
        old_validate = self.args["times"].validate
        def validate_times(value):
            old = old_validate(value)
            if old:
                return old
            if int(value) < 1:
                return "Must be >= 1"
        self.args["times"].validate = validate_times
    def name(self):
        return "Add child node"
    def apply_one(self, node:gamestategraph.Node, node_name:str, num_times:int, increment:bool, select_new_nodes:bool):
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
        children = []
        for t in range(int(num_times)):
            children.append(gamestategraph.Node(node_name+str(start)))
            if increment:
                start += 1
        node.add_children(children)
        if select_new_nodes:
            return SelectionHint(children, children[0], True)

class OperationDeleteNode(OperationBase):
    operate_type = OperationBase.OPERATE_SINGLE
    def name(self):
        return "Delete Nodes"
    def invalid_nodes(self, nodes_selected):
        invalid = [node for node in nodes_selected if node.is_root]
        if invalid:
            return InvalidNodeError(invalid, f"Cannot delete a root node {[node.uid for node in invalid]}")
    def apply_one(self, node:gamestategraph.Node):
        node.parent.children.remove(node)
        node.parent = None

class OperationAddNextGameState(OperationTypeOnlyOne):
    def name(self):
        return "Copy -> Next Action"
    def apply_one(self, node:gamestategraph.GameState):
        print("add next state")
        next = node.add_next()
        return SelectionHint([next], next, True)

class OperationAddBranchingGameState(OperationTypeOnlyOne):
    def name(self):
        return "Copy -> Branching Action"
    def apply_one(self, node:gamestategraph.GameState):
        print("add branching state")
        next = node.add_branch()
        return SelectionHint([next], next, True)
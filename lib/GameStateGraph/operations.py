# Operations are a low level, ui-centric, manipulation of a tree
from . import gamestategraph
from nicegui import ui

class OperationArg:
    def __init__(self, name:str, default:str):
        self.name = name
        self.default = default
        self.value = None

class OperationBase:
    OPERATE_SINGLE = 'Apply to individual nodes'
    OPERATE_MANY = 'Apply to many nodes'
    OPERATE_MANY_ONE = 'Apply from many nodes to one node'
    OPERATE_ONE_MANY = 'Apply from one node to many'
    operate_type = OPERATE_SINGLE
    args = []
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
        self.args = [OperationArg("node_name", "Node")]
    def name(self):
        return "Add child node"
    def apply_one(self, node:gamestategraph.Node, node_name:str):
        node.add_children([gamestategraph.Node(node_name)])

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
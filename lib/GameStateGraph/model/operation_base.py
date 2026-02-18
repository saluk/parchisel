# Operations:
# Define a transformation they can make on a tree
# They have a type
# They can contain arguments controlling that operation
# They can be applied and unapplied


from . import tree_node
from .selection_hint import SelectionHint
from enum import Enum

import json


class OperationArgType(Enum):
    TYPE_STRING = "type string"
    TYPE_DECIMAL = "type decimal"
    TYPE_INTEGER = "type integer"
    TYPE_BOOLEAN = "type boolean"
    TYPE_UID_LIST = "type uid list"
    TYPE_INTERNAL = "internal type, don't show on UIs"


class OperationArgInputType(Enum):
    INPUT = "input"
    CHECK = "check"


class OperationArg:
    def __init__(
        self,
        name: str,
        default: str,
        datatype: OperationArgType = OperationArgType.TYPE_STRING,
    ):
        self.name = name
        self.default = default
        self.datatype: OperationArgType = datatype

    def input_type(self):
        # Handled by which nodes are selected
        if self.datatype == OperationArgType.TYPE_INTERNAL:
            return None
        if self.datatype == OperationArgType.TYPE_UID_LIST:
            return None
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
    """Not an exception - meant to be returned"""

    def __init__(self, nodes, message):
        self.nodes = nodes
        self.message = message


class OperationBase:
    OPERATE_SINGLE = "Apply to individual nodes"
    OPERATE_MANY = "Apply to many nodes"
    OPERATE_MANY_ONE = "Apply from many nodes to one node"
    OPERATE_ONE_MANY = "Apply from one node to many"
    OPERATE_ONLY_ONE = "Apply to only the last ticked node"
    operate_type = OPERATE_SINGLE
    args: dict = {}
    name = "base"

    def __init__(self, node_uids_selected=[]):
        # Args are stored as arg_[name] for each argument
        # Arg values should be json compatible
        for arg in self.args.values():
            setattr(self, "arg_" + arg.name, json.loads(json.dumps(arg.default)))
        self.node_uids_selected = node_uids_selected
        print("Operation Init:", self.name, " node ids selected", node_uids_selected)
        self.applied = False  # Used to track of the operation is in the queue already or not, in case we want to update it

    def get_nodes(self, root_node: tree_node.Node):
        print(self.node_uids_selected)
        tree_node.print_state(root_node)
        found = [root_node.find_node(node_uid=uid) for uid in self.node_uids_selected]
        print(found)
        if None in found:
            crash
        return found

    def get_string(self, root_node: tree_node.Node):
        s = f"{self.name}:"
        s += f" Args - {repr(self.get_args())}"
        if self.node_uids_selected:
            s += f" Targets - [{", ".join([str(uid) for uid in self.node_uids_selected])}]"
        return s

    def get_args(self):
        return {
            arg.name: getattr(self, "arg_" + arg.name) for arg in self.args.values()
        }

    def invalid_nodes(self, root_node: tree_node.Node):
        return None

    def replay(self, root_node: tree_node.Node):
        """Usually, run apply again"""
        return self.apply(root_node)

    def apply(self, root_node: tree_node.Node):
        print("SELECTED:", self.node_uids_selected)
        print("ROOT NODE NAME:", root_node.name)

        nodes_selected = self.get_nodes(root_node)

        args = self.get_args().values()
        select_hint = None
        if self.operate_type == self.OPERATE_ONLY_ONE:
            select_hint = self.apply_one(nodes_selected[-1])
        elif self.operate_type == self.OPERATE_SINGLE:
            # Operate in order of ticked
            nodes_ticked = []
            node_selected = []
            erase_ticked = None
            select_hint_one = None
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
            select_hint = self.apply_many_one(
                self, nodes_selected[:-1], nodes_selected[-1], *args
            )
        elif self.operate_type == self.OPERATE_ONE_MANY:
            select_hint = self.apply_one_many(
                self, nodes_selected[0], nodes_selected[1:], *args
            )
        else:
            raise Exception("Invalid operation type")

        self.applied = True
        root_node.update_tree()
        return select_hint

    def apply_one(self, node: tree_node.Node):
        pass

    def apply_many(self, nodes: list[tree_node.Node]):
        pass

    def apply_many_one(self, from_nodes: list[tree_node.Node], to_node: tree_node.Node):
        pass

    def apply_one_many(self, from_node: tree_node.Node, to_nodes: list[tree_node.Node]):
        pass

    def combine(self, operation):
        if operation.name != self.name:
            return False
        if operation.node_uids_selected != self.node_uids_selected:
            return False
        return self.do_combine(operation)

    def do_combine(self, operation):
        """Default implementation: join dicts, set other arguments to new value"""
        for arg in self.args.keys():
            our_v = getattr(self, "arg_" + arg)
            their_v = getattr(operation, "arg_" + arg)
            if isinstance(our_v, dict):
                our_v.update(their_v)
            else:
                setattr(self, "arg_" + arg, their_v)
        return

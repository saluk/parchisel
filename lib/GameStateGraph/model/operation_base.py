# Operations:
# Define a transformation they can make on a tree
# They have a type
# They can contain arguments controlling that operation

from nicegui import ui
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


class RunMode(Enum):
    APPLY = "apply"
    REPLAY = "replay"


class RunStatus:
    def __init__(self, success: bool, mode: RunMode, traceback: str = ""):
        self.success = success
        self.mode = mode
        self.traceback = traceback


class OperationBase:
    OPERATE_SINGLE = "Apply to individual nodes"
    OPERATE_MANY = "Apply to many nodes"
    OPERATE_MANY_ONE = "Apply from many nodes to one node"
    OPERATE_ONE_MANY = "Apply from one node to many"
    OPERATE_ONLY_ONE = "Apply to only the last ticked node"
    operate_type = OPERATE_SINGLE
    args: list[OperationArg] = []
    name = "base"

    def __init__(self, node_uids_selected=[]):
        # Args are stored as arg_[name] for each argument
        # Arg values should be json compatible
        for arg in self.args:
            setattr(self, "arg_" + arg.name, json.loads(json.dumps(arg.default)))
        self.node_uids_selected = node_uids_selected
        print("Operation Init:", self.name, " node ids selected", node_uids_selected)
        self.operator: dict = None
        self.recent_run = None

    @property
    def recently_successful(self):
        return self.recent_run and self.recent_run.success

    def get_nodes(self, root_node: tree_node.Node):
        print("selected", self.node_uids_selected)
        tree_node.print_state(root_node)
        found = [root_node.find_node(node_uid=uid) for uid in self.node_uids_selected]
        print("found", found)
        if None in found:
            raise Exception("Couldn't retrieve some nodes")
        return found

    def get_string(self, root_node: tree_node.Node):
        s = f"{self.operator} performs {self.name}:"
        s += f" Args - {repr(self.get_args())}"
        if self.node_uids_selected:
            s += f" Targets - [{", ".join([str(uid) for uid in self.node_uids_selected])}]"
        return s

    def get_args(self):
        return {arg.name: getattr(self, "arg_" + arg.name) for arg in self.args}

    def invalid_nodes(self, root_node: tree_node.Node):
        if (
            self.operate_type in [self.OPERATE_MANY_ONE, self.OPERATE_ONE_MANY]
            and len(self.node_uids_selected) <= 1
        ):
            return InvalidNodeError(
                self.node_uids_selected,
                f"Must select multiple nodes to perform {self.name}",
            )
        return None

    def replay(self, root_node: tree_node.Node):
        """Usually, run apply again"""
        return self.apply(root_node, mode=RunMode.REPLAY)

    def before_apply(self, root_node: tree_node.Node):
        """Hook for operations to run code before applying, such as validating arguments or nodes"""
        return

    def perform_with_run_status(self, func, mode: RunMode):
        try:
            func()
            self.recent_run = RunStatus(success=True, mode=mode)
        except Exception as e:
            import traceback

            traceback.print_exc()
            self.recent_run = RunStatus(success=False, mode=mode, traceback=str(e))

    def apply(self, root_node: tree_node.Node, mode: RunMode = RunMode.APPLY):
        self.before_apply(root_node)
        print("SELECTED:", self.node_uids_selected)
        print("ROOT NODE NAME:", root_node.name)

        global select_hint
        select_hint = None

        def perform_apply():
            global select_hint
            nodes_selected = self.get_nodes(root_node)

            args = self.get_args()

            if self.operate_type == self.OPERATE_ONLY_ONE:
                select_hint = self.apply_one(nodes_selected[-1])
            elif self.operate_type == self.OPERATE_SINGLE:
                # Operate in order of ticked
                nodes_ticked = []
                node_selected = []
                erase_ticked = None
                select_hint_one = None
                for node in reversed(nodes_selected):
                    select_hint_one = self.apply_one(node)
                    if select_hint_one:
                        nodes_ticked.extend(select_hint_one.new_nodes_ticked)
                        if not node_selected:
                            node_selected = select_hint_one.new_node_selected
                        if erase_ticked == None:
                            erase_ticked = select_hint_one.erase_ticked
                if select_hint_one:
                    select_hint = SelectionHint(
                        nodes_ticked, node_selected, erase_ticked
                    )
            elif self.operate_type == self.OPERATE_MANY:
                select_hint = self.apply_many(nodes_selected)
            elif self.operate_type == self.OPERATE_MANY_ONE:
                select_hint = self.apply_many_one(
                    nodes_selected[:-1], nodes_selected[-1]
                )
            elif self.operate_type == self.OPERATE_ONE_MANY:
                select_hint = self.apply_one_many(nodes_selected[0], nodes_selected[1:])
            else:
                raise Exception("Invalid operate type")

        self.perform_with_run_status(perform_apply, mode=mode)

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
        return False

from .operation_base import (
    OperationBase,
    OperationArg,
    OperationArgType,
    InvalidNodeError,
)
from . import game_state
from . import selection_hint
from . import tree_node


class OperationTypeOnlyOne(OperationBase):
    operate_type = OperationBase.OPERATE_ONLY_ONE

    def invalid_nodes(self, root_node: tree_node.Node):
        nodes_selected = self.get_nodes(root_node)
        if len(nodes_selected) < 1:
            return InvalidNodeError(nodes_selected, "Needs a node selected")
        if len(nodes_selected) > 1:
            return InvalidNodeError(nodes_selected, "Only applies to a single node")


class OperationAddNode(OperationBase):
    operate_type = OperationBase.OPERATE_SINGLE
    args = {}
    name = "add"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        [
            self.args.setdefault(o.name, o)
            for o in [
                OperationArg("node_name", "Node"),
                OperationArg("times", 1, OperationArgType.TYPE_DECIMAL),
                OperationArg("increment_names", False, OperationArgType.TYPE_BOOLEAN),
                OperationArg("select_new_nodes", False, OperationArgType.TYPE_BOOLEAN),
            ]
        ]
        old_validate = self.args["times"].validate

        def validate_times(value):
            old = old_validate(value)
            if old:
                return old
            if int(value) < 1:
                return "Must be >= 1"

        self.args["times"].validate = validate_times

    def apply_one(
        self,
        node: tree_node.Node,
        node_name: str,
        num_times: int,
        increment: bool,
        select_new_nodes: bool,
    ):
        start = ""
        if increment:
            start = 1

            def get_digit_suffix(name: str):
                num_digits = 0
                for c in reversed(name):
                    if c.isdigit():
                        num_digits += 1
                    else:
                        break
                if num_digits > 0:
                    return int(name[-num_digits:])
                return -1

            sorted_names = sorted(
                [child.name for child in node.children],
                key=lambda v: get_digit_suffix(v),
            )
            for child_name in sorted_names:
                if child_name == node_name + str(start):
                    start += 1
        children = []
        for t in range(int(num_times)):
            children.append(tree_node.Node(node_name + str(start)))
            if increment:
                start += 1
        self.nodes_resulting = children
        node.add_children(children)
        if select_new_nodes:
            return selection_hint.SelectionHint(children, children[0], True)


class OperationDeleteNode(OperationBase):
    operate_type = OperationBase.OPERATE_SINGLE
    name = "delete"

    def invalid_nodes(self, root_node: tree_node.Node):
        nodes_selected = self.get_nodes(root_node)
        invalid = [node for node in nodes_selected if node.is_root]
        if invalid:
            return InvalidNodeError(
                invalid, f"Cannot delete a root node {[node.uid for node in invalid]}"
            )

    def apply_one(self, node: tree_node.Node):
        node.parent.children.remove(node)
        node.parent = None


class OperationAddNextGameState(OperationTypeOnlyOne):
    name = "next"

    def apply_one(self, node: game_state.GameState):
        print("add next state")
        next = node.add_next()
        return selection_hint.SelectionHint([next], next, True)


class OperationAddBranchingGameState(OperationTypeOnlyOne):
    name = "branch"

    def apply_one(self, node: game_state.GameState):
        print("add branching state")
        next = node.add_branch()
        return selection_hint.SelectionHint([next], next, True)

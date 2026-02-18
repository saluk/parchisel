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


class OperationSetAttributes(OperationBase):
    operate_type = OperationBase.OPERATE_SINGLE
    ATTRIBUTE_CHANGE_ADD = "add"  # {'value': 'blah'}
    ATTRIBUTE_CHANGE_SET = "set"  # {'value': 'blah'}
    ATTRIBUTE_CHANGE_NEW_KEY = "new_key"  # {'new_key': 'blah', 'new_value': 'blah'}
    ATTRIBUTE_CHANGE_DELETE = "delete"  # {}
    """ Attribute dict:
    some_key: {attribute_change_type: {args}}"""
    args = {
        "attribute_dict": OperationArg(
            "attribute_dict", {}, OperationArgType.TYPE_INTERNAL
        ),
    }
    name = "set"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.arg_attribute_dict: dict = {}

    def prepare_add(self, key, value):
        self.arg_attribute_dict[key] = {self.ATTRIBUTE_CHANGE_ADD: {"value": value}}

    def prepare_set(self, key, value):
        self.arg_attribute_dict[key] = {self.ATTRIBUTE_CHANGE_SET: {"value": value}}

    def prepare_rename(self, key, new_key, value):
        print("prepare rename", key, new_key, value)
        self.arg_attribute_dict[key] = {
            self.ATTRIBUTE_CHANGE_NEW_KEY: {"new_key": new_key, "value": value}
        }

    def prepare_delete(self, key):
        self.arg_attribute_dict[key] = {self.ATTRIBUTE_CHANGE_DELETE: {}}

    def apply_one(self, node: tree_node.Node, attribute_dict: dict):
        for key, change in attribute_dict.items():
            add_op = change.get(self.ATTRIBUTE_CHANGE_ADD, None)
            set_op = change.get(self.ATTRIBUTE_CHANGE_SET, None)
            new_key_op = change.get(self.ATTRIBUTE_CHANGE_NEW_KEY, None)
            delete_op = change.get(self.ATTRIBUTE_CHANGE_DELETE, None)
            if add_op != None:
                if key == "__name__":
                    node.name = add_op["value"]
                else:
                    node.attributes[key] = add_op["value"]
            elif set_op != None:
                if key == "__name__":
                    node.name = set_op["value"]
                else:
                    node.attributes[key] = set_op["value"]
            elif delete_op != None:
                print("DO DELETE")
                print(node.attributes, key)
                if key in node.attributes:
                    del node.attributes[key]
                print(node.attributes, key)
            elif new_key_op != None:
                if key in node.attributes:
                    del node.attributes[key]
                node.attributes[new_key_op["new_key"]] = new_key_op["value"]

    def do_combine(self, operation):
        print("combine self:", self.arg_attribute_dict)
        print("     them:", operation.arg_attribute_dict)

        for key, their_change in operation.arg_attribute_dict.items():
            if key not in self.arg_attribute_dict:
                self.arg_attribute_dict[key] = their_change
                continue
            our_change = self.arg_attribute_dict[key]
            # Error cases
            if our_change.get(self.ATTRIBUTE_CHANGE_DELETE, None) != None:
                if their_change.get(self.ATTRIBUTE_CHANGE_SET, None) != None:
                    # Reject attempts to delete or rename a key that we have deleted
                    continue
            # if we delete something that was previously added, we should NOT add it
            # if we set something that was previously added, we should STILL add it
            # if we rename something that was previously added, we should add the new neame
            if our_change.get(self.ATTRIBUTE_CHANGE_ADD, None) != None:
                set_op = their_change.get(self.ATTRIBUTE_CHANGE_SET, None)
                new_key_op = their_change.get(self.ATTRIBUTE_CHANGE_NEW_KEY, None)
                delete_op = their_change.get(self.ATTRIBUTE_CHANGE_DELETE, None)
                if set_op != None:
                    self.prepare_add(key, set_op["value"])
                elif new_key_op != None:
                    del self.arg_attribute_dict[key]
                    self.prepare_add(new_key_op["new_key"], new_key_op["value"])
                elif delete_op != None:
                    del self.arg_attribute_dict[key]
                continue
            self.arg_attribute_dict[key] = their_change
        return True


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
                OperationArg("added_nodes", False, OperationArgType.TYPE_INTERNAL),
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

    def apply(self, root_node: tree_node.Node):
        if not self.arg_added_nodes:
            self.arg_added_nodes = {}
        super().apply(root_node)

    def replay(self, root_node: tree_node.Node):
        for parent_uid in self.arg_added_nodes:
            parent = root_node.find_node(node_uid=parent_uid)
            children = self.arg_added_nodes[parent_uid]
            parent.add_children(
                [tree_node.Node(child["name"], uid=child["uid"]) for child in children]
            )

    def apply_one(
        self,
        node: tree_node.Node,
        node_name: str,
        num_times: int,
        increment: bool,
        select_new_nodes: bool,
        added_nodes: list,
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
        node.add_children(children)
        self.arg_added_nodes[node.uid] = [
            {"name": child.name, "uid": child.uid} for child in children
        ]
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

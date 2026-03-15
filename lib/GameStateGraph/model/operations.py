import itertools

from .operation_base import (
    OperationBase,
    OperationContextValid,
    OperationArg,
    OperationArgType,
    InvalidNodeError,
    RunStatus,
    RunMode,
)
from . import game_state
from . import selection_hint
from . import tree_node

from nicegui import ui


class OperationTypeOnlyOne(OperationBase):
    operate_type = OperationBase.OPERATE_ONLY_ONE
    operation_contexts_valid: list[OperationContextValid] = []

    def invalid_nodes(self, root_node: tree_node.Node):
        nodes_selected = self.get_nodes(root_node)
        if len(nodes_selected) < 1:
            return InvalidNodeError(nodes_selected, "Needs a node selected")
        if len(nodes_selected) > 1:
            return InvalidNodeError(nodes_selected, "Only applies to a single node")


class OperationSetAttributes(OperationBase):
    operate_type = OperationBase.OPERATE_SINGLE
    operation_contexts_valid: list[OperationContextValid] = (
        []
    )  # Set is managed internally
    ATTRIBUTE_CHANGE_ADD = "add"  # {'value': 'blah'}
    ATTRIBUTE_CHANGE_SET = "set"  # {'value': 'blah'}
    ATTRIBUTE_CHANGE_NEW_KEY = "new_key"  # {'new_key': 'blah', 'new_value': 'blah'}
    ATTRIBUTE_CHANGE_DELETE = "delete"  # {}
    """ Attribute dict:
    some_key: {attribute_change_type: {args}}"""
    args = [OperationArg("attribute_dict", {}, OperationArgType.TYPE_INTERNAL)]
    name = "set"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.arg_attribute_dict: dict = {}

    def prepare_add(self, key, value):
        self.arg_attribute_dict[key] = {self.ATTRIBUTE_CHANGE_ADD: {"value": value}}

    def prepare_set(self, key, value):
        self.arg_attribute_dict[key] = {self.ATTRIBUTE_CHANGE_SET: {"value": value}}

    def prepare_rename(self, key, new_key, value):
        # Having the value here makes the combination business logic easier
        self.arg_attribute_dict[key] = {
            self.ATTRIBUTE_CHANGE_NEW_KEY: {"new_key": new_key, "value": value}
        }

    def prepare_delete(self, key):
        self.arg_attribute_dict[key] = {self.ATTRIBUTE_CHANGE_DELETE: {}}

    def apply_one(self, node: tree_node.Node):
        attribute_dict = self.arg_attribute_dict
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
        # TODO not handled - alter operation such that it is a no-op
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
    operation_contexts_valid: list[OperationContextValid] = [
        OperationContextValid.SINGLE_STATE
    ]
    args = [
        OperationArg("node_name", "Node"),
        OperationArg("times", 1, OperationArgType.TYPE_DECIMAL),
        OperationArg("increment_names", False, OperationArgType.TYPE_BOOLEAN),
        OperationArg("concat_names", "", OperationArgType.TYPE_STRING),
        OperationArg("select_new_nodes", False, OperationArgType.TYPE_BOOLEAN),
        OperationArg("added_nodes", False, OperationArgType.TYPE_INTERNAL),
    ]
    name = "add"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        old_validate = self.args[1].validate

        def validate_times(value):
            old = old_validate(value)
            if old:
                return old
            if int(value) < 1:
                return "Must be >= 1"

        self.args[1].validate = validate_times

    def get_concat_names(self):
        categories = [
            category.strip().split(",") for category in self.arg_concat_names.split(" ")
        ]
        names = [
            self.arg_node_name + ":" + " - ".join(items)
            for items in itertools.product(*categories)
        ]
        return names

    def before_apply(self, root_node: tree_node.Node):
        if not self.arg_added_nodes:
            self.arg_added_nodes = {}
        if self.arg_concat_names:
            self.arg_times = len(self.get_concat_names())

    def replay(self, root_node: tree_node.Node):
        def f():
            for parent_uid in self.arg_added_nodes:
                parent = root_node.find_node(node_uid=parent_uid)
                children = self.arg_added_nodes[parent_uid]
                parent.add_children(
                    [
                        tree_node.Node(child["name"], uid=child["uid"])
                        for child in children
                    ]
                )
                self.recent_run = RunStatus(success=True, mode=RunMode.REPLAY)

        self.perform_with_run_status(f, mode=RunMode.REPLAY)

    def apply_one(self, node: tree_node.Node):
        names = []

        if self.arg_increment_names:
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
                if child_name == self.arg_node_name + str(start):
                    start += 1
            for t in range(int(self.arg_times)):
                names.append(self.arg_node_name + str(start))
                start += 1
        elif self.arg_concat_names:
            names = self.get_concat_names()
        else:
            names = [self.arg_node_name] * int(self.arg_times)
        ui.notify(f"Adding nodes {names} to {node.name}")
        children = []
        for name in names:
            child = tree_node.Node(name)
            children.append(child)
        node.add_children(children)
        self.arg_added_nodes[node.uid] = [
            {"name": child.name, "uid": child.uid} for child in children
        ]
        if self.arg_select_new_nodes:
            return selection_hint.SelectionHint(children, children[0], True)


class OperationMoveNodes(OperationBase):
    operate_type = OperationBase.OPERATE_MANY_ONE
    operation_contexts_valid: list[OperationContextValid] = [
        OperationContextValid.SINGLE_STATE,
        OperationContextValid.GAME_STATE,
    ]
    args = {}
    name = "move"

    def apply_many_one(self, from_nodes: list[tree_node.Node], to_node: tree_node.Node):
        for node in from_nodes:
            node.reparent(to_node)


class OperationMoveNodesUp(OperationBase):
    operate_type = OperationBase.OPERATE_SINGLE
    operation_contexts_valid: list[OperationContextValid] = [
        OperationContextValid.SINGLE_STATE,
        OperationContextValid.GAME_STATE,
    ]
    args = {}
    name = "moveup"

    def apply_one(self, node: tree_node.Node):
        i = node.parent.children.index(node)
        if i > 0:
            node.parent.children[i], node.parent.children[i - 1] = (
                node.parent.children[i - 1],
                node.parent.children[i],
            )


class OperationMoveNodesDown(OperationBase):
    operate_type = OperationBase.OPERATE_SINGLE
    operation_contexts_valid: list[OperationContextValid] = [
        OperationContextValid.SINGLE_STATE,
        OperationContextValid.GAME_STATE,
    ]
    args = {}
    name = "movedown"

    def get_nodes(self, root_node):
        # Reverse the order of nodes so that when we move down, we move the bottom ones first, otherwise we can get into a situation where we move a node down, then the node that was below it is now above it and doesn't get moved
        return list(reversed(super().get_nodes(root_node)))

    def apply_one(self, node: tree_node.Node):
        i = node.parent.children.index(node)
        if i < len(node.parent.children) - 1:
            node.parent.children[i], node.parent.children[i + 1] = (
                node.parent.children[i + 1],
                node.parent.children[i],
            )


class OperationShuffle(OperationBase):
    operate_type = OperationBase.OPERATE_MANY
    operation_contexts_valid: list[OperationContextValid] = [
        OperationContextValid.SINGLE_STATE,
        OperationContextValid.GAME_STATE,
    ]
    args = [
        OperationArg("positions", False, OperationArgType.TYPE_INTERNAL),
    ]
    name = "shuffle"

    def before_apply(self, root_node):
        if not self.arg_positions:
            self.arg_positions = {}
            keys = [child.uid for child in self.get_nodes(root_node)]
            positions = [
                child.parent.children.index(child)
                for child in self.get_nodes(root_node)
            ]
            import random

            random.shuffle(keys)
            positions.sort()
            for i, key in enumerate(keys):
                self.arg_positions[key] = positions[i]

    def apply_many(self, nodes):
        for node in nodes:
            parent = node.parent
            position = self.arg_positions[node.uid]
            parent.children[position] = node

    def invalid_nodes(self, root_node):
        nodes_selected = self.get_nodes(root_node)
        if any(1 for node in nodes_selected if node.parent != nodes_selected[0].parent):
            return InvalidNodeError(
                self.node_uids_selected,
                f"All nodes must have the same parent to shuffle",
            )


class OperationDeleteNode(OperationBase):
    operate_type = OperationBase.OPERATE_SINGLE
    operation_contexts_valid: list[OperationContextValid] = [
        OperationContextValid.SINGLE_STATE,
        OperationContextValid.GAME_STATE,
    ]
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


class OperationDeleteAndShiftNode(OperationBase):
    operate_type = OperationBase.OPERATE_SINGLE
    operation_contexts_valid: list[OperationContextValid] = [
        OperationContextValid.SINGLE_STATE,
        OperationContextValid.GAME_STATE,
    ]
    name = "delete/shift"

    def invalid_nodes(self, root_node: tree_node.Node):
        nodes_selected = self.get_nodes(root_node)
        invalid = [node for node in nodes_selected if node.is_root]
        if invalid:
            return InvalidNodeError(
                invalid, f"Cannot delete a root node {[node.uid for node in invalid]}"
            )

    def apply_one(self, node: tree_node.Node):
        node.parent.children.remove(node)
        for child in node.children:
            child.reparent(node.parent)
        node.parent = None


class OperationAddNextGameState(OperationTypeOnlyOne):
    name = "next"
    operation_contexts_valid: list[OperationContextValid] = [
        OperationContextValid.GAME_STATE
    ]

    def apply_one(self, node: game_state.GameState):
        print("add next state")
        next = node.add_next()
        return selection_hint.SelectionHint([next], next, True)


class OperationAddBranchingGameState(OperationTypeOnlyOne):
    name = "branch"
    operation_contexts_valid: list[OperationContextValid] = [
        OperationContextValid.GAME_STATE
    ]

    def apply_one(self, node: game_state.GameState):
        print("add branching state")
        next = node.add_branch()
        return selection_hint.SelectionHint([next], next, True)

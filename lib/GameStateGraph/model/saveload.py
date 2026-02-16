from . import tree_node
from . import operation_base
from . import operations
from . import game_state
from . import operation_queue
from enum import Enum


class ClassRef:
    def __init__(self, name, class_):
        self.name = name
        self.class_ = class_


class Saver:
    # Precedence of how objects are saved and loaded - if object classes match earlier it will use that one
    classes = [
        ClassRef("operation", operation_base.OperationBase),
        ClassRef("operationqueue", operation_queue.OperationQueue),
        ClassRef("gamestate", game_state.GameState),
        ClassRef("gamestatetree", game_state.GameStateTree),
        ClassRef("node", tree_node.Node),
    ]

    def __init__(self):
        pass

    def to_dict(self, object):
        for class_ref in self.classes:
            if isinstance(object, class_ref.class_):
                d = getattr(self, "to_dict_" + class_ref.name)(object)
                d["class_ref"] = class_ref.name
                return d
        raise Exception(
            f"Couldn't find to_dict_(class_ref) for class {object.__class__.__name__}"
        )

    def from_dict(self, d):
        print("LOAD OBJECT", d["class_ref"], d.get("name", ""))
        for class_ref in self.classes:
            if class_ref.name == d["class_ref"]:
                object = getattr(self, "from_dict_" + class_ref.name)(d)
                assert object
                return object
        raise Exception(
            f"Couldn't find from_dict_(class_ref) for class {object.__class__.__name__}"
        )

    def to_dict_node(self, node):
        d = {}
        d["name"] = node.name
        d["children"] = [self.to_dict(child) for child in node.children]
        print("len children", len(d["children"]))
        d["compress"] = node.compress
        d["is_root"] = node.is_root
        d["uid"] = node.uid
        d["attributes"] = node.attributes
        return d

    def from_dict_node(self, d, create_class=tree_node.Node):
        n = create_class(
            name=d["name"],
            children=[self.from_dict(child_d) for child_d in d["children"]],
            compress=d["compress"],
            is_root=d["is_root"],
            uid=d["uid"],
            attributes=d["attributes"],
        )
        if n.is_root:
            n.update_tree()
        return n

    def to_dict_gamestate(self, game_state_node):
        d = self.to_dict_node(game_state_node)
        d["operation_queue"] = self.to_dict(game_state_node.operation_queue)
        d["_initial_state"] = self.to_dict(game_state_node._initial_state)
        d["current_state"] = self.to_dict(game_state_node.current_state)
        d["action_level"] = game_state_node.action_level
        return d

    def from_dict_gamestate(self, d, create_class=game_state.GameState):
        gs = self.from_dict_node(d, create_class)
        gs.operation_queue = self.from_dict(d["operation_queue"])
        gs._initial_state = self.from_dict(d["_initial_state"])
        gs.current_state = self.from_dict(d["current_state"])
        gs.action_level = d["action_level"]
        return gs

    def to_dict_gamestatetree(self, game_state_tree):
        return self.to_dict_node(game_state_tree)

    def from_dict_gamestatetree(self, d, create_class=game_state.GameStateTree):
        return self.from_dict_node(d, create_class)

    def to_dict_operationqueue(self, oq):
        d = {}
        d["queue"] = [self.to_dict(operation) for operation in oq.queue]
        return d

    def from_dict_operationqueue(self, d):
        q = operation_queue.OperationQueue()
        for op in d["queue"]:
            q.queue.append(self.from_dict(op))
        return q

    def to_dict_operation(self, operation: operation_base.OperationBase):
        d = {}
        d["operation_class"] = operation.__class__.__name__
        assert (d["operation_class"]) in dir(operations)
        d["args"] = operation.get_args()
        d["node_uids_selected"] = operation.node_uids_selected
        return d

    def from_dict_operation(self, d):
        class_ = getattr(operations, d["operation_class"])
        operation = class_(d["node_uids_selected"])
        operation.applied = True
        for arg in d["args"]:
            setattr(operation, "arg_" + arg, d["args"][arg])
        return operation

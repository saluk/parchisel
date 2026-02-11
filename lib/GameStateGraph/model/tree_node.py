"""
TODO
- save/load state tree
- nicegui exposes initial state generation
- save state change commands instead of individual states and generate entire tree
        - show states that are invalid after a state change command
"""

import copy, random

import uuid


class Node:
    def __init__(
        self,
        name=None,
        children=None,
        compress=False,
        is_root=False,
        uid=None,
        **kwargs,
    ):
        self.name = name
        self.attributes = kwargs
        if not children:
            children = []
        self.children: list[Node] = children
        self.compress = compress

        self.uid: str = uid or str(uuid.uuid4())

        self.is_root = is_root  # The root node will keep track of ids as an attribute
        self.root: Node = None
        self.parent: Node = None

        self.recursive_update = True
        self.name_cache = {}

        if self.is_root:
            self.root = self
            self.uid = 0
            self.dirty = True
            self.update_tree()

    def update_tree(self):
        if self.is_root:
            print("call update tree on a root", self.dirty)
            if self.dirty:
                self.dirty = False
                self._annotate_subtree()
                self.dirty = True
        elif self.root:
            self.root.update_tree()
        else:
            raise Exception("A Node should always either be the root or have a root")

    def _annotate_subtree(self):
        if not self.is_root:
            raise Exception("Only the root should call annotate_subtree")
        # print("- call annotate from "+self.fullname()+" -")
        self.name_cache[:] = {}
        self.root = self
        for node in self.walk():
            # print("-- walking node", node.fullname(),"--")
            self.name_cache[node.fullname()] = node
            if node == self:
                continue
            node.root = self
            node.is_root = False

    def walk(self):
        """Iterator to get all nodes, with depth-first search.
        Also as a side effect ensures nodes point to correct parent"""
        search_nodes = [self]
        while search_nodes:
            cur_node = search_nodes.pop()
            yield cur_node
            for child_node in cur_node.children:
                child_node.parent = cur_node
                search_nodes.append(child_node)

    def find_node(self, node_name: str = None, node_uid: str = None):
        assert (isinstance(node_name, str) or node_name == None) and (
            isinstance(node_uid, str) or node_uid == None
        )
        print(
            "find node in:",
            self.root.name,
            "node_name",
            node_name,
            "node_uid",
            node_uid,
        )
        for node in self.walk():
            if node.uid == node_uid or node.name == node_name:
                return node
            if (
                isinstance(node_name, str)
                and "." in node_name
                and node.fullname().endswith(node_name)
            ):
                return node
        return None

    def get_index(self):
        if not self.parent:
            return 0
        return self.parent.children.index(self)

    def reparent(self, parent):
        """Moves a node from its current parent to the parent with the given name"""
        self.parent.children.remove(self)
        parent.children.append(self)
        self.update_tree()

    def delete_children(self):
        self.children[:] = []

    def add_children(self, children):
        self.root.dirty = True
        self.children.extend(children)
        print("add children", self.root.dirty)
        self.update_tree()
        return self

    def fullname(self):
        n = self.name
        p = self.parent
        while p:
            n = p.name + "." + n
            p = p.parent
        return n

    def copy(self):
        copied = copy.copy(self)
        copied.attributes = copy.copy(self.attributes)
        copy_children = [copied]
        while copy_children:
            next_copy = copy_children.pop(0)
            new_children = []
            for i in range(len(next_copy.children)):
                new_children.append(next_copy.children[i].copy())
                copy_children.append(next_copy.children[i])
            next_copy.children = new_children
        if copied.is_root:
            print("COPYING ROOT", copied)
            copied.dirty = True
            copied.update_tree()
            print(copied.children[0].root == copied)
            print(copied.children[0].root != self.children[0].root)
            self.recursive_update = True
        else:
            print("COPYING NON-ROOT", copied)
        return copied

    def to_dict(self):
        d = {}
        d["name"] = self.name
        d["children"] = [child.to_dict() for child in self.children]
        d["compress"] = self.compress
        d["is_root"] = self.is_root
        d["attributes"] = self.attributes
        return d

    @staticmethod
    def from_dict(d):
        n = Node(
            d["name"],
            [Node.from_dict(child_d) for child_d in d["children"]],
            d["compress"],
            d["is_root"],
        )
        n.attributes = d["attributes"]
        if n.is_root:
            n.update_tree()
        return n

    def apply_operation(self, operation):
        """Apply an operation which may change the graph"""
        print(
            "Node.apply_operation name, uid, root:", self.name, self.uid, self.root.name
        )
        return operation.apply(self.root)

    def check_operation_valid(self, operation):
        """Determine whether an operation can be performed"""
        return operation.invalid_nodes(self.root)


def print_state(node):
    next = [(node, 0)]
    while next:
        next_node: Node = None
        next_node, indent = next.pop(0)
        print(
            "   " * indent + next_node.name + " - ",
            next_node.uid,
            "r:",
            next_node.root.uid if next_node.root else "_",
        )
        for k in sorted(next_node.attributes.keys()):
            print("   " * indent + ":" + k + ":" + str(next_node.attributes[k]))
        if next_node.compress and next_node.children:
            print(
                "   " * (indent + 1)
                + ">"
                + ", ".join(
                    [
                        child.name + " - " + str(next_node.uid)
                        for child in next_node.children
                    ]
                )
            )
        else:
            for child in reversed(next_node.children):
                next.insert(0, (child, indent + 1))

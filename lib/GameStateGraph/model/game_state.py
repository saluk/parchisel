from .tree_node import Node, print_state
from .operation_queue import OperationQueue

import itertools, random, copy

random.seed(50)


def prod(*lists):
    return [x for x in itertools.product(*lists)]


def shuffled(l):
    newl = [x for x in l]
    random.shuffle(newl)
    return newl


class GameState(Node):
    """A GameState contains the actual state (to keep tree roots separate) as well as a stack
    of actions that was performed on the parent game state to get to this state"""

    def __init__(self, initial_state, action_level=1):
        super().__init__()
        self.operation_queue = OperationQueue()
        self.initial_state = initial_state
        self.current_state = initial_state
        self.action_level = action_level

    @property
    def name(self):
        return "state" + str(self.action_level)

    @name.setter
    def name(self, value):
        pass

    def apply_gamestate_operation(self, operation):
        print(
            "GameState.apply_gamestate_operation",
            self.uid,
            self.name,
            self.current_state.name,
        )
        try:
            operation_result = self.current_state.apply_operation(operation)
            print(f"Result:{operation_result}")
            self.operation_queue.add(operation, self)
            print(f"Stack:{repr(self.operation_queue)}")
            return operation_result
        except:
            raise

    def add_branch(self, branch_name: str = None):
        """Make a new sibling clone of this state as an alternate move"""
        state = self.copy()
        state.delete_children()
        print(id(self.attributes), id(state.attributes))
        if branch_name:
            state.attributes["branch_name"] = branch_name
        state.attributes["game_state_owner"] = self
        self.parent.add_children([state])
        return state

    def add_next(self):
        """Make a new child clone of this state as the next move"""
        state = self.copy()
        state.delete_children()
        state.action_level += 1
        state.attributes["game_state_owner"] = self
        self.add_children([state])
        print_state(self)
        return state

    def copy(self):
        state = super().copy()
        state.uid = None
        state.current_state = self.current_state.copy()
        state.initial_state = self.initial_state.copy()
        # Each state has its own operation_queue
        state.operation_queue = OperationQueue()
        return state


class GameStateTree(Node):
    """A GameStateTree is a tree of GameStates.
    Each child GameState is a different decision which is made on the current state
    GameStateTree
            state1
                    state2
                            state3
                                    state4
                                            state5
                                            state6
                                    state4
                                            state5
                                            state6
            state1
                    state2
                            state3
    """

    def __init__(self):
        super().__init__("GameStateTree", is_root=True)

    def update_tree(self):
        super().update_tree()
        for node in self.walk():
            if isinstance(node, GameState):
                node.current_state.update_tree()


def test_annotate_tree():
    state1 = Node(
        "s1.1",
        [
            Node("2", [Node("3"), Node("4"), Node("5")]),
            Node("6", [Node("7"), Node("8", [Node("9")])]),
        ],
        is_root=True,
    )
    gs_tree = GameStateTree()
    gs1 = GameState(state1)
    gs_tree.add_children([gs1])
    gs2 = gs1.add_next()
    gs2.current_state.name = "s2.1"
    gs2.current_state.uid = "2.0"
    print_state(gs_tree)
    print_state(gs1.current_state)
    print_state(gs2.current_state)
    assert gs1.current_state == state1
    assert gs2.current_state != gs1.current_state
    assert gs1.current_state.root != gs2.current_state.root


test_annotate_tree()

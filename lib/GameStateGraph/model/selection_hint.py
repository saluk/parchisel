from . import tree_node


class SelectionHint:
    """Which nodes should be selected or ticked after an operation"""

    def __init__(
        self,
        new_nodes_ticked: list[tree_node.Node],
        new_node_selected: tree_node.Node,
        erase_ticked: bool,
    ):
        self.new_nodes_ticked = new_nodes_ticked
        self.new_node_selected = new_node_selected
        self.erase_ticked = erase_ticked

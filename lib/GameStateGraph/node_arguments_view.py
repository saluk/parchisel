# Shows options for a selected set of Nodes
from __future__ import annotations

from nicegui.elements.dialog import Dialog
from lib.GameStateGraph.model import tree_node
from lib.GameStateGraph.model import operation_base
from lib.GameStateGraph import state_tree_view
from nicegui import ui, html


class SingleNodeArgumentsView:
    def __init__(
        self,
        node_selected: tree_node.Node,
        parent: state_tree_view.StateTreeView,
    ) -> None:
        self.node_selected: tree_node.Node = node_selected
        self.parent: state_tree_view.StateTreeView = parent

    def refresh(self):
        self.build.refresh()

    @ui.refreshable
    async def build(self) -> None:
        ui.notify("building")
        if not self.node_selected:
            return

        def name_change_operation(e):
            # TODO this should apply an operation instead
            self.node_selected.name = e.value
            # TODO slow and should be handled by the state view
            for node in self.parent.treeElement.nodes():
                if node["uid"] == self.node_selected.uid:
                    node["name"] = e.value

        with ui.card():
            ui.input(value=self.node_selected.name).on_value_change(
                name_change_operation
            )

# Shows options for a selected set of Nodes
from __future__ import annotations

from nicegui.elements.dialog import Dialog
from lib.GameStateGraph.model import tree_node
from lib.GameStateGraph.model import operation_base
from lib.GameStateGraph.model import operations
from lib.GameStateGraph import state_tree_view
from nicegui import ui, html


class SingleNodeAttributesView:
    def __init__(
        self,
        node_selected: tree_node.Node,
        parent: state_tree_view.StateTreeView,
    ) -> None:
        self.node_selected: tree_node.Node = node_selected
        self.parent: state_tree_view.StateTreeView = parent

    def refresh(self):
        self.build.refresh()

    def update_operation(self, refresh=True):
        self.parent.refresh_tree()
        self.parent.refresh_ops()
        if refresh:
            self.refresh()

    def set_attribute_value(self, node, key, value, delete_key=None, refresh=False):
        operation = operations.OperationSetAttributes([node.uid])
        if key != None and delete_key != None:
            operation.prepare_rename(delete_key, key, value)
        elif key != None:
            if key != "__name__" and key not in node.attributes:
                operation.prepare_add(key, value)
            else:
                operation.prepare_set(key, value)
        elif delete_key != None:
            operation.prepare_delete(delete_key)
            refresh = True
        self.parent.game_state.apply_gamestate_operation(operation)
        self.update_operation(refresh=refresh)

    @ui.refreshable
    async def build(self) -> None:
        ui.notify("building")
        if not self.node_selected:
            return

        self.new_key_name = ""
        self.new_key_value = ""
        self.new_keyvalue_set = False

        def change_new_input():
            self.new_keyvalue_set = self.new_key_name and self.new_key_value

        with ui.card():
            ui.input(value=self.node_selected.name).on_value_change(
                lambda e: self.set_attribute_value(
                    self.node_selected, "__name__", e.value
                )
            )
            ui.separator()
            ui.label("-- Attributes --")
            if not self.node_selected.attributes:
                ui.markdown("(No attributes)")
            for key, value in self.node_selected.attributes.items():
                with ui.row():
                    ui.input("Name:", value=key).on_value_change(
                        lambda e: self.set_attribute_value(
                            self.node_selected, e.value, value, e.previous_value
                        )
                    )
                    ui.input("Value:", value=value).on_value_change(
                        lambda e: self.set_attribute_value(
                            self.node_selected, key, e.value
                        )
                    )
                    ui.button("-").on_click(
                        lambda e: self.set_attribute_value(
                            self.node_selected, None, None, delete_key=key
                        )
                    )
            ui.label("-- Add new attribute --")
            with ui.row():
                ui.input("New Name:").bind_value(self, "new_key_name").on_value_change(
                    change_new_input
                )
                ui.input("New Value:").bind_value(
                    self, "new_key_value"
                ).on_value_change(change_new_input)
                ui.button("+").on_click(
                    lambda e: self.set_attribute_value(
                        self.node_selected,
                        self.new_key_name,
                        self.new_key_value,
                        None,
                        refresh=True,
                    )
                ).bind_enabled(self, "new_keyvalue_set")

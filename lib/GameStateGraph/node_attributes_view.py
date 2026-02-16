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
        self.operation = operations.OperationSetAttributes([])

    def refresh(self):
        # TODO this is a long access probably want to simplify
        queue = self.parent.game_state.operation_queue.queue
        if (
            queue
            and queue[-1].node_uids_selected == [self.node_selected.uid]
            and isinstance(queue[-1], operations.OperationSetAttributes)
        ):
            self.operation = queue[-1]
        else:
            self.operation = operations.OperationSetAttributes([self.node_selected.uid])
        # TODO if the last operation in the queue is also a set attribute operation with the same node, we should make that our operation
        self.build.refresh()

    def update_operation(self, refresh=True):
        self.parent.game_state.apply_gamestate_operation(
            self.operation, self.operation.applied == False
        )
        self.parent.regen_tree()
        if refresh:
            self.refresh()

    @ui.refreshable
    async def build(self) -> None:
        ui.notify("building")
        if not self.node_selected:
            return

        def name_change_operation(e):
            self.operation.arg_attribute_dict["__name__"] = e.value
            self.update_operation(refresh=False)

        def existing_key_rename_operation(old_key, new_key):
            if old_key in self.node_selected.attributes:
                value = self.node_selected.attributes[old_key]
                if old_key in self.operation.arg_attribute_dict:
                    del self.operation.arg_attribute_dict[old_key]
                self.operation.arg_attribute_dict[new_key] = value
                self.operation.arg_delete_attribute_list.append(old_key)
                self.update_operation(refresh=False)

        def existing_key_value_set(old_key, new_value):
            if old_key in self.operation.arg_delete_attribute_list:
                self.operation.arg_delete_attribute_list.remove(old_key)
            self.operation.arg_attribute_dict[old_key] = new_value
            self.update_operation()

        def remove_attribute(old_key):
            if old_key not in self.operation.arg_delete_attribute_list:
                self.operation.arg_delete_attribute_list.append(old_key)
            if old_key in self.operation.arg_attribute_dict:
                del self.operation.arg_attribute_dict[old_key]
            self.update_operation()

        self.new_key_name = ""
        self.new_key_value = ""
        self.new_keyvalue_set = False

        def change_new_input():
            self.new_keyvalue_set = self.new_key_name and self.new_key_value

        def save_new_attribute(e):
            existing_key_value_set(self.new_key_name, self.new_key_value)

        with ui.card():
            ui.input(value=self.node_selected.name).on_value_change(
                name_change_operation
            )
            ui.separator()
            ui.label("-- Attributes --")
            if not self.node_selected.attributes:
                ui.markdown("(No attributes)")
            for key, value in self.node_selected.attributes.items():
                with ui.row():
                    ui.input("Name:", value=key).on_value_change(
                        lambda e: existing_key_rename_operation(
                            e.previous_value, e.value
                        )
                    )
                    ui.input("Value:", value=value).on_value_change(
                        lambda e: existing_key_value_set(key, e.value)
                    )
                    ui.button("-").on_click(lambda e: remove_attribute(key))
            ui.label("-- Add new attribute --")
            with ui.row():
                ui.input("New Name:").bind_value(self, "new_key_name").on_value_change(
                    change_new_input
                )
                ui.input("New Value:").bind_value(
                    self, "new_key_value"
                ).on_value_change(change_new_input)
                ui.button("+").on_click(save_new_attribute).bind_enabled(
                    self, "new_keyvalue_set"
                )

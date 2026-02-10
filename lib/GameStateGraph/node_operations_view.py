# Shows options for a selected set of Nodes
from __future__ import annotations

from nicegui.elements.dialog import Dialog
from lib.GameStateGraph import gamestategraph
from lib.GameStateGraph import operations
from lib.GameStateGraph import state_tree_view
from nicegui import ui, html


class NodeOperationsView:
    def __init__(
        self,
        nodes_ticked: list[gamestategraph.Node],
        state: gamestategraph.Node,
        allowed_operations: list[operations.OperationBase],
        parent: state_tree_view.StateTreeView,
    ) -> None:
        self.ticked_nodes: list[gamestategraph.Node] = nodes_ticked
        self.state: gamestategraph.Node = state
        self.operations_dialog = None
        self.allowed_operations = allowed_operations
        self.parent = parent
        super().__init__()

    def refresh(self):
        self.build.refresh()

    def from_nodes(self):
        if len(self.ticked_nodes) <= 1:
            return []
        return self.ticked_nodes[:-1]

    def to_node(self):
        if len(self.ticked_nodes) <= 1:
            return []
        return self.ticked_nodes[-1]

    def nodes_string(self, nodes, length=30):
        s = "{"
        first = True
        i = 0
        while len(s) < length and i < len(nodes):
            if not first:
                s += ","
            s += nodes[i].name
            first = False
            i += 1
        if i < len(nodes) - 1:
            s += ",..."
        s += "}"
        return s

    async def on_click_operation(
        self, operation_class: operations.OperationBase.__class__
    ):
        self.current_operation = operation_class(
            [node.uid for node in self.ticked_nodes]
        )
        if self.current_operation.args:
            self.show_dialog()
        else:
            print("apply operation on its own")
            await self.parent.apply_operation(self.current_operation)

    def show_dialog(self):
        operation = self.current_operation
        if self.operations_dialog:
            self.operations_dialog.clear()

        async def confirm() -> None:
            print("Applying operation:", self.parent.state.name)
            await self.parent.apply_operation(self.current_operation)
            self.operations_dialog.close()

        with ui.dialog() as dialog, ui.card():
            ui.label(operation.name)
            for arg in operation.args.values():
                if arg.input_type() == operations.OperationArgInputType.INPUT:
                    ui.input(arg.name, validation=arg.validate).bind_value(
                        operation, "arg_" + arg.name
                    )
                elif arg.input_type() == operations.OperationArgInputType.CHECK:
                    print(arg.default)
                    ui.checkbox(arg.name).bind_value(operation, "arg_" + arg.name)
            ui.button("Confirm", on_click=confirm)
            ui.button("Close", on_click=dialog.close)
        self.operations_dialog: Dialog = dialog
        self.operations_dialog.open()

    @ui.refreshable
    async def build(self) -> None:
        with ui.context_menu() as self.root_widget:
            with ui.card():
                ui.label(self.state.name)
                with ui.row():
                    ui.button("Select None", on_click=self.parent.select_none)
                    await self.parent.select_range_button.build()
                ui.separator()
                with ui.row():
                    with html.section():
                        html.span("Selected: ")
                        html.strong(self.nodes_string(self.ticked_nodes))
                with ui.row():
                    ui.label("Operations")
                    if not self.ticked_nodes:
                        ui.label("No nodes selected")
                        return
                    with ui.row():
                        print(self.allowed_operations)
                        for operation_class in self.allowed_operations:
                            button = ui.button(
                                operation_class.name,
                                on_click=lambda op_class=operation_class: self.on_click_operation(
                                    op_class
                                ),
                            )
                            invalid = self.state.check_operation_valid(
                                operation_class(
                                    [node.uid for node in self.ticked_nodes]
                                )
                            )
                            if invalid:
                                button.disable()
                                button.tooltip(invalid.message)

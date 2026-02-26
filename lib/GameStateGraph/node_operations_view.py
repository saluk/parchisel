# Shows options for a selected set of Nodes
from __future__ import annotations

from nicegui.elements.dialog import Dialog
from lib.GameStateGraph.model import tree_node
from lib.GameStateGraph.model import operation_base
from lib.GameStateGraph import state_tree_view
from nicegui import ui, html


class NodeOperationsView:
    def __init__(
        self,
        nodes_ticked: list[tree_node.Node],
        state: tree_node.Node,
        allowed_operations: list[operation_base.OperationBase],
        parent: state_tree_view.StateTreeView,
    ) -> None:
        self.ticked_nodes: list[tree_node.Node] = nodes_ticked
        self.state: tree_node.Node = state
        self.game_state = None
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
        self, operation_class: operation_base.OperationBase.__class__
    ):
        operation = operation_class([node.uid for node in self.ticked_nodes])
        if operation.args:
            self.show_operation_arguments_dialog(operation)
        else:
            print("apply operation on its own")
            await self.parent.apply_operation(operation)

    def show_operation_arguments_dialog(self, operation: operation_base.OperationBase):
        if self.operations_dialog:
            self.operations_dialog.clear()

        async def confirm() -> None:
            print("Applying operation:", self.parent.state.name)
            await self.parent.apply_operation(operation)
            self.operations_dialog.close()

        with ui.dialog() as dialog, ui.card():
            ui.label(operation.name + " " + str(id(operation)))
            for arg in operation.args:
                if arg.input_type() == operation_base.OperationArgInputType.INPUT:
                    ui.input(arg.name, validation=arg.validate).bind_value(
                        operation, "arg_" + arg.name
                    )
                elif arg.input_type() == operation_base.OperationArgInputType.CHECK:
                    print(arg.default)
                    ui.checkbox(arg.name).bind_value(operation, "arg_" + arg.name)
            ui.button("Confirm", on_click=confirm)
            ui.button("Close", on_click=dialog.close)
        self.operations_dialog: Dialog = dialog
        self.operations_dialog.open()

    def find_operators(self):
        operators = {"": None}
        for node in self.state.walk():
            if node.attributes.get("operator", None):
                operators[node.uid] = node.name
        return operators

    def set_operator(self, e):
        operators = self.find_operators()
        name = operators[e.value]
        self.game_state.operator = {"uid": e.value, "name": name}

    @ui.refreshable
    async def build(self) -> None:
        with ui.dialog() as self.main_dialog:
            with ui.card():
                with ui.row():
                    ui.label(self.state.name)
                    if self.game_state and self.find_operators():
                        operators = self.find_operators()
                        ui.select(
                            operators,
                            value=(
                                self.game_state.operator["uid"]
                                if self.game_state.operator
                                and self.game_state.operator["uid"] in operators
                                else ""
                            ),
                        ).on_value_change(self.set_operator)
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

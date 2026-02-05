# Shows options for a selected set of Nodes
from __future__ import annotations

from nicegui.elements.dialog import Dialog
from lib.GameStateGraph import gamestategraph
from lib.GameStateGraph import operations
from nicegui import ui, html

class NodeOperationsView:
    def __init__(self, nodes_ticked:list[gamestategraph.Node], state:gamestategraph.Node, allowed_operations:list[operations.OperationBase], parent:StateTreeView) -> None:
        self.ticked_nodes:list[gamestategraph.Node] = nodes_ticked
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
        while len(s)<length and i<len(nodes):
            if not first:
                s += ","
            s += nodes[i].name
            first = False
            i+=1
        if i<len(nodes)-1:
            s += ",..."
        s+="}"
        return s
    def on_click_operation(self, operation:operations.OperationBase):
        if operation.args:
            self.show_dialog(operation)
        else:
            print("apply operation on its own")
            operation.apply(self.ticked_nodes)
            self.parent.refresh()
    def show_dialog(self, operation:operations.OperationBase):
        if self.operations_dialog:
            self.operations_dialog.clear()
        async def confirm() -> None:
            operation.apply(self.ticked_nodes)
            self.state.update_tree()
            self.operations_dialog.close()
            self.parent.refresh()
        with ui.dialog() as dialog, ui.card():
            ui.label(operation.name())
            for arg in operation.args:
                if arg.input_type() == operations.OperationArgInputType.INPUT:
                    ui.input(arg.name,validation=arg.validate).bind_value(arg, "value")
                elif arg.input_type() == operations.OperationArgInputType.CHECK:
                    print(arg.default)
                    ui.checkbox(arg.name).bind_value(arg, "value")
            ui.button("Confirm", on_click=confirm)
            ui.button('Close', on_click=dialog.close)
        self.operations_dialog: Dialog = dialog
        self.operations_dialog.open()
    @ui.refreshable
    async def build(self) -> None:
        with ui.card():
            ui.label("Operations")
            if not self.ticked_nodes:
                ui.label("No nodes selected")
                return
            with ui.row():
                print(self.allowed_operations)
                for operation in self.allowed_operations:
                    print("build op",operation.name())
                    ui.button(operation.name(), on_click=lambda op=operation: self.on_click_operation(op))
            with html.section():
                html.span("Selected: ")
                html.strong(self.nodes_string(self.ticked_nodes)) 
from __future__ import annotations

from nicegui.elements.tree import Tree
from nicegui.elements.button import Button
from .model import game_state, tree_node
from .node_operations_view import NodeOperationsView
from .operation_queue_view import OperationQueueView
from .node_attributes_view import SingleNodeAttributesView
from .model import operations, operation_base, selection_hint
from nicegui import ui, html
import json


def get_ui_tree(state: tree_node.Node):
    d = {
        "compress": state.compress,
        "uid": state.uid,
        "fullname": state.fullname(),
        "name": state.name,
        "children": [get_ui_tree(child) for child in state.children],
    }
    # Within the state explorer, don't interact with root
    if state.is_root and isinstance(state, game_state.GameStateTree):
        d["tickable"] = False
        d["selectable"] = False
    # Within a given state, only tick
    # if not isinstance(state, GameState):
    # 	d["selectable"] = False
    return d


class SelectRangeButton:
    def __init__(self):
        self.active = False
        self.node_start: tree_node.Node = None
        self.node_end: tree_node.Node = None
        self.untick = False

    def get_label(self):
        if not self.active:
            return "Select Range"
        if self.node_start == None:
            return "Select Start Node"
        elif self.node_end == None:
            return "Select End Node"

    def enabled(self):
        return not self.active

    async def click(self) -> None:
        if not self.active:
            self.active = True
            self.node_start = None
            self.node_end = None
            self.build.refresh()
            return

    @ui.refreshable
    async def build(self):
        button = ui.button(self.get_label(), on_click=self.click)
        self.button = button
        self.update()
        return

    def update(self):
        self.button.text = self.get_label()
        if self.enabled():
            self.button.enable()
        else:
            self.button.disable()

    async def clicked_node(self, node, tree_view, untick=False):
        if not self.active:
            return
        if not self.node_start:
            self.untick = untick
            self.node_start = node
            self.update()
            return
        self.node_end = node
        self.active = False
        self.update()
        self.select_range(tree_view)
        return True

    def select_range(self, tree_view):
        if self.node_start.parent != self.node_end.parent:
            ui.notify("Range can only be selected between nodes at the same level")
            return False
        start_i = self.node_start.get_index()
        end_i = self.node_end.get_index()
        if start_i > end_i:
            start_i, end_i = end_i, start_i
        found = []
        while start_i <= end_i:
            found.append(self.node_start.parent.children[start_i])
            start_i += 1
        if not self.untick:
            [
                tree_view.nodes_ticked.insert(-1, node)
                for node in found
                if node not in tree_view.nodes_ticked
            ]
            tree_view.treeElement.tick([node.uid for node in found])
        else:
            [
                tree_view.nodes_ticked.remove(node)
                for node in found
                if node in tree_view.nodes_ticked
            ]
            tree_view.treeElement.untick([node.uid for node in found])
        return True


class StateTreeViewBase:
    width = "64"
    height = "48"
    allowed_operations: list[operation_base.OperationBase.__class__] = []

    def __init__(self, view, state=None, label="", game_state=None) -> None:
        self.view = view
        self.label = label
        self.state: tree_node.Node = state
        self.game_state: game_state.GameState = game_state

        self.treeElement = None
        self.nodes_ticked: list[tree_node.Node] = []
        self.node_selected: tree_node.Node = None

        self.select_range_button = SelectRangeButton()

        # A view of a selected node (or set of nodes) and their properties
        self.single_node_attributes_view = None

        # A view of operations to apply to the selected nodes
        self.node_operations_view = None

        self.nodes_ticked = []

    def refresh(self, reset_ticked=True) -> None:
        print("refresh stateTreeViewBase:", self.state.name)
        if reset_ticked:
            self.nodes_selected = None
            self.nodes_ticked[:] = []
        # If some nodes were deleted, we might need to update our selection
        if self.node_selected and not self.node_selected.parent:
            self.node_selected = None
        self.nodes_ticked[:] = [
            node for node in self.nodes_ticked if node and (node.parent or node.is_root)
        ]
        self.build.refresh()

    async def select_none(self) -> None:
        self.treeElement.untick(None)
        self.treeElement.deselect()
        self.nodes_ticked = []
        self.tick_node([])

    async def select_node_callback(self, e) -> None:
        print(e)
        if e.value != None:
            node: tree_node.Node | None = self.state.find_node(node_uid=e.value)
            self.node_selected = node
        if self.node_selected:
            await self.select_node(self.node_selected)

    async def select_node(self, node: tree_node.Node) -> None:
        pass

    async def tick_node_callback(self, e) -> None:
        print("tick node callback:", e)
        unticked = None
        for node in self.nodes_ticked:
            if node.uid not in e.value:
                unticked = node
                self.nodes_ticked.remove(node)
                if self.select_range_button.active:
                    await self.select_range_button.clicked_node(
                        unticked, self, untick=True
                    )
                    self.tick_node(self.nodes_ticked)
                    return
        self.nodes_ticked = []
        for uid in e.value:
            self.nodes_ticked.append(self.state.find_node(node_uid=uid))
        if self.nodes_ticked and await self.select_range_button.clicked_node(
            self.nodes_ticked[-1], self
        ):
            self.tick_node(self.nodes_ticked)
            return
        self.tick_node(self.nodes_ticked)

    def tick_node(self, nodes: list[tree_node.Node]) -> None:
        pass

    async def apply_operation(self, operation):
        print(f"APPLYING OPERATION {repr(operation)} TO: {self.state.name}")
        operation_result = self.state.apply_operation(operation)
        return await self.after_operation(operation_result)

    async def after_operation(self, operation_result):
        pass

    async def show_operations(self):
        pass

    @ui.refreshable
    async def build(self) -> None:
        if not self.state:
            ui.label("No state selected")
            return
        print("Building statetreeview", self.state.name)
        with ui.card():
            with ui.dialog() as debug_popup, ui.card():
                ui.button("Close", on_click=debug_popup.close)
                with ui.card().tight().classes("bg-gray-50"):
                    ui.markdown(
                        "```\n"
                        + json.dumps(get_ui_tree(self.state), indent=2)
                        + "\n```"
                    ).classes("text-xs")
            with ui.row():
                ui.markdown(self.label).classes("text-lg")
                ui.button("debug", on_click=lambda: debug_popup.open())
                if self.game_state:
                    ui.button(
                        f"ops:{len(self.game_state.operation_queue.queue)}"
                    ).on_click(self.show_operations)
            with ui.scroll_area().classes(
                f"w-{self.width} h-{self.height} border"
            ) as scroll_area:
                self.treeElement: Tree = ui.tree(
                    [get_ui_tree(self.state)],
                    label_key="name",
                    node_key="uid",
                    children_key="children",
                    tick_strategy="strict",
                    on_select=self.select_node_callback,
                    on_tick=self.tick_node_callback,
                )
                self.treeElement.add_slot(
                    "default-header",
                    """
                    <q-tooltip :props="props">
                        Fullname: {{ props.node.fullname }} <br>
                        ID:{{ props.node.uid }}
                    </q-tooltip>
                    <span :props="props">
                    {{ props.node.name }} 
                    </span>""",
                )
                for n in self.treeElement.nodes():
                    keys = []
                    if not n["compress"]:
                        keys.append(n["uid"])
                    self.treeElement.expand(keys)
            if self.node_selected:
                self.treeElement.select(self.node_selected.uid)
                await self.select_node(self.node_selected)
            if self.nodes_ticked:
                self.treeElement.untick(None)
                self.treeElement.tick([n.uid for n in self.nodes_ticked])
                self.tick_node(self.nodes_ticked)

            def remember_scroll(e):
                self.scroll_position = [e.horizontal_position, e.vertical_position]

            scroll_area.on_scroll(remember_scroll)
            if getattr(self, "scroll_position", None):
                scroll_area.scroll_to(pixels=self.scroll_position[0], axis="horizontal")
                scroll_area.scroll_to(pixels=self.scroll_position[1], axis="vertical")

            self.node_operations_view: NodeOperationsView = NodeOperationsView(
                self.nodes_ticked, self.state, self.allowed_operations, self
            )
            await self.node_operations_view.build()

        self.single_node_arguments_view = SingleNodeAttributesView(None, self)
        await self.single_node_arguments_view.build()


class StateTreeView(StateTreeViewBase):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def tick_node(self, nodes: list[tree_node.Node]) -> None:
        self.node_operations_view.ticked_nodes = nodes
        self.node_operations_view.state = self.state
        self.node_operations_view.refresh()

    async def after_operation(self, select_hint: selection_hint.SelectionHint):
        if select_hint:
            if select_hint.erase_ticked:
                self.nodes_ticked = []
            if select_hint.new_node_selected:
                self.node_selected = select_hint.new_node_selected
            if select_hint.new_nodes_ticked:
                self.nodes_ticked[:] = select_hint.new_nodes_ticked
        self.refresh(False)


class AllStatesTree(StateTreeView):
    width = "64"
    height = "48"
    allowed_operations = [
        operations.OperationAddNextGameState,
        operations.OperationAddBranchingGameState,
        operations.OperationDeleteNode,
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class SingleStateTree(StateTreeView):
    width = "94"
    height = "128"
    allowed_operations = [
        operations.OperationAddNode,
        operations.OperationDeleteNode,
    ]

    @property
    def state(self):
        return self.game_state.current_state if self.game_state else None

    @state.setter
    def state(self, v):
        pass

    async def apply_operation(self, operation):
        print(
            f"APPLYING OPERATION TO GAMESTATE: {self.game_state.name}, {self.game_state.uid}"
        )
        operation_result = self.game_state.apply_gamestate_operation(operation)
        print("RESULT IN SingleStateTree", operation_result)
        return await self.after_operation(operation_result)

    async def show_operations(self):
        with ui.dialog() as self.operation_queue_dialog, ui.card():
            self.operation_queue_view = OperationQueueView(self, self.game_state)
            await self.operation_queue_view.build()
        self.operation_queue_dialog.open()

    async def select_node(self, node):
        self.single_node_arguments_view.node_selected = node
        self.single_node_arguments_view.refresh()

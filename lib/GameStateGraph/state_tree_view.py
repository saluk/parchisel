from __future__ import annotations

from nicegui.elements.tree import Tree
from nicegui.elements.button import Button
from . import gamestategraph
from .node_operations_view import NodeOperationsView
from . import operations
from nicegui import ui, html
from nicegui.events import KeyboardKey

class SelectRangeButton:
    def __init__(self):
        self.active = False
        self.node_start:gamestategraph.Node = None
        self.node_end:gamestategraph.Node = None
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
        while start_i<=end_i:
            found.append(self.node_start.parent.children[start_i])
            start_i += 1
        if not self.untick:
            [tree_view.nodes_ticked.insert(-1, node) for node in found if node not in tree_view.nodes_ticked]
            tree_view.treeElement.tick([node.uid for node in found])
        else:
            [tree_view.nodes_ticked.remove(node) for node in found if node in tree_view.nodes_ticked]
            tree_view.treeElement.untick([node.uid for node in found])
        return True

class StateTreeViewBase:
    width = "64"
    height = "48"
    allowed_operations: list[operations.OperationBase] = []
    def __init__(self, view, state, label="") -> None:
        self.view = view
        self.label = label
        self.state:gamestategraph.Node = state

        self.treeElement = None
        self.nodes_ticked:list[gamestategraph.Node] = []
        self.node_selected:gamestategraph.Node = None

        self.select_range_button = SelectRangeButton()

        # A view of a selected node (or set of nodes) and their properties
        self.node_properties_view = None

        # A view of operations to apply to the selected nodes
        self.node_operations_view = None

        self.nodes_ticked = []
    def refresh(self) -> None:
        print("refresh stateTreeViewBase:", self.state.name)
        # If some nodes were deleted, we might need to update our selection
        if self.node_selected and not self.node_selected.parent:
            self.node_selected = None
        self.nodes_ticked[:] = [node for node in self.nodes_ticked if node and (node.parent or node.is_root)]
        self.build.refresh()
    async def select_none(self) -> None:
        self.treeElement.untick(None)
        self.treeElement.deselect()
        self.nodes_ticked = []
        self.tick_node([])
    def select_node_callback(self, e) -> None:
        print(e)
        if e.value != None:
            node: gamestategraph.Node | None = self.state.find_node(e.value)
            self.node_selected = node
        if self.node_selected:
            self.select_node(self.node_selected)
    def select_node(self, node:gamestategraph.Node) -> None:
        pass
    async def tick_node_callback(self, e) -> None:
        print(e)
        unticked = None
        for node in self.nodes_ticked:
            if node.uid not in e.value:
                unticked = node
                self.nodes_ticked.remove(node)
                if self.select_range_button.active:
                    await self.select_range_button.clicked_node(unticked, self, untick=True)
                    self.tick_node(self.nodes_ticked)
                    return
        self.nodes_ticked = []
        for uid in e.value:
            self.nodes_ticked.append(self.state.find_node(uid))
        if self.nodes_ticked and await self.select_range_button.clicked_node(self.nodes_ticked[-1], self):
            self.tick_node(self.nodes_ticked)
            return
        self.tick_node(self.nodes_ticked)
    def tick_node(self, nodes:list[gamestategraph.Node]) -> None:
        pass
    @ui.refreshable
    async def build(self) -> None:
        print("Building statetreeview")
        ui.label(self.label)
        with ui.card():
            with ui.card():
                with ui.row():
                    ui.button("Select None", on_click=self.select_none)
                    await self.select_range_button.build()
            with ui.row():
                with ui.card() as treeCard:
                    with ui.scroll_area().classes(f'w-{self.width} h-{self.height} border'):
                        self.treeElement: Tree = ui.tree(
                            [gamestategraph.get_ui_tree(self.state)], 
                            label_key='name',
                            node_key='uid',
                            children_key='children',
                            tick_strategy='strict',
                            on_select=self.select_node_callback,
                            on_tick=self.tick_node_callback,
                        )
                        self.treeElement.add_slot('default-header', 
                            '''
                            <q-tooltip :props="props">
                                Fullname: {{ props.node.fullname }} <br>
                                ID:{{ props.node.uid }}
                            </q-tooltip>
                            <span :props="props">
                            {{ props.node.name }} 
                            </span>'''
                        )
                        for n in self.treeElement.nodes():
                            keys = []
                            if not n["compress"]:
                                keys.append(n["uid"])
                            self.treeElement.expand(keys)
                        self.treeElement.on('click', lambda e:print(e))
                if self.node_selected:
                    self.treeElement.select(self.node_selected.uid)
                if self.nodes_ticked:
                    self.treeElement.tick([n.uid for n in self.nodes_ticked])
                self.node_operations_view: NodeOperationsView = NodeOperationsView(self.nodes_ticked, self.state, self.allowed_operations, self)
                await self.node_operations_view.build()

class StateTreeView(StateTreeViewBase):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
    def tick_node(self, nodes:list[gamestategraph.Node]) -> None:
        self.node_operations_view.ticked_nodes = nodes
        self.node_operations_view.refresh()

class AllStatesTree(StateTreeView):
    width = "64"
    height = "48"
    allowed_operations = [operations.OperationAddNextGameState(), operations.OperationAddBranchingGameState(), operations.OperationDeleteNode()]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class SingleStateTree(StateTreeView):
    width = "94"
    height = "128"
    allowed_operations = [operations.OperationAddNode(),operations.OperationDeleteNode()]
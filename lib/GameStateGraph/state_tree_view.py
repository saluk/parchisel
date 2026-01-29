from __future__ import annotations

from nicegui.elements.tree import Tree
from . import gamestategraph
from .node_operations_view import NodeOperationsView
from . import operations
from nicegui import ui, html

class StateTreeViewBase:
    allowed_operations: list[operations.OperationBase] = []
    def __init__(self, state) -> None:
        self.state:gamestategraph.Node = state

        self.treeElement = None
        self.nodes_ticked:list[gamestategraph.Node] = []
        self.node_selected:gamestategraph.Node = None

        # A view of a selected node (or set of nodes) and their properties
        self.node_properties_view = None

        # A view of operations to apply to the selected nodes
        self.node_operations_view = None
    def refresh(self) -> None:
        print("refresh stateTreeViewBase:", self.state.name)
        self.build.refresh()
    def select_node_callback(self, e) -> None:
        if e.value != None:
            node: gamestategraph.Node | None = self.state.find_node(e.value)
            if isinstance(node, gamestategraph.GameStateTree):
                if self.node_selected:
                    self.treeElement.select(self.node_selected.uid)
                return
            self.node_selected = node
        if self.node_selected:
            self.select_node(self.node_selected)
    def select_node(self, node:gamestategraph.Node) -> None:
        pass
    async def select_none(self) -> None:
        self.treeElement.untick(None)
        self.treeElement.deselect()
        self.nodes_ticked = []
        self.tick_node([])
    async def tick_node_callback(self, e) -> None:
        print(e)
        self.nodes_ticked = []
        for uid in e.value:
            self.nodes_ticked.append(self.state.find_node(uid))
        self.tick_node(self.nodes_ticked)
    def tick_node(self, nodes:list[gamestategraph.Node]) -> None:
        pass
    @ui.refreshable
    async def build(self) -> None:
        print("Building statetreeview")
        with ui.card():
            ui.button("Select None", on_click=self.select_none)
            self.treeElement: Tree = ui.tree(
                [gamestategraph.get_ui_tree(self.state)], 
                label_key='name',
                node_key='uid',
                children_key='children',
                tick_strategy='strict',
                on_select=self.select_node_callback,
                on_tick=self.tick_node_callback
            )
            self.treeElement.add_slot('default-body', '''
    <span :props="props">ID: "{{ props.node.uid }}"</span>
''')
            for n in self.treeElement.nodes():
                keys = []
                if not n["compress"]:
                    keys.append(n["uid"])
                self.treeElement.expand(keys)
        if self.node_selected:
            self.treeElement.select(self.node_selected.uid)
        if self.nodes_ticked:
            self.treeElement.tick([n.uid for n in self.nodes_ticked])
        self.node_operations_view: NodeOperationsView = NodeOperationsView(self.nodes_ticked, self.state, self.allowed_operations, self)
        with ui.card():
            await self.node_operations_view.build()

class StateTreeView(StateTreeViewBase):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.dont_tick = False
        self.dont_select = False
    def select_node(self, node:gamestategraph.Node) -> None:
        if not self.dont_tick:
            self.dont_select = True
            if node in self.nodes_ticked:
                self.nodes_ticked.remove(node)
            self.nodes_ticked.append(node)
            self.treeElement.tick([tick_node.uid for tick_node in self.nodes_ticked])
            self.tick_node(self.nodes_ticked)
            self.dont_select = False
    def tick_node(self, nodes:list[gamestategraph.Node]) -> None:
        if nodes and not self.dont_select:
            self.dont_tick = True
            self.treeElement.select(nodes[-1].uid)
            self.node_selected = nodes[-1]
            self.select_node(nodes[-1])
            self.dont_tick = False
        self.node_operations_view.ticked_nodes = nodes
        self.node_operations_view.refresh()

class AllStatesTree(StateTreeView):
    allowed_operations = [operations.OperationAddNextGameState(), operations.OperationAddBranchingGameState()]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.on_select_target = None
    def select_node(self, node:gamestategraph.Node) -> None:
        super().select_node(node)
        if self.on_select_target:
            self.on_select_target.on_all_states_select(node)

class SingleStateTree(StateTreeView):
    allowed_operations = [operations.OperationAddNode()]
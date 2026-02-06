from nicegui import ui, html


from . import gamestategraph
from .state_tree_view import AllStatesTree, SingleStateTree

class GameStateGraphUI:
    def __init__(self, ov):
        self.view = ov
        self.game_states = gamestategraph.GameStateTree()
        self.game_states.add_children([gamestategraph.GameState([], gamestategraph.Node("something",[gamestategraph.Node("something_child")],is_root=True))])
        self.game_states.children[0].add_next()
        self.game_states.children[0].children[0].current_state.name = "something2"
        self.game_states.update_tree()
        print("PRINTING STATE")
        gamestategraph.print_state(self.game_states)
        gamestategraph.print_state(self.game_states.children[0].children[0].current_state)

        # interfaces
        self.all_states_tree = AllStatesTree(self.view, self.game_states, "Decision Tree")
        self.all_states_tree.select_node = lambda node: self.on_all_states_select(node)
        self.single_state_tree = None
        self.selected_node_inspector = None

    def new_graph(self):
        self.game_states.delete_children()
        self.game_states.add_children([gamestategraph.GameState([], gamestategraph.Node("root",is_root=True))])
        self.refresh()
    def refresh(self):
        self.build.refresh()
    def on_all_states_select(self, node:gamestategraph.Node):
        self.single_state_tree = SingleStateTree(self.view, node.current_state, f"Decision Node: **{node.name}**")
        print("refresh after clicking to select a gamestate node")
        self.refresh()
    @ui.refreshable
    async def build(self):
        print("building gamestategraph")
        ov = self.view
        project = ov.project
        ui.label("Game State Graph")
        ui.button("New Graph", on_click=self.new_graph)
        with ui.row():
            await self.all_states_tree.build()
            if(self.single_state_tree):
                await self.single_state_tree.build()
            else:
                ui.label('no state selected')
        return
from nicegui import ui, html


from .model import game_state, tree_node
from .model.game_state import GameState
from .state_tree_view import AllStatesTree, SingleStateTree


class GameStateGraphUI:
    def __init__(self, ov):
        self.view = ov
        self.game_states = game_state.GameStateTree()
        self.game_states.add_children(
            [
                GameState(
                    tree_node.Node(
                        "something",
                        [tree_node.Node("something_child")],
                        is_root=True,
                    )
                )
            ]
        )
        self.game_states.children[0].add_next()
        self.game_states.children[0].children[
            0
        ].current_state.name = "something2"  # Shouldn't be setting the state directly, but this is just for debug
        self.game_states.update_tree()
        print("PRINTING STATE")
        game_state.print_state(self.game_states)
        game_state.print_state(self.game_states.children[0].children[0].current_state)

        # interfaces
        self.all_states_tree = AllStatesTree(
            self.view, self.game_states, "Decision Tree"
        )
        self.all_states_tree.select_node = self.on_all_states_select
        self.single_state_tree = SingleStateTree(self.view)
        self.selected_node_inspector = None

    def new_graph(self):
        self.game_states.delete_children()
        self.game_states.add_children(
            [game_state.GameState(tree_node.Node("root", is_root=True))]
        )
        self.refresh()

    def refresh(self):
        self.build.refresh()

    async def on_all_states_select(self, node: tree_node.Node):
        self.single_state_tree.state = node.current_state
        self.single_state_tree.game_state = node
        self.single_state_tree.label = f"Decision Node: **{node.name}**"
        self.single_state_tree.refresh()

    @ui.refreshable
    async def build(self):
        print("building gamestategraph")
        ov = self.view
        project = ov.project
        ui.label("Game State Graph")
        ui.button("New Graph", on_click=self.new_graph)
        with ui.row():
            await self.all_states_tree.build()
            await self.single_state_tree.build()
        return

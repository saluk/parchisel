from nicegui import ui, html, app


from .model import game_state, tree_node
from .model.game_state import GameState
from .state_tree_view import AllStatesTree, SingleStateTree
from . import save_load_view


class GameStateGraphUI:
    def __init__(self, ov):
        self.view = ov
        self.file_menu = save_load_view.SaveLoadView(self)

        self.game_states = game_state.GameStateTree("Tree", is_root=True)
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

        self.regen_views()

    def new_graph(self):
        self.game_states.delete_children()
        self.game_states.add_children(
            [game_state.GameState(tree_node.Node("root", is_root=True))]
        )
        self.regen_views()
        self.refresh()

    def replace_graph(self, game_states):
        self.game_states = game_states
        self.game_states.update_tree()
        self.regen_views()
        self.refresh()

    def regen_views(self):
        self.all_states_tree = AllStatesTree(
            self.view, self.game_states, "Decision Tree"
        )
        self.single_state_tree = SingleStateTree(self.view)
        self.all_states_tree.single_state_tree = self.single_state_tree
        self.selected_node_inspector = None

    def refresh(self):
        self.build.refresh()

    @ui.refreshable
    async def build(self):
        print("building gamestategraph")
        ov = self.view
        project = ov.project
        ui.markdown(
            "##### Game State Graph"
            + (f": **{self.file_menu.filename}**" if self.file_menu.filename else "")
        )
        await self.file_menu.build()
        with ui.row():
            await self.all_states_tree.build()
            await self.single_state_tree.build()
        return
